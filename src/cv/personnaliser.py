"""
Personnalisation du CV par le modèle local (EPIC-5, EPIC-14).

Le modèle propose des substitutions ; tout le reste est déterministe :
- il ne voit que la zone modifiable du CV (titre et accroche) ;
- chaque substitution est vérifiée : texte d'origine présent tel quel dans la
  zone, et aucun mot nouveau absent du profil maître ;
- l'édition du fichier passe par le serveur MCP docx, jamais par le modèle ;
- toute défaillance du modèle renvoie le CV d'axe inchangé.
"""
from __future__ import annotations
import json, re, unicodedata
from docx import Document

SYSTEME = """Tu adaptes un CV existant à une annonce. Tu ne rédiges pas un CV : tu proposes des substitutions de texte dans un CV déjà validé.

Source de vérité : le profil maître du candidat. Rien d'autre.

1. N'ajoute aucune compétence, technologie, employeur, certification, chiffre ou date absent du profil maître.
2. Reformule, réordonne, mets en avant. N'invente jamais.
3. Ne touche qu'aux paragraphes fournis dans ZONE (titre et accroche).
4. "avant" est un extrait copié mot pour mot d'un paragraphe de ZONE.
5. Aucune mise en forme : pas de gras, pas de symbole, pas de markdown.
6. Si l'annonce exige une compétence absente du profil maître, liste-la dans ecarts. Ne la comble pas.
7. Au plus 4 substitutions. Aucune si le CV convient déjà.

Réponds uniquement en JSON."""

SCHEMA = {
    "type": "object",
    "properties": {
        "substitutions": {"type": "array", "maxItems": 4, "items": {
            "type": "object", "properties": {"avant": {"type": "string"}, "apres": {"type": "string"}},
            "required": ["avant", "apres"]}},
        "ecarts": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["substitutions", "ecarts"],
}

MOTS_OUTILS = set("""a à au aux avec d de des du en et l la le les leur leurs mise ou par pour sur un une
dans chez vers sous sans entre ses son sa ce ces cette qui que dont
and the of for with to in on at by from an as or""".split())


def _norm(m: str) -> str:
    m = unicodedata.normalize("NFKD", m.lower())
    return "".join(c for c in m if not unicodedata.combining(c))


def mots(texte: str) -> list[str]:
    return [_norm(m) for m in re.findall(r"[\w+#.-]+", texte, flags=re.UNICODE)
            if len(m.strip(".-")) > 1]


def vocabulaire(profil: dict, *textes: str) -> set[str]:
    v = set()
    def parcourir(x):
        if isinstance(x, dict):
            for k, y in x.items():
                parcourir(y)
        elif isinstance(x, list):
            for y in x:
                parcourir(y)
        elif isinstance(x, str):
            v.update(m.strip(".-") for m in mots(x))
    parcourir(profil)
    for t in textes:
        v.update(m.strip(".-") for m in mots(t))
    return v


def zone(chemin_docx: str) -> list[str]:
    """Titre et accroche : paragraphes avant le premier titre de section, sans coordonnées."""
    z = []
    for i, p in enumerate(Document(chemin_docx).paragraphs):
        if i == 0:
            continue                               # nom du candidat
        if p.style.name.lower().startswith(("heading", "titre")):
            break
        t = p.text.strip()
        if not t or "@" in t or re.search(r"\d\d[ .]?\d\d[ .]?\d\d[ .]?\d\d", t):
            continue                               # coordonnées
        z.append(t)
    return z


def valider(propositions: dict, zone_cv: list[str], vocab: set[str]) -> tuple[list[dict], list[dict]]:
    """Sépare les substitutions acceptées des refusées, avec leur motif."""
    ok, refus = [], []
    for s in (propositions or {}).get("substitutions", [])[:4]:
        av, ap = (s.get("avant") or "").strip(), (s.get("apres") or "").strip()
        if not av or not ap or av == ap:
            refus.append({**s, "motif": "vide ou identique"}); continue
        if not any(av in p for p in zone_cv):
            refus.append({**s, "motif": "texte d'origine absent de la zone modifiable"}); continue
        if re.search(r"[*_#`]|\*\*", ap):
            refus.append({**s, "motif": "mise en forme interdite"}); continue
        nouveaux = sorted({m.strip(".-") for m in mots(ap)} - vocab - MOTS_OUTILS)
        if nouveaux:
            refus.append({**s, "motif": "termes absents du profil maître : " + ", ".join(nouveaux)}); continue
        ok.append({"avant": av, "apres": ap})
    return ok, refus


def proposer(llm, chemin_docx: str, annonce: str, profil: dict, max_annonce: int = 6000) -> dict:
    """Interroge le modèle local. Renvoie substitutions validées, refus et écarts."""
    z = zone(chemin_docx)
    message = ("ZONE (paragraphes modifiables) :\n" + "\n".join(f"- {p}" for p in z) +
               "\n\nPROFIL MAÎTRE (JSON) :\n" + json.dumps(profil, ensure_ascii=False)[:9000] +
               "\n\nANNONCE :\n" + annonce[:max_annonce])
    brut = llm.json(SYSTEME, message, SCHEMA)
    ok, refus = valider(brut, z, vocabulaire(profil, *z))
    return {"substitutions": ok, "refus": refus, "ecarts": list(brut.get("ecarts", []))[:10]}


def personnaliser(llm, cv_axe: str, sortie_docx: str, annonce: str, profil: dict) -> dict:
    """CV d'axe -> CV adapté. Toute défaillance du modèle : CV d'axe inchangé, motif consigné."""
    from .docx_mcp import appliquer
    from ..llm.local import LLMIndisponible
    try:
        prop = proposer(llm, cv_axe, annonce, profil)
    except (LLMIndisponible, ValueError, KeyError, TypeError) as e:
        appliquer(cv_axe, sortie_docx, [])
        return {"docx": sortie_docx, "mode": "axe", "motif": f"modèle indisponible : {e}",
                "appliquees": [], "refus": [], "ecarts": []}
    bilan = appliquer(cv_axe, sortie_docx, prop["substitutions"])
    return {"docx": sortie_docx, "mode": "adapte" if any(b["applique"] for b in bilan) else "axe",
            "appliquees": [b for b in bilan if b["applique"]],
            "refus": prop["refus"] + [b for b in bilan if not b["applique"]],
            "ecarts": prop["ecarts"]}
