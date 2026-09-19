"""Choix du CV mission par mission (défaut relevé le 19/09/2026 : toutes les
missions partaient avec le même CV, le choix du moteur était ignoré)."""
import importlib.util, os, sys
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
spec = importlib.util.spec_from_file_location("apply_script", os.path.join(RACINE, "scripts", "apply.py"))
apply_script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(apply_script)
cv_pour_mission = apply_script.cv_pour_mission


def test_axe_urbaniste_donne_son_cv():
    m = {"cv_path": "reprise/cv_finaux/FR_ARCHITECTE_ENTREPRISE_URBANISTE.docx"}
    nom, local = cv_pour_mission(m)
    assert nom == "FR_ARCHITECTE_ENTREPRISE_URBANISTE.pdf"


def test_mission_anglaise_donne_le_cv_anglais():
    m = {"cv_path": "reprise/cv_finaux/EN_ENTERPRISE_ARCHITECT.docx"}
    assert cv_pour_mission(m)[0] == "EN_ENTERPRISE_ARCHITECT.pdf"


def test_deux_axes_deux_cv_differents():
    a = cv_pour_mission({"cv_path": "x/FR_ARCHITECTE_IA_GENAI.docx"})[0]
    b = cv_pour_mission({"cv_path": "x/FR_DIRECTEUR_PROGRAMME_DATA_IA.docx"})[0]
    assert a != b


def test_fichier_local_retrouve_dans_cv_prets():
    nom, local = cv_pour_mission({"cv_path": "x/FR_ARCHITECTE_IA_GENAI.docx"})
    assert local and local.endswith(os.path.join("cv_prets", "pdf", "FR_ARCHITECTE_IA_GENAI.pdf"))


def test_cv_force_prioritaire():
    nom, local = cv_pour_mission({"cv_path": "x/FR_CONSULTANT_DATA_BI.docx"}, cv_force="MON_CV.pdf")
    assert nom == "MON_CV.pdf" and local is None


def test_fichier_force_prioritaire_et_deposable():
    nom, local = cv_pour_mission({"cv_path": "x/FR_CONSULTANT_DATA_BI.docx"},
                                 fichier_force="/tmp/CV_Dedie.pdf")
    assert nom == "CV_Dedie.pdf" and local == "/tmp/CV_Dedie.pdf"


def test_sans_cv_path_repli_generique():
    assert cv_pour_mission({})[0] == "FR_ARCHITECTE_IA_GENAI.pdf"
