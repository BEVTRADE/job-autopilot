"""Modèle local et édition MCP des CV : hors ligne, avec un faux serveur Ollama."""
import json, os, sys, shutil, tempfile, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.llm.local import LLMLocal, LLMIndisponible
from src.cv import personnaliser as P

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CV = os.path.join(RACINE, "cv_prets", "FR_ARCHITECTE_IA_GENAI.docx")
PROFIL = json.load(open(os.path.join(RACINE, "profile", "master_profile.json"), encoding="utf-8"))
TITRE = "ARCHITECTE IA ET IA GÉNÉRATIVE — LLM, RAG ET AGENTS"


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
    srv, url, recu = faux_ollama({"substitutions": [], "ecarts": []})
    try:
        LLMLocal(url, num_ctx=16384).json("sys", "user", P.SCHEMA)
        assert recu["format"] == P.SCHEMA and recu["options"]["num_ctx"] == 16384
        assert recu["options"]["temperature"] == 0 and recu["stream"] is False
    finally:
        srv.shutdown()


def test_zone_titre_et_accroche_sans_coordonnees():
    z = P.zone(CV)
    assert z[0] == TITRE
    assert not any("@" in p for p in z)
    assert not any(p.startswith("Réalisations") for p in z)


def test_validation_refuse_invention_et_texte_hors_zone():
    z = P.zone(CV); v = P.vocabulaire(PROFIL, *z)
    ok, refus = P.valider({"substitutions": [
        {"avant": "LLM, RAG ET AGENTS", "apres": "AGENTS ET MLOPS"},
        {"avant": "LLM, RAG ET AGENTS", "apres": "AGENTS SUR KUBERNETES ET SLURM"},
        {"avant": "Banque Internationale", "apres": "Banque"},
        {"avant": "LLM, RAG ET AGENTS", "apres": "**AGENTS**"},
    ]}, z, v)
    assert ok == [{"avant": "LLM, RAG ET AGENTS", "apres": "AGENTS ET MLOPS"}]
    motifs = [r["motif"] for r in refus]
    assert "slurm" in motifs[0] and "hors" not in motifs[0]
    assert motifs[1].startswith("texte d'origine absent")
    assert motifs[2] == "mise en forme interdite"


def test_bout_en_bout_titre_decoupe_en_segments():
    """Le titre compte 19 segments : render.substitute échoue, le serveur MCP réussit."""
    from docx import Document
    from src.cv import render
    d = tempfile.mkdtemp()
    try:
        render.substitute(CV, f"{d}/r.docx", {TITRE: "ARCHITECTE IA — AGENTS ET MLOPS"})
        assert Document(f"{d}/r.docx").paragraphs[1].text == TITRE      # échec silencieux connu
        srv, url, _ = faux_ollama({"substitutions": [
            {"avant": "LLM, RAG ET AGENTS", "apres": "AGENTS ET MLOPS"},
            {"avant": "LLM, RAG ET AGENTS", "apres": "SLURM"}], "ecarts": ["Slurm"]})
        try:
            res = P.personnaliser(LLMLocal(url), CV, f"{d}/cv.docx", "Annonce Lead MLOps", PROFIL)
        finally:
            srv.shutdown()
        doc = Document(f"{d}/cv.docx")
        assert doc.paragraphs[1].text == "ARCHITECTE IA ET IA GÉNÉRATIVE — AGENTS ET MLOPS"
        assert len(doc.paragraphs) == len(Document(CV).paragraphs)
        assert res["mode"] == "adapte" and len(res["appliquees"]) == 1
        assert res["ecarts"] == ["Slurm"] and "slurm" in res["refus"][0]["motif"]
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_modele_defaillant_rend_le_cv_d_axe():
    from docx import Document
    d = tempfile.mkdtemp()
    srv, url, _ = faux_ollama("ceci n'est pas du JSON")
    try:
        res = P.personnaliser(LLMLocal(url), CV, f"{d}/cv.docx", "annonce", PROFIL)
        assert res["mode"] == "axe" and "non JSON" in res["motif"]
        assert Document(f"{d}/cv.docx").paragraphs[1].text == TITRE
    finally:
        srv.shutdown(); shutil.rmtree(d, ignore_errors=True)


