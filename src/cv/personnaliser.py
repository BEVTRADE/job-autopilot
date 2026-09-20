"""
Personnalisation d'un CV d'axe par SÉLECTION (EPIC-14, ADR-011, décision du 20/09/2026).

Le modèle local n'écrit aucun texte. Pour une annonce, il choisit :
- le titre du CV, dans la liste autorisée de l'axe et de la langue du CV
  (profile/titres_autorises.json), ou « inchangé » ;
- l'ordre des paragraphes d'accroche, SAUF le premier (le résumé), qui reste en tête ;
et signale les « écarts » : exigences de l'annonce absentes du profil maître.

Tout le reste est déterministe :
- la liste des titres est fixée par le candidat, jamais par le modèle ;
- la réponse est validée (titre dans la liste, permutation valide), sinon CV d'axe inchangé ;
- garde de rôle : si le titre de l'annonce contient « architecte » ou « architect », le titre choisi
  doit le contenir aussi, sinon le titre actuel est gardé ;
- le code applique le titre et déplace le texte des paragraphes existants par le serveur
  MCP docx-mcp-server, tout ou rien, puis relit le fichier produit ;
- toute défaillance du modèle ou du serveur rend le CV d'axe inchangé, motif consigné.

La rédaction libre (substitutions de texte contrôlées mot à mot) est retirée : sur 20 annonces,
91 % des propositions de Qwen 14B étaient refusées à raison (docs/revues/epic14-evaluation.md ;
dernier état du code : commit ad3bdf6). La référence TF-IDF (choix sans modèle) est abandonnée pour
cet étage : notée 17/40 contre 27/40 pour Qwen, dont 7 choix nuisibles contre 3 (dernier état : commit 7700467).
"""
from __future__ import annotations
import json, os, random, re, time, unicodedata
from docx import Document

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TITRES = os.path.join(RACINE, "profile", "titres_autorises.json")
INCHANGE = "inchangé"

SYSTEME = """Tu aides à choisir, pour une annonce, le titre et l'ordre de l'accroche d'un CV déjà validé. Tu n'écris aucun texte.

1. "titre" : recopie exactement UNE option de la liste OPTIONS DE TITRE, celle qui correspond le mieux au poste de l'annonce. Réponds "inchangé" si le titre actuel convient déjà. Ces titres sont les seuls que le CV atteste : n'en invente pas.
2. "ordre_accroche" : les paragraphes d'accroche sont numérotés à partir de 0. Le paragraphe 0 est le résumé : il reste toujours en premier et ne figure PAS dans ta réponse. Donne les indices de tous les autres paragraphes, une seule fois chacun, dans l'ordre où ils doivent apparaître. Mets en premier ceux qui servent le plus cette annonce. Si l'ordre actuel convient, garde-le.
3. "ecarts" : exigences ou compétences de l'annonce absentes du PROFIL MAÎTRE. Ce qui figure au profil n'est pas un écart. Liste vide s'il n'y en a pas.

Réponds uniquement en JSON."""


# --- vocabulaire du profil : ne sert plus qu'à écarter les « écarts » que le profil couvre déjà ---

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
            for y in x.values():
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


def profil_pour_modele(profil: dict) -> str:
    """Profil complet et compact, sans coordonnées ni préférences : rien d'utile n'est tronqué."""
    utile = {k: v for k, v in profil.items() if k not in ("identity", "preferences")}
    return json.dumps(utile, ensure_ascii=False, separators=(",", ":"))


# --- CV d'axe : titre, accroche, liste de titres autorisés ---

def zone(chemin_docx: str) -> list[tuple[int, str]]:
    """(indice, texte) du titre puis des paragraphes d'accroche : avant le premier titre de section,
    sans le nom ni les coordonnées. Le premier élément est le titre, les suivants l'accroche."""
    z = []
    for i, p in enumerate(Document(chemin_docx).paragraphs):
        if i == 0:
            continue                               # nom du candidat
        if p.style.name.lower().startswith(("heading", "titre")):
            break
        t = p.text.strip()
        if not t or "@" in t or re.search(r"\d\d[ .]?\d\d[ .]?\d\d[ .]?\d\d", t):
            continue                               # coordonnées
        z.append((i, p.text))
    return z


def charger_titres(chemin: str = TITRES) -> dict:
    return json.load(open(chemin, encoding="utf-8"))["axes"]


