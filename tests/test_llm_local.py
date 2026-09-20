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
IDENTITE = [0, 1, 2, 3]                  # ordre complet de l'accroche, résumé en tête
REP_ID = [1, 2, 3]                       # réponse du modèle : le paragraphe 0 (résumé) n'y figure pas


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


def _personnaliser(reponse, cv=CV, annonce="annonce", table=TABLE, **options):
    """Lance personnaliser contre un faux Ollama ; rend (résultat, textes des paragraphes, requête reçue)."""
    from docx import Document
    d = tempfile.mkdtemp()
    srv, url, recu = faux_ollama(reponse)
    try:
        res = P.personnaliser(LLMLocal(url), cv, f"{d}/cv.docx", annonce, PROFIL, table, **options)
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
    srv, url, recu = faux_ollama({"titre": "inchangé", "ordre_accroche": REP_ID, "ecarts": []})
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


def test_schema_impose_la_liste_et_des_indices_sans_le_resume():
    s = P.schema_selection([P.INCHANGE, AUTRE, LEAD], 4)
    assert s["properties"]["titre"]["enum"] == [P.INCHANGE, AUTRE, LEAD]
    o = s["properties"]["ordre_accroche"]
    assert o["minItems"] == o["maxItems"] == 3 and o["items"]["enum"] == [1, 2, 3]      # pas d'indice 0
    assert "substitutions" not in s["properties"]                # plus aucun texte libre, sauf les écarts


def test_titres_du_cv_par_nom_de_fichier_et_cv_inconnu():
    assert P.titres_du_cv(CV, TABLE) == ("AXE_TEST", "fr", [TITRE, AUTRE, LEAD])
    assert P.titres_du_cv(CV_EN, TABLE)[1] == "en"
    assert P.titres_du_cv(os.path.join(RACINE, "cv_prets", "FR_CONSULTANT_DATA_BI.docx"), TABLE) is None


def test_validation_titre_dans_la_liste_et_permutation_du_reste_de_l_accroche():
    opts = [P.INCHANGE, AUTRE, LEAD]
    assert P.valider_selection({"titre": AUTRE, "ordre_accroche": [2, 1, 3]}, opts, 4) == (AUTRE, [0, 2, 1, 3], None)
    assert P.valider_selection({"titre": "inchangé", "ordre_accroche": REP_ID}, opts, 4) == ("inchangé", IDENTITE, None)
    for brut in ({"titre": "ARCHITECTE IA SENIOR", "ordre_accroche": REP_ID},            # hors liste
                 {"titre": TITRE, "ordre_accroche": REP_ID},                              # titre actuel : c'est « inchangé »
                 {"titre": AUTRE, "ordre_accroche": [0, 1, 2, 3]},                        # le résumé n'est pas permutable
                 {"titre": AUTRE, "ordre_accroche": [0, 2, 3]},                           # le résumé déplacé
                 {"titre": AUTRE, "ordre_accroche": [1, 2]},                              # trop court
                 {"titre": AUTRE, "ordre_accroche": [1, 1, 2]},                           # doublon
                 {"titre": AUTRE, "ordre_accroche": [1, 2, 4]},                           # hors bornes
                 {"titre": AUTRE, "ordre_accroche": [1, 2, True]},                        # booléen
                 {"titre": AUTRE, "ordre_accroche": "123"}, {"titre": AUTRE}, {"ordre_accroche": REP_ID},
                 ["une", "liste"], "texte", None):
        t, o, motif = P.valider_selection(brut, opts, 4)
        assert t is None and o is None and motif, brut


def test_le_resume_reste_en_tete_pour_toute_permutation_acceptee():
    import itertools
    opts = [P.INCHANGE, AUTRE]
    for perm in itertools.permutations([1, 2, 3]):
        _, ordre, motif = P.valider_selection({"titre": AUTRE, "ordre_accroche": list(perm)}, opts, 4)
        assert motif is None and ordre[0] == 0 and sorted(ordre) == [0, 1, 2, 3]