def test_profil_envoye_au_modele_complet_sans_coordonnees():
    s = P.profil_pour_modele(PROFIL)
    assert len(s) > 9000, "le premier jet tronquait à 9000 caractères"
    assert PROFIL["identity"]["email"] not in s and "identity" not in s
    assert json.loads(s)["experiences"] == PROFIL["experiences"]


def test_ecart_deja_au_profil_est_mis_de_cote_et_apostrophe_typographique():
    d = tempfile.mkdtemp()
    srv, url, _ = faux_ollama({"substitutions": [{"avant": "LLM, RAG ET AGENTS", "apres": "AGENTS ET MLOPS"}],
                               "ecarts": ["Kubernetes", "Slurm"]})
    try:
        res = P.personnaliser(LLMLocal(url), CV, f"{d}/cv.docx", "annonce", PROFIL)
        assert res["ecarts"] == ["Slurm"] and res["ecarts_a_tort"] == ["Kubernetes"]
        assert res["nb_propositions"] == 1 and res["duree_modele_s"] is not None
        ok, _ = P.valider({"substitutions": [{"avant": "Opérationnel sur l’ensemble", "apres": "Architecte sur l'ensemble"}]},
                          ["Opérationnel sur l’ensemble de la chaîne"],
                          P.vocabulaire(PROFIL, "Opérationnel sur l’ensemble de la chaîne"))
        assert ok[0]["apres"] == "Architecte sur l’ensemble"
    finally:
        srv.shutdown(); shutil.rmtree(d, ignore_errors=True)


def test_reponse_de_forme_inattendue_rend_le_cv_d_axe():
    from docx import Document
    for rep in ('["une", "liste"]', '{"substitutions": "texte", "ecarts": 3}', '{"substitutions": [42], "ecarts": []}'):
        d = tempfile.mkdtemp()
        srv, url, _ = faux_ollama(rep)
        try:
            res = P.personnaliser(LLMLocal(url), CV, f"{d}/cv.docx", "annonce", PROFIL)
            assert res["mode"] == "axe" and res["appliquees"] == [], rep
            assert Document(f"{d}/cv.docx").paragraphs[1].text == TITRE
        finally:
            srv.shutdown(); shutil.rmtree(d, ignore_errors=True)


def test_echec_du_serveur_mcp_rend_le_cv_d_axe(monkeypatch=None):
    from docx import Document
    from src.cv import docx_mcp
    d = tempfile.mkdtemp()
    srv, url, _ = faux_ollama({"substitutions": [{"avant": "LLM, RAG ET AGENTS", "apres": "AGENTS ET MLOPS"}], "ecarts": []})
    vrai = docx_mcp._appliquer
    async def casse(*a, **k):
        raise docx_mcp.EchecEdition("serveur simulé en panne")
    docx_mcp._appliquer = casse
    try:
        res = P.personnaliser(LLMLocal(url), CV, f"{d}/cv.docx", "annonce", PROFIL)
        assert res["mode"] == "axe" and "MCP" in res["motif"] and res["nb_propositions"] == 1
        assert Document(f"{d}/cv.docx").paragraphs[1].text == TITRE
    finally:
        docx_mcp._appliquer = vrai; srv.shutdown(); shutil.rmtree(d, ignore_errors=True)


def test_aucune_connexion_reseau_hors_du_poste_pendant_une_personnalisation():
    """Critère d'acceptation EPIC-14 : toute connexion sortante est enregistrée, toutes doivent être locales."""
    import socket
    vues = []
    connect = socket.socket.connect
    def espion(self, adresse, *a, **k):
        vues.append(adresse); return connect(self, adresse, *a, **k)
    d = tempfile.mkdtemp()
    srv, url, _ = faux_ollama({"substitutions": [{"avant": "LLM, RAG ET AGENTS", "apres": "AGENTS ET MLOPS"}], "ecarts": []})
    socket.socket.connect = espion
    try:
        res = P.personnaliser(LLMLocal(url), CV, f"{d}/cv.docx", "annonce", PROFIL)
    finally:
        socket.socket.connect = connect; srv.shutdown(); shutil.rmtree(d, ignore_errors=True)
    assert res["mode"] == "adapte" and vues
    hotes = {a[0] for a in vues if isinstance(a, tuple)}
    assert hotes <= {"127.0.0.1", "::1", "localhost"}, hotes