def titres_du_cv(chemin_docx: str, table: dict | None = None) -> tuple[str, str, list[str]] | None:
    """(axe, langue, titres autorisés) d'après le nom du fichier CV ; None si ce CV n'a pas de liste."""
    nom = os.path.basename(chemin_docx)
    for axe, d in (table if table is not None else charger_titres()).items():
        for langue, fichier in d["cv"].items():
            if fichier == nom:
                return axe, langue, list(d[langue]["titres"])
    return None


def schema_selection(options: list[str], n_accroche: int) -> dict:
    """Schéma JSON : le décodage contraint le modèle à une option de la liste et à des indices valides.
    Le paragraphe 0 (résumé) n'est pas permutable : `ordre_accroche` ne porte que sur les indices 1 à n-1."""
    n = n_accroche - 1
    return {"type": "object", "properties": {
        "titre": {"type": "string", "enum": list(options)},
        "ordre_accroche": {"type": "array", "minItems": n, "maxItems": n,
                           "items": {"type": "integer", "enum": list(range(1, n_accroche))}},
        "ecarts": {"type": "array", "items": {"type": "string"}}},
        "required": ["titre", "ordre_accroche", "ecarts"]}


def valider_selection(brut, options: list[str], n_accroche: int) -> tuple[str | None, list[int] | None, str | None]:
    """(titre choisi, ordre complet, motif de refus). Titre hors liste ou permutation invalide : refus, CV d'axe
    inchangé. La réponse du modèle est une permutation de 1..n-1 ; l'ordre rendu commence toujours par 0."""
    if not isinstance(brut, dict):
        return None, None, f"réponse de forme inattendue : {type(brut).__name__}"
    titre, ordre = brut.get("titre"), brut.get("ordre_accroche")
    if not isinstance(titre, str) or titre not in options:
        return None, None, f"titre hors de la liste autorisée : {str(titre)[:80]!r}"
    if (not isinstance(ordre, list) or len(ordre) != n_accroche - 1
            or not all(isinstance(i, int) and not isinstance(i, bool) for i in ordre)
            or sorted(ordre) != list(range(1, n_accroche))):
        return None, None, f"ordre d'accroche invalide : {str(ordre)[:80]}"
    return titre, [0] + ordre, None


_ARCHITECTE = re.compile(r"\barchitect(?:e|es|s)?\b")


def contient_architecte(titre: str) -> bool:
    """« architecte », « architect » (et leurs pluriels), sans accent ni casse. « architecture » ne compte pas."""
    return bool(_ARCHITECTE.search(_norm(titre or "")))


def titre_admis_par_la_garde(titre_annonce: str, titre_choisi: str) -> bool:
    """Garde de rôle : une annonce d'architecte n'obtient pas un CV qui n'annonce plus d'architecte."""
    return not contient_architecte(titre_annonce) or contient_architecte(titre_choisi)


# --- appel du modèle ---

def proposer(llm, chemin_docx: str, annonce: str, profil: dict, titres: list[str], max_annonce: int = 6000,
             melange: random.Random | None = None) -> dict:
    """Interroge le modèle local et valide sa réponse. Une réponse invalide ne lève rien : le motif est rendu.
    `melange` (mesure du biais de position) mélange l'ordre des titres alternatifs ; « inchangé » reste en tête."""
    z = zone(chemin_docx)
    titre_actuel, accroche = z[0][1], [t for _, t in z[1:]]
    alternatives = [t for t in titres if t != titre_actuel]
    if melange is not None:
        melange.shuffle(alternatives)
    options = [INCHANGE] + alternatives
    message = (f"TITRE ACTUEL : {titre_actuel}\n\nOPTIONS DE TITRE :\n- {INCHANGE} (garde le titre actuel)\n"
               + "".join(f"- {t}\n" for t in alternatives)
               + "\nACCROCHE (paragraphes numérotés à partir de 0 ; le paragraphe 0 est le résumé et reste en tête) :\n"
               + "".join(f"[{i}] {t}\n" for i, t in enumerate(accroche))
               + "\nPROFIL MAÎTRE (JSON) :\n" + profil_pour_modele(profil)
               + "\n\nANNONCE :\n" + annonce[:max_annonce])
    t0 = time.time()
    brut = llm.json(SYSTEME, message, schema_selection(options, len(accroche)))
    duree = round(time.time() - t0, 1)
    titre, ordre, motif = valider_selection(brut, options, len(accroche))
    ecarts, a_tort = [], []
    if isinstance(brut, dict) and isinstance(brut.get("ecarts"), list):
        vocab = vocabulaire(profil, *(t for _, t in z))
        ecarts = [e for e in brut["ecarts"] if isinstance(e, str)][:10]
        # Un « écart » dont tous les mots sont au profil est une erreur du modèle : on le met de côté.
        a_tort = [e for e in ecarts if mots(e) and all(m.strip(".-") in vocab for m in mots(e))]
        ecarts = [e for e in ecarts if e not in a_tort]
    return {"titre_choisi": titre, "ordre": ordre, "motif": motif, "ecarts": ecarts, "ecarts_a_tort": a_tort,
            "options": options, "duree_modele_s": duree, "mesure_modele": dict(getattr(llm, "mesure", {}) or {})}


