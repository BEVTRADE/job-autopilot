"""Modèle local et édition MCP des CV : hors ligne, avec un faux serveur Ollama.

La personnalisation est une SÉLECTION (titre dans une liste, ordre de l'accroche) : le modèle n'écrit aucun texte.
Les tests de la chaîne utilisent une table de titres de test, pas profile/titres_autorises.json.
"""
import json, os, sys, shutil, tempfile, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.llm.local import LLMLocal, LLMIndisponible
from src.cv import personnaliser as P

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CV = os.path.join(RACINE, "cv_prets", "FR_ARCHITECTE_IA_GENAI.docx")
CV_EN = os.path.join(RACINE, "cv_prets", "EN_ENTERPRISE_ARCHITECT.docx")
PROFIL = json.load(open(os.path.join(RACINE, "profile", "master_profile.json"), encoding="utf-8"))
TITRE = "ARCHITECTE IA ET IA GÉNÉRATIVE — LLM, RAG ET AGENTS"
AUTRE = "ARCHITECTE IA — LLM, RAG ET AGENTS"
LEAD = "LEAD TECHNIQUE IA — LLM, RAG ET AGENTS"
TABLE = {"AXE_TEST": {"cv": {"fr": "FR_ARCHITECTE_IA_GENAI.docx", "en": "EN_ENTERPRISE_ARCHITECT.docx"},
                      "fr": {"titres": [TITRE, AUTRE, LEAD]},
                      "en": {"titres": ["ENTERPRISE ARCHITECT — IT URBANISATION, DATA AND AI",
                                        "ENTERPRISE ARCHITECT — IT URBANISATION"]}}}
IDENTITE = [0, 1, 2, 3]


def faux_ollama(reponse: dict | str, modeles=("gpt-oss:20b",)):
    recu = {}
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def _rep(self, obj):
            b = json.dumps(obj).encode(); self.send_response(200)
            self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(b)
        def do_GET(self):
            self._rep({"models": [{"name": m} for m in modeles]})
        def do_POST(self):
            recu.update(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            c = reponse if isinstance(reponse, str) else json.dumps(reponse, ensure_ascii=False)
            self._rep({"message": {"role": "assistant", "content": c}})
    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_port}", recu


def _personnaliser(reponse, cv=CV, annonce="annonce", table=TABLE):
    """Lance personnaliser contre un faux Ollama ; rend (résultat, textes des paragraphes, requête reçue)."""
    from docx import Document
    d = tempfile.mkdtemp()
    srv, url, recu = faux_ollama(reponse)
    try:
        res = P.personnaliser(LLMLocal(url), cv, f"{d}/cv.docx", annonce, PROFIL, table)
        doc = Document(f"{d}/cv.docx")
        return res, [p.text for p in doc.paragraphs], [p.style.name for p in doc.paragraphs], recu
    finally:
        srv.shutdown(); shutil.rmtree(d, ignore_errors=True)


def _textes(cv):
    from docx import Document
    d = Document(cv)
    return [p.text for p in d.paragraphs], [p.style.name for p in d.paragraphs]


# --- client Ollama ---

def test_refuse_une_adresse_non_locale():
    for url in ("https://api.example.com", "http://192.168.1.10:11434"):
        try:
            LLMLocal(url); assert False, url
        except ValueError:
            pass


def test_disponibilite_et_modele_absent():
    srv, url, _ = faux_ollama({}, modeles=("qwen3:8b",))
    try:
        ok, motif = LLMLocal(url, "gpt-oss:20b").disponible()
        assert not ok and "ollama pull gpt-oss:20b" in motif
        assert LLMLocal(url, "qwen3:8b").disponible() == (True, "ok")
    finally:
        srv.shutdown()


def test_serveur_absent_leve_llm_indisponible():
    try:
        LLMLocal("http://127.0.0.1:9", timeout=2).modeles(); assert False
    except LLMIndisponible:
        pass


def test_requete_contrainte_par_schema_et_contexte():
    srv, url, recu = faux_ollama({"titre": "inchangé", "ordre_accroche": IDENTITE, "ecarts": []})
    schema = P.schema_selection([P.INCHANGE, AUTRE], 4)
    try:
        LLMLocal(url, num_ctx=8192).json("sys", "user", schema)
        assert recu["format"] == schema and recu["options"]["num_ctx"] == 8192
        assert recu["options"]["temperature"] == 0 and recu["stream"] is False
    finally:
        srv.shutdown()