# --- Faux refus du validateur (EPIC-14, étape 4) : ils ne doivent pas rouvrir la porte aux mots de l'annonce ---

ZONE_MINI = ["ARCHITECTE IA ET IA GÉNÉRATIVE — LLM, RAG ET AGENTS",
             "Opérationnel sur l’ensemble de la chaîne, en environnement bancaire sécurisé."]
VOCAB_MINI = P.vocabulaire({"competences": ["MLOps", "Kubernetes"]}, *ZONE_MINI)


def test_pluriel_et_feminin_d_un_mot_du_profil_ne_sont_pas_refuses():
    """Mesuré : « environnements », « bancaires », « opérationnelle » refusés à tort alors que le profil dit
    « environnement », « bancaire », « opérationnel »."""
    ok, refus = P.valider({"substitutions": [
        {"avant": "Opérationnel sur l’ensemble de la chaîne",
         "apres": "Opérationnelle sur l’ensemble des environnements bancaires sécurisés"}]}, ZONE_MINI, VOCAB_MINI)
    assert not refus and len(ok) == 1
    assert P._formes("securisees") & {"securisee", "securise"}      # féminin pluriel, en deux pas
    assert "operationnel" in P._formes("operationnelles")


def test_un_mot_de_l_annonce_reste_refuse_meme_proche_d_un_mot_du_profil():
    """Aucune extension du vocabulaire : niveau, outil ou synonyme absents du profil restent refusés."""
    _, refus = P.valider({"substitutions": [
        {"avant": "Opérationnel sur l’ensemble de la chaîne",
         "apres": "Expert senior GCP sur les environnements bancaires robustes"}]}, ZONE_MINI, VOCAB_MINI)
    assert len(refus) == 1
    absents = refus[0]["motif"].split(" : ")[1].split(", ")
    assert absents == ["expert", "gcp", "robustes", "senior"]        # « environnements », « bancaires » admis
    # deux mots distincts ne se confondent pas parce qu'ils se ressemblent
    v = {"sa", "domain", "expert"}
    _, refus = P.valider({"substitutions": [{"avant": "ARCHITECTE", "apres": "sas domaine expertise"}]},
                         ["ARCHITECTE"], v)
    assert refus[0]["motif"].endswith("domaine, expertise, sas")


def test_texte_d_origine_recopie_avec_une_autre_casse_ou_apostrophe():
    """Mesuré : le modèle écrit « Architecte IA ET IA GÉNÉRATIVE… » pour un titre en capitales, et « l'ensemble »
    pour « l’ensemble ». L'extrait réel du CV est utilisé, pas celui du modèle."""
    ok, refus = P.valider({"substitutions": [
        {"avant": "Architecte IA ET IA GÉNÉRATIVE — LLM, RAG ET AGENTS", "apres": "ARCHITECTE IA ET MLOPS"},
        {"avant": "opérationnel sur l'ensemble", "apres": "Opérationnel sur l’ensemble et Kubernetes"},
        {"avant": "Texte absent du CV", "apres": "Kubernetes"}]}, ZONE_MINI, VOCAB_MINI)
    assert [o["avant"] for o in ok] == ["ARCHITECTE IA ET IA GÉNÉRATIVE — LLM, RAG ET AGENTS",
                                        "Opérationnel sur l’ensemble"]
    assert [r["motif"] for r in refus] == ["texte d'origine absent de la zone modifiable"]


def test_texte_d_origine_a_la_casse_pres_est_applique_par_le_serveur_mcp():
    from docx import Document
    d = tempfile.mkdtemp()
    srv, url, _ = faux_ollama({"substitutions": [{"avant": "llm, rag et agents", "apres": "AGENTS ET MLOPS"}], "ecarts": []})
    try:
        res = P.personnaliser(LLMLocal(url), CV, f"{d}/cv.docx", "annonce", PROFIL)
        assert res["mode"] == "adapte" and not res["refus"], res
        assert Document(f"{d}/cv.docx").paragraphs[1].text == "ARCHITECTE IA ET IA GÉNÉRATIVE — AGENTS ET MLOPS"
    finally:
        srv.shutdown(); shutil.rmtree(d, ignore_errors=True)
