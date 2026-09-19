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
import json, re, time, unicodedata
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


def _formes(m: str, pas: int = 2) -> set[str]:
    """Formes fléchies (pluriel, féminin) d'un mot : le validateur juge les mots, pas leur accord.
    Aucun mot n'est ajouté au vocabulaire : seule la forme fléchie d'un mot présent au profil est reconnue.
    La casse et les accents sont déjà écartés par mots()."""
    f = set()
    if len(m) > 4 and m[-1] in "sx":
        f.add(m[:-1])                                  # environnements -> environnement
    if len(m) > 3:
        f.update((m + "s", m + "x"))                   # cible -> cibles
    if m.endswith("elle"):
        f.add(m[:-2])                                  # operationnelle -> operationnel
    elif m.endswith("el"):
        f.add(m + "le")
    if m.endswith("ee"):
        f.add(m[:-1])                                  # securisee -> securise (sécurisée -> sécurisé)
    elif m.endswith("e") and len(m) > 4:
        f.add(m + "e")
    if pas > 1:
        for x in list(f):
            f |= _formes(x, pas - 1)                   # operationnelles -> operationnelle -> operationnel
    f.discard(m)
    return f


def _localiser(av: str, zone_cv: list[str]) -> str | None:
    """Extrait du CV qui correspond à `av` à la casse, aux espaces et à l'apostrophe près, sinon None."""
    lettre = lambda c: "['’]" if c in "'’" else re.escape(c)
    motif = r"\s+".join("".join(lettre(c) for c in w) for w in av.split())
    for p in zone_cv:
        m = re.search(motif, p, flags=re.IGNORECASE)
        if m:
            return m.group(0)
    return None


def valider(propositions: dict, zone_cv: list[str], vocab: set[str]) -> tuple[list[dict], list[dict]]:
    """Sépare les substitutions acceptées des refusées, avec leur motif."""
    ok, refus = [], []
    subs = propositions.get("substitutions") if isinstance(propositions, dict) else None
    for s in (subs if isinstance(subs, list) else [])[:4]:
        if not isinstance(s, dict):
            refus.append({"avant": "", "apres": str(s)[:200], "motif": "forme inattendue"}); continue
        av, ap = str(s.get("avant") or "").strip(), str(s.get("apres") or "").strip()
        if not av or not ap or av == ap:
            refus.append({**s, "motif": "vide ou identique"}); continue
        if not any(av in p for p in zone_cv):
            av = _localiser(av, zone_cv)              # le modèle change la casse ou l'apostrophe en recopiant
            if not av:
                refus.append({**s, "motif": "texte d'origine absent de la zone modifiable"}); continue
            if av == ap:
                refus.append({**s, "motif": "vide ou identique"}); continue
        if re.search(r"[*_#`]|\*\*", ap):
            refus.append({**s, "motif": "mise en forme interdite"}); continue
        nouveaux = sorted(m for m in {m.strip(".-") for m in mots(ap)} - vocab - MOTS_OUTILS
                          if not _formes(m) & vocab)
        if nouveaux:
            refus.append({**s, "motif": "termes absents du profil maître : " + ", ".join(nouveaux)}); continue
        if any("’" in p for p in zone_cv):
            ap = ap.replace("'", "’")               # typographie du CV : le modèle écrit l'apostrophe droite
        ok.append({"avant": av, "apres": ap})
    return ok, refus


def profil_pour_modele(profil: dict) -> str:
    """Profil complet et compact, sans coordonnées ni préférences : rien d'utile n'est tronqué."""
    utile = {k: v for k, v in profil.items() if k not in ("identity", "preferences")}
    return json.dumps(utile, ensure_ascii=False, separators=(",", ":"))


def proposer(llm, chemin_docx: str, annonce: str, profil: dict, max_annonce: int = 6000) -> dict:
    """Interroge le modèle local. Renvoie substitutions validées, refus, écarts, durée."""
    z = zone(chemin_docx)
    message = ("ZONE (paragraphes modifiables) :\n" + "\n".join(f"- {p}" for p in z) +
               "\n\nPROFIL MAÎTRE (JSON) :\n" + profil_pour_modele(profil) +
               "\n\nANNONCE :\n" + annonce[:max_annonce])
    t0 = time.time()
    brut = llm.json(SYSTEME, message, SCHEMA)
    duree = round(time.time() - t0, 1)
    if not isinstance(brut, dict):
        raise ValueError(f"réponse de forme inattendue : {type(brut).__name__}")
    vocab = vocabulaire(profil, *z)
    ok, refus = valider(brut, z, vocab)
    ecarts = [e for e in (brut.get("ecarts") or []) if isinstance(e, str)][:10]
    # Un « écart » dont tous les mots sont au profil est une erreur du modèle : on le met de côté.
    a_tort = [e for e in ecarts if mots(e) and all(m.strip(".-") in vocab for m in mots(e))]
    proposees = brut.get("substitutions") if isinstance(brut.get("substitutions"), list) else []
    return {"substitutions": ok, "refus": refus, "duree_modele_s": duree, "nb_propositions": len(proposees),
            "mesure_modele": dict(getattr(llm, "mesure", {}) or {}),
            "ecarts": [e for e in ecarts if e not in a_tort], "ecarts_a_tort": a_tort}


def _cv_d_axe(cv_axe: str, sortie_docx: str, motif: str, **plus) -> dict:
    from .docx_mcp import appliquer
    appliquer(cv_axe, sortie_docx, [])
    return {"docx": sortie_docx, "mode": "axe", "motif": motif, "appliquees": [], "refus": [],
            "ecarts": [], "ecarts_a_tort": [], "duree_modele_s": None, "nb_propositions": 0, **plus}


def personnaliser(llm, cv_axe: str, sortie_docx: str, annonce: str, profil: dict) -> dict:
    """CV d'axe -> CV adapté. Toute défaillance du modèle ou du serveur MCP : CV d'axe inchangé, motif consigné."""
    from .docx_mcp import appliquer, EchecEdition
    from ..llm.local import LLMIndisponible
    try:
        prop = proposer(llm, cv_axe, annonce, profil)
    except (LLMIndisponible, ValueError, KeyError, TypeError, AttributeError) as e:
        return _cv_d_axe(cv_axe, sortie_docx, f"modèle indisponible : {e}")
    try:
        bilan = appliquer(cv_axe, sortie_docx, prop["substitutions"])
    except (EchecEdition, OSError, ExceptionGroup, RuntimeError) as e:
        return _cv_d_axe(cv_axe, sortie_docx, f"édition MCP en échec : {e}", ecarts=prop["ecarts"],
                         ecarts_a_tort=prop["ecarts_a_tort"], duree_modele_s=prop["duree_modele_s"],
                         nb_propositions=prop["nb_propositions"], refus=prop["refus"])
    return {"docx": sortie_docx, "mode": "adapte" if any(b["applique"] for b in bilan) else "axe",
            "appliquees": [b for b in bilan if b["applique"]],
            "refus": prop["refus"] + [b for b in bilan if not b["applique"]],
            "ecarts": prop["ecarts"], "ecarts_a_tort": prop["ecarts_a_tort"],
            "duree_modele_s": prop["duree_modele_s"], "nb_propositions": prop["nb_propositions"],
            "mesure_modele": prop["mesure_modele"]}