def test_garde_de_role_architecte():
    assert P.contient_architecte("Offre d'emploi Architecte IA") and P.contient_architecte("Lead ARCHITECT Cloud")
    assert P.contient_architecte("Mission freelance Architectes SI") and P.contient_architecte("ARCHITECTE D’ENTREPRISE — DATA")
    assert not P.contient_architecte("Responsable Architecture Data") and not P.contient_architecte("Tech Lead IA")
    # annonce d'architecte : le titre choisi doit en contenir un
    assert not P.titre_admis_par_la_garde("Offre d'emploi Architecte IA", LEAD)
    assert P.titre_admis_par_la_garde("Offre d'emploi Architecte IA", AUTRE)
    assert P.titre_admis_par_la_garde("Senior Solution Architect", "ENTERPRISE ARCHITECT — IT URBANISATION")
    assert not P.titre_admis_par_la_garde("Senior Solution Architect", "CONSULTANT DATA ET BI — POWER BI")
    # annonce sans architecte : aucune contrainte
    assert P.titre_admis_par_la_garde("Tech Lead Data IA", LEAD) and P.titre_admis_par_la_garde("", LEAD)
    # « architecture » seul ne déclenche pas la garde et ne la satisfait pas
    assert P.titre_admis_par_la_garde("Responsable Architecture Data", LEAD)
    assert not P.titre_admis_par_la_garde("Architecte SI", "CONSULTANT — ARCHITECTURE D’ENTREPRISE")


def test_profil_envoye_au_modele_complet_sans_coordonnees():
    s = P.profil_pour_modele(PROFIL)
    assert len(s) > 9000, "le premier jet tronquait à 9000 caractères"
    assert PROFIL["identity"]["email"] not in s and "identity" not in s
    assert json.loads(s)["experiences"] == PROFIL["experiences"]


def test_melange_des_alternatives_reproductible_avec_inchange_en_tete():
    import random
    titres = [TITRE, "A — 1", "B — 2", "C — 3", "D — 4", "E — 5"]
    table = {"AXE_TEST": {"cv": {"fr": "FR_ARCHITECTE_IA_GENAI.docx"}, "fr": {"titres": titres}}}
    def options(graine):
        _, _, _, recu = _personnaliser({"titre": "inchangé", "ordre_accroche": REP_ID, "ecarts": []}, table=table,
                                       melange=None if graine is None else random.Random(graine))
        enum = recu["format"]["properties"]["titre"]["enum"]
        msg = recu["messages"][1]["content"]
        assert [l[2:] for l in msg.split("OPTIONS DE TITRE :\n")[1].split("\n\nACCROCHE")[0].split("\n")[1:]] == enum[1:]
        return enum
    fixe, m1, m1bis, m2 = options(None), options(1), options(1), options(2)
    assert fixe == ["inchangé"] + titres[1:]                       # sans graine : ordre du fichier
    assert m1 == m1bis and sorted(m1) == sorted(fixe) and m1[0] == m2[0] == "inchangé"
    assert m1 != fixe or m2 != fixe                                # l'ordre est bien mélangé


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
    res, apres, styles_apres, recu = _personnaliser({"titre": AUTRE, "ordre_accroche": REP_ID, "ecarts": []})
    assert res["mode"] == "adapte" and res["titre_avant"] == TITRE and res["titre_apres"] == AUTRE
    assert apres[1] == AUTRE and apres[2:] == avant[2:] and apres[0] == avant[0]
    assert styles_apres == styles


def test_ordre_de_l_accroche_deplace_le_texte_sans_toucher_au_resume():
    avant, styles = _textes(CV)
    res, apres, styles_apres, _ = _personnaliser({"titre": "inchangé", "ordre_accroche": [3, 1, 2], "ecarts": []})
    assert res["mode"] == "adapte" and res["ordre"] == [0, 3, 1, 2] and res["titre_apres"] == TITRE
    assert apres[3] == avant[3]                                          # le résumé reste en tête
    assert apres[4:7] == [avant[6], avant[4], avant[5]]                  # texte déplacé tel quel
    assert apres[:3] == avant[:3] and apres[7:] == avant[7:] and sorted(apres) == sorted(avant)
    assert styles_apres == styles


def test_rotation_de_l_accroche_et_titre_ensemble_sur_cv_anglais():
    avant, styles = _textes(CV_EN)
    titre_en = TABLE["AXE_TEST"]["en"]["titres"][1]
    res, apres, styles_apres, _ = _personnaliser({"titre": titre_en, "ordre_accroche": [2, 3, 1], "ecarts": []}, cv=CV_EN)
    assert res["mode"] == "adapte" and res["langue"] == "en" and apres[1] == titre_en
    assert apres[3:7] == [avant[3], avant[5], avant[6], avant[4]] and apres[7:] == avant[7:]
    assert styles_apres == styles