# --- CV d'axe, liste de titres, schéma ---

def test_zone_titre_puis_accroche_avec_indices_sans_coordonnees():
    z = P.zone(CV)
    assert z[0] == (1, TITRE)
    assert [i for i, _ in z[1:]] == [3, 4, 5, 6]                 # le paragraphe 2 (coordonnées) est écarté
    assert not any("@" in t for _, t in z)
    assert not any(t.startswith("Réalisations") for _, t in z)


def test_schema_impose_la_liste_et_les_indices():
    s = P.schema_selection([P.INCHANGE, AUTRE, LEAD], 4)
    assert s["properties"]["titre"]["enum"] == [P.INCHANGE, AUTRE, LEAD]
    o = s["properties"]["ordre_accroche"]
    assert o["minItems"] == o["maxItems"] == 4 and o["items"]["enum"] == [0, 1, 2, 3]
    assert "substitutions" not in s["properties"]                # plus aucun texte libre, sauf les écarts


def test_titres_du_cv_par_nom_de_fichier_et_cv_inconnu():
    assert P.titres_du_cv(CV, TABLE) == ("AXE_TEST", "fr", [TITRE, AUTRE, LEAD])
    assert P.titres_du_cv(CV_EN, TABLE)[1] == "en"
    assert P.titres_du_cv(os.path.join(RACINE, "cv_prets", "FR_CONSULTANT_DATA_BI.docx"), TABLE) is None


def test_validation_titre_dans_la_liste_et_permutation_valide():
    opts = [P.INCHANGE, AUTRE, LEAD]
    assert P.valider_selection({"titre": AUTRE, "ordre_accroche": [1, 0, 3, 2]}, opts, 4) == (AUTRE, [1, 0, 3, 2], None)
    assert P.valider_selection({"titre": "inchangé", "ordre_accroche": IDENTITE}, opts, 4)[2] is None
    for brut in ({"titre": "ARCHITECTE IA SENIOR", "ordre_accroche": IDENTITE},          # hors liste
                 {"titre": TITRE, "ordre_accroche": IDENTITE},                            # titre actuel : c'est « inchangé »
                 {"titre": AUTRE, "ordre_accroche": [0, 1, 2]},                            # trop court
                 {"titre": AUTRE, "ordre_accroche": [0, 1, 2, 2]},                         # doublon
                 {"titre": AUTRE, "ordre_accroche": [0, 1, 2, 4]},                         # hors bornes
                 {"titre": AUTRE, "ordre_accroche": [0, 1, 2, True]},                      # booléen
                 {"titre": AUTRE, "ordre_accroche": "0123"}, {"titre": AUTRE}, {"ordre_accroche": IDENTITE},
                 ["une", "liste"], "texte", None):
        t, o, motif = P.valider_selection(brut, opts, 4)
        assert t is None and o is None and motif, brut


def test_reference_sans_modele_deterministe_et_titre_actuel_a_egalite():
    titres = ["ARCHITECTE D’ENTREPRISE — URBANISATION DU SI", "ARCHITECTE DATA ET IA — PLATEFORMES D’ENTREPRISE",
              "CONSULTANT POWER BI — RESTITUTION"]
    assert P.reference_titre("Recherche un architecte data et IA pour des plateformes d'entreprise", titres) == titres[1]
    assert P.reference_titre("Consultant Power BI, restitution et tableaux de bord", titres) == titres[2]
    assert P.reference_titre("Boulanger pâtissier confirmé", titres) == titres[0]      # aucun mot commun : titre actuel
    assert P.reference_titre("Boulanger pâtissier confirmé", titres) == P.reference_titre("Boulanger pâtissier confirmé", titres)


def test_profil_envoye_au_modele_complet_sans_coordonnees():
    s = P.profil_pour_modele(PROFIL)
    assert len(s) > 9000, "le premier jet tronquait à 9000 caractères"
    assert PROFIL["identity"]["email"] not in s and "identity" not in s
    assert json.loads(s)["experiences"] == PROFIL["experiences"]


# --- chaîne complète, serveur MCP réel ---