def _cv_d_axe(cv_axe: str, sortie_docx: str, motif: str | None, **plus) -> dict:
    from .docx_mcp import appliquer
    appliquer(cv_axe, sortie_docx, [])
    base = {"docx": sortie_docx, "mode": "axe", "ecarts": [], "ecarts_a_tort": [], "duree_modele_s": None,
            "titre_avant": None, "titre_apres": None, "titre_modele": None, "ordre": None, "garde_role": None}
    if motif:
        base["motif"] = motif
    return {**base, **plus}


def personnaliser(llm, cv_axe: str, sortie_docx: str, annonce: str, profil: dict, table_titres: dict | None = None,
                  titre_annonce: str | None = None, melange: random.Random | None = None) -> dict:
    """CV d'axe -> CV adapté (titre et ordre de l'accroche). Toute défaillance : CV d'axe inchangé, motif consigné.

    `titre_annonce` sert à la garde de rôle ; à défaut, la première ligne de `annonce`.
    `titre_modele` est le choix du modèle avant la garde ; `titre_apres` le titre écrit dans le CV."""
    from .docx_mcp import appliquer_remplacements, EchecEdition
    from ..llm.local import LLMIndisponible
    try:
        liste = titres_du_cv(cv_axe, table_titres)
    except (OSError, KeyError, ValueError) as e:
        return _cv_d_axe(cv_axe, sortie_docx, f"liste de titres illisible : {e}")
    if liste is None:
        return _cv_d_axe(cv_axe, sortie_docx, f"aucune liste de titres pour {os.path.basename(cv_axe)}")
    axe, langue, titres = liste
    z = zone(cv_axe)
    if len(z) < 3:
        return _cv_d_axe(cv_axe, sortie_docx, "titre et accroche introuvables dans le CV", axe=axe, langue=langue)
    (i_titre, titre_actuel), accroche = z[0], z[1:]
    try:
        prop = proposer(llm, cv_axe, annonce, profil, titres, melange=melange)
    except (LLMIndisponible, ValueError, KeyError, TypeError, AttributeError) as e:
        return _cv_d_axe(cv_axe, sortie_docx, f"modèle indisponible : {e}", axe=axe, langue=langue)
    commun = {"axe": axe, "langue": langue, "ecarts": prop["ecarts"], "ecarts_a_tort": prop["ecarts_a_tort"],
              "duree_modele_s": prop["duree_modele_s"], "mesure_modele": prop["mesure_modele"], "options": prop["options"]}
    if prop["motif"]:
        return _cv_d_axe(cv_axe, sortie_docx, prop["motif"], **commun)
    modele = titre_actuel if prop["titre_choisi"] in (INCHANGE, titre_actuel) else prop["titre_choisi"]
    ta = titre_annonce if titre_annonce is not None else (annonce.strip().splitlines() or [""])[0]
    titre, refuse = modele, None
    if modele != titre_actuel and not titre_admis_par_la_garde(ta, modele):
        titre, refuse = titre_actuel, modele                # garde de rôle : on garde le titre actuel
    garde = {"declenchee": contient_architecte(ta), "titre_refuse": refuse}
    ordre = prop["ordre"]
    remplacements = []
    if titre != titre_actuel:
        remplacements.append({"indice": i_titre, "avant": titre_actuel, "apres": titre})
    for k, src in enumerate(ordre):                      # la position k reçoit le texte du paragraphe `src`
        if src != k:
            remplacements.append({"indice": z[1 + k][0], "avant": accroche[k][1], "apres": accroche[src][1],
                                  "deplacement": True})
    try:
        appliquer_remplacements(cv_axe, sortie_docx, remplacements)
    except (EchecEdition, OSError, ExceptionGroup, RuntimeError, IndexError) as e:
        return _cv_d_axe(cv_axe, sortie_docx, f"édition MCP en échec : {e}", titre_modele=modele, garde_role=garde, **commun)
    return {"docx": sortie_docx, "mode": "adapte" if remplacements else "axe", "titre_avant": titre_actuel,
            "titre_apres": titre, "titre_modele": modele, "ordre": ordre, "garde_role": garde, **commun}