def test_choix_inchange_et_ordre_identique_rend_le_cv_d_axe_sans_motif():
    avant, _ = _textes(CV)
    res, apres, _, _ = _personnaliser({"titre": "inchangé", "ordre_accroche": REP_ID, "ecarts": ["Slurm"]})
    assert res["mode"] == "axe" and "motif" not in res and apres == avant and res["ecarts"] == ["Slurm"]
    assert res["ordre"] == IDENTITE and res["titre_modele"] == TITRE
    res, apres, _, _ = _personnaliser({"titre": "inchangé", "ordre_accroche": REP_ID, "ecarts": []})
    assert res["mode"] == "axe" and apres == avant


def test_reponse_invalide_rend_le_cv_d_axe_avec_motif():
    avant, _ = _textes(CV)
    cas = [({"titre": "ARCHITECTE IA SENIOR — LLM", "ordre_accroche": REP_ID, "ecarts": []}, "hors de la liste"),
           ({"titre": AUTRE, "ordre_accroche": [1, 1, 2], "ecarts": []}, "ordre d'accroche invalide"),
           ({"titre": AUTRE, "ordre_accroche": [1, 2], "ecarts": []}, "ordre d'accroche invalide"),
           ({"titre": AUTRE, "ordre_accroche": IDENTITE, "ecarts": []}, "ordre d'accroche invalide"),   # résumé permuté
           ({"titre": TITRE, "ordre_accroche": REP_ID, "ecarts": []}, "hors de la liste"),
           ('["une", "liste"]', "forme inattendue"), ('{"titre": 3}', "hors de la liste"),
           ("ceci n'est pas du JSON", "non JSON")]
    for rep, motif in cas:
        res, apres, _, _ = _personnaliser(rep)
        assert res["mode"] == "axe" and motif in res["motif"], (rep, res.get("motif"))
        assert apres == avant, rep


def test_garde_de_role_garde_le_titre_actuel_pour_une_annonce_d_architecte():
    avant, _ = _textes(CV)
    # annonce d'architecte, le modèle choisit un titre sans « architecte » : le titre actuel est gardé
    res, apres, _, _ = _personnaliser({"titre": LEAD, "ordre_accroche": REP_ID, "ecarts": []},
                                      annonce="Offre d'emploi Architecte IA\nMission ...")
    assert res["mode"] == "axe" and apres == avant and "motif" not in res
    assert res["titre_modele"] == LEAD and res["titre_apres"] == TITRE
    assert res["garde_role"] == {"declenchee": True, "titre_refuse": LEAD}
    # la garde ne touche qu'au titre : l'ordre de l'accroche choisi est appliqué
    res, apres, _, _ = _personnaliser({"titre": LEAD, "ordre_accroche": [2, 1, 3], "ecarts": []},
                                      annonce="x", titre_annonce="Architecte IA senior")
    assert res["mode"] == "adapte" and apres[1] == TITRE and apres[4] == avant[5] and apres[5] == avant[4]
    # un titre qui contient « architecte » passe
    res, apres, _, _ = _personnaliser({"titre": AUTRE, "ordre_accroche": REP_ID, "ecarts": []}, annonce="Architecte IA")
    assert apres[1] == AUTRE and res["garde_role"] == {"declenchee": True, "titre_refuse": None}
    # annonce sans « architecte » : le titre du modèle est gardé, la garde n'est pas déclenchée
    res, apres, _, _ = _personnaliser({"titre": LEAD, "ordre_accroche": REP_ID, "ecarts": []}, annonce="Tech Lead Data IA")
    assert apres[1] == LEAD and res["garde_role"] == {"declenchee": False, "titre_refuse": None}
    # « inchangé » n'est jamais refusé
    res, apres, _, _ = _personnaliser({"titre": "inchangé", "ordre_accroche": REP_ID, "ecarts": []}, annonce="Architecte IA")
    assert apres == avant and res["garde_role"]["titre_refuse"] is None


def test_cv_sans_liste_de_titres_rend_le_cv_d_axe():
    avant, _ = _textes(CV)
    res, apres, _, recu = _personnaliser({"titre": AUTRE, "ordre_accroche": REP_ID, "ecarts": []}, table={})
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
        res, apres, _, _ = _personnaliser({"titre": AUTRE, "ordre_accroche": [2, 1, 3], "ecarts": []})
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
    res, _, _, _ = _personnaliser({"titre": AUTRE, "ordre_accroche": REP_ID, "ecarts": ["Kubernetes", "Slurm", 3]})
    assert res["ecarts"] == ["Slurm"] and res["ecarts_a_tort"] == ["Kubernetes"]
    assert res["duree_modele_s"] is not None and "titre_reference" not in res     # la référence TF-IDF est abandonnée