def test_bout_en_bout_titre_decoupe_en_segments():
    """Le titre compte 19 segments : render.substitute échoue en silence, le serveur MCP réussit."""
    from docx import Document
    from src.cv import render
    d = tempfile.mkdtemp()
    try:
        render.substitute(CV, f"{d}/r.docx", {TITRE: AUTRE})
        assert Document(f"{d}/r.docx").paragraphs[1].text == TITRE      # échec silencieux connu
    finally:
        shutil.rmtree(d, ignore_errors=True)
    avant, styles = _textes(CV)
    res, apres, styles_apres, recu = _personnaliser({"titre": AUTRE, "ordre_accroche": IDENTITE, "ecarts": []})
    assert res["mode"] == "adapte" and res["titre_avant"] == TITRE and res["titre_apres"] == AUTRE
    assert apres[1] == AUTRE and apres[2:] == avant[2:] and apres[0] == avant[0]
    assert styles_apres == styles


def test_ordre_de_l_accroche_deplace_le_texte_des_paragraphes_existants():
    avant, styles = _textes(CV)
    res, apres, styles_apres, _ = _personnaliser({"titre": "inchangé", "ordre_accroche": [1, 0, 3, 2], "ecarts": []})
    assert res["mode"] == "adapte" and res["ordre"] == [1, 0, 3, 2] and res["titre_apres"] == TITRE
    assert apres[3:7] == [avant[4], avant[3], avant[6], avant[5]]       # texte déplacé tel quel
    assert apres[:3] == avant[:3] and apres[7:] == avant[7:] and sorted(apres) == sorted(avant)
    assert styles_apres == styles


def test_rotation_de_l_accroche_et_titre_ensemble_sur_cv_anglais():
    avant, styles = _textes(CV_EN)
    titre_en = TABLE["AXE_TEST"]["en"]["titres"][1]
    res, apres, styles_apres, _ = _personnaliser({"titre": titre_en, "ordre_accroche": [3, 0, 1, 2], "ecarts": []},
                                                 cv=CV_EN)
    assert res["mode"] == "adapte" and res["langue"] == "en" and apres[1] == titre_en
    assert apres[3:7] == [avant[6], avant[3], avant[4], avant[5]] and apres[7:] == avant[7:]
    assert styles_apres == styles


def test_choix_inchange_et_ordre_identique_rend_le_cv_d_axe_sans_motif():
    avant, _ = _textes(CV)
    res, apres, _, _ = _personnaliser({"titre": "inchangé", "ordre_accroche": IDENTITE, "ecarts": ["Slurm"]})
    assert res["mode"] == "axe" and "motif" not in res and apres == avant and res["ecarts"] == ["Slurm"]
    res, apres, _, _ = _personnaliser({"titre": "inchangé", "ordre_accroche": IDENTITE, "ecarts": []})
    assert res["mode"] == "axe" and apres == avant


def test_reponse_invalide_rend_le_cv_d_axe_avec_motif():
    avant, _ = _textes(CV)
    cas = [({"titre": "ARCHITECTE IA SENIOR — LLM", "ordre_accroche": IDENTITE, "ecarts": []}, "hors de la liste"),
           ({"titre": AUTRE, "ordre_accroche": [0, 0, 1, 2], "ecarts": []}, "ordre d'accroche invalide"),
           ({"titre": AUTRE, "ordre_accroche": [0, 1], "ecarts": []}, "ordre d'accroche invalide"),
           ({"titre": TITRE, "ordre_accroche": IDENTITE, "ecarts": []}, "hors de la liste"),
           ('["une", "liste"]', "forme inattendue"), ('{"titre": 3}', "hors de la liste"),
           ("ceci n'est pas du JSON", "non JSON")]
    for rep, motif in cas:
        res, apres, _, _ = _personnaliser(rep)
        assert res["mode"] == "axe" and motif in res["motif"], (rep, res.get("motif"))
        assert apres == avant, rep


def test_cv_sans_liste_de_titres_rend_le_cv_d_axe():
    avant, _ = _textes(CV)
    res, apres, _, recu = _personnaliser({"titre": AUTRE, "ordre_accroche": IDENTITE, "ecarts": []}, table={})
    assert res["mode"] == "axe" and "aucune liste de titres" in res["motif"] and apres == avant
    assert not recu, "le modèle n'est pas interrogé sans liste de titres"


def test_echec_du_serveur_mcp_rend_le_cv_d_axe_sans_fichier_a_moitie_modifie():
    from src.cv import docx_mcp
    avant, _ = _textes(CV)
    vrai = docx_mcp._remplacer
    async def casse(*a, **k):
        raise docx_mcp.EchecEdition("serveur simulé en panne")
    docx_mcp._remplacer = casse
    try:
        res, apres, _, _ = _personnaliser({"titre": AUTRE, "ordre_accroche": [1, 0, 2, 3], "ecarts": []})
    finally:
        docx_mcp._remplacer = vrai
    assert res["mode"] == "axe" and "MCP" in res["motif"] and apres == avant