def test_le_modele_recoit_les_options_l_accroche_et_le_profil_sans_coordonnees():
    _, _, _, recu = _personnaliser({"titre": "inchangé", "ordre_accroche": REP_ID, "ecarts": []}, annonce="Annonce X")
    msg = recu["messages"][1]["content"]
    assert f"- {AUTRE}\n" in msg and f"- {LEAD}\n" in msg and "[0] Architecte et lead technique IA" in msg
    assert "le paragraphe 0 est le résumé et reste en tête" in msg
    assert "Annonce X" in msg and PROFIL["identity"]["email"] not in msg
    enum = recu["format"]["properties"]["titre"]["enum"]
    assert enum == ["inchangé", AUTRE, LEAD]                     # le titre actuel est « inchangé », pas une option de plus
    assert recu["format"]["properties"]["ordre_accroche"]["maxItems"] == 3


def test_aucune_connexion_reseau_hors_du_poste_pendant_une_personnalisation():
    """Critère d'acceptation EPIC-14 : toute connexion sortante est enregistrée, toutes doivent être locales."""
    import socket
    vues = []
    connect = socket.socket.connect
    def espion(self, adresse, *a, **k):
        vues.append(adresse); return connect(self, adresse, *a, **k)
    socket.socket.connect = espion
    try:
        res, _, _, _ = _personnaliser({"titre": AUTRE, "ordre_accroche": REP_ID, "ecarts": []})
    finally:
        socket.socket.connect = connect
    assert res["mode"] == "adapte" and vues
    hotes = {a[0] for a in vues if isinstance(a, tuple)}
    assert hotes <= {"127.0.0.1", "::1", "localhost"}, hotes


# --- liste des titres autorisés (profile/titres_autorises.json) ---

INTERDITS = {"senior", "expert", "head", "principal"}


def test_liste_des_titres_autorises_attestee_par_chaque_cv():
    """Chaque axe et langue : le premier titre est celui du CV, chaque mot figure dans ce CV, aucun niveau
    (« Senior », « Expert », « Head of », « Principal ») qui ne soit déjà dans le CV. Seuls les titres de
    « _valides_par_le_candidat » peuvent contenir des mots absents du CV, et seulement ceux que le candidat a acceptés.
    Seule « titres » est lue par le code."""
    from docx import Document
    brut = json.load(open(P.TITRES, encoding="utf-8"))
    assert brut["_statut"].startswith("VALIDÉ par le candidat le 20/09/2026")
    valides = brut["_valides_par_le_candidat"]["titres"]
    assert brut["_valides_par_le_candidat"]["date"] == "2026-09-20"
    table = P.charger_titres()
    assert len(table) == 4
    vus = set()
    for axe, d in table.items():
        for langue in ("fr", "en"):
            fichier = os.path.join(RACINE, "cv_prets", d["cv"][langue])
            doc = Document(fichier)
            assert doc.paragraphs[1].text == d[langue]["titres"][0], (axe, langue)
            assert "a_valider" not in d[langue], "les titres non validés sont supprimés du fichier"
            cv_mots = {m.strip(".-") for m in P.mots(" ".join(p.text for p in doc.paragraphs))}
            assert len(set(d[langue]["titres"])) == len(d[langue]["titres"]) >= 3, (axe, langue)
            for t in d[langue]["titres"]:
                mots = {m.strip(".-") for m in P.mots(t)}
                hors = mots - cv_mots
                if t in valides:
                    vus.add(t)
                    assert hors <= set(valides[t]), (axe, langue, t, sorted(hors))   # rien de plus que ce que le candidat a accepté
                else:
                    assert not hors, (axe, langue, t, sorted(hors))                  # règle générale, non assouplie
                assert not (mots & INTERDITS) or (mots & INTERDITS) <= cv_mots, (axe, langue, t)
            assert P.titres_du_cv(fichier, table) == (axe, langue, d[langue]["titres"])
    assert vus == set(valides), sorted(set(valides) - vus)                            # aucune exception périmée