def test_edition_tout_ou_rien_texte_attendu_different():
    from src.cv import docx_mcp
    d = tempfile.mkdtemp()
    try:
        try:
            docx_mcp.appliquer_remplacements(CV, f"{d}/x.docx", [
                {"indice": 1, "avant": TITRE, "apres": AUTRE}, {"indice": 3, "avant": "texte qui n'y est pas", "apres": "x"}])
            assert False
        except docx_mcp.EchecEdition:
            pass
        assert not os.path.exists(f"{d}/x.docx") and not [f for f in os.listdir(d)]
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_ecart_deja_au_profil_est_mis_de_cote_et_duree_mesuree():
    res, _, _, _ = _personnaliser({"titre": AUTRE, "ordre_accroche": IDENTITE, "ecarts": ["Kubernetes", "Slurm", 3]})
    assert res["ecarts"] == ["Slurm"] and res["ecarts_a_tort"] == ["Kubernetes"]
    assert res["duree_modele_s"] is not None and res["titre_reference"] in TABLE["AXE_TEST"]["fr"]["titres"]


def test_le_modele_recoit_les_options_l_accroche_et_le_profil_sans_coordonnees():
    _, _, _, recu = _personnaliser({"titre": "inchangé", "ordre_accroche": IDENTITE, "ecarts": []}, annonce="Annonce X")
    msg = recu["messages"][1]["content"]
    assert f"- {AUTRE}\n" in msg and f"- {LEAD}\n" in msg and "[0] Architecte et lead technique IA" in msg
    assert "Annonce X" in msg and PROFIL["identity"]["email"] not in msg
    enum = recu["format"]["properties"]["titre"]["enum"]
    assert enum == ["inchangé", AUTRE, LEAD]                     # le titre actuel est « inchangé », pas une option de plus
    assert recu["format"]["properties"]["ordre_accroche"]["maxItems"] == 4


def test_aucune_connexion_reseau_hors_du_poste_pendant_une_personnalisation():
    """Critère d'acceptation EPIC-14 : toute connexion sortante est enregistrée, toutes doivent être locales."""
    import socket
    vues = []
    connect = socket.socket.connect
    def espion(self, adresse, *a, **k):
        vues.append(adresse); return connect(self, adresse, *a, **k)
    socket.socket.connect = espion
    try:
        res, _, _, _ = _personnaliser({"titre": AUTRE, "ordre_accroche": IDENTITE, "ecarts": []})
    finally:
        socket.socket.connect = connect
    assert res["mode"] == "adapte" and vues
    hotes = {a[0] for a in vues if isinstance(a, tuple)}
    assert hotes <= {"127.0.0.1", "::1", "localhost"}, hotes


# --- liste des titres autorisés (profile/titres_autorises.json) ---

INTERDITS = {"senior", "expert", "head", "principal"}


def test_liste_des_titres_autorises_attestee_par_chaque_cv():
    """Chaque axe et langue : le premier titre est celui du CV, chaque mot figure dans ce CV, aucun niveau
    (« Senior », « Expert », « Head of », « Principal ») qui ne soit déjà dans le CV. Seule « titres » est lue."""
    from docx import Document
    table = P.charger_titres()
    assert len(table) == 4
    for axe, d in table.items():
        for langue in ("fr", "en"):
            fichier = os.path.join(RACINE, "cv_prets", d["cv"][langue])
            doc = Document(fichier)
            assert doc.paragraphs[1].text == d[langue]["titres"][0], (axe, langue)
            cv_mots = {m.strip(".-") for m in P.mots(" ".join(p.text for p in doc.paragraphs))}
            assert len(set(d[langue]["titres"])) == len(d[langue]["titres"]) >= 3, (axe, langue)
            for t in d[langue]["titres"]:
                mots = {m.strip(".-") for m in P.mots(t)}
                assert not (mots - cv_mots), (axe, langue, t, sorted(mots - cv_mots))
                assert not (mots & INTERDITS) or (mots & INTERDITS) <= cv_mots, (axe, langue, t)
            assert P.titres_du_cv(fichier, table) == (axe, langue, d[langue]["titres"])
