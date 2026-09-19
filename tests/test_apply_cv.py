"""Correspondance du nom de CV affiché par Free-Work (blocage du 19/09/2026)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.apply.freework import meme_cv

LONG = "CV_Hakim_Arezki_Architecte_Domaine_Simulation.pdf"


def test_egalite_exacte():
    assert meme_cv(LONG, LONG)


def test_insensible_casse_et_extension():
    assert meme_cv("cv_hakim_arezki_architecte_domaine_simulation", LONG)


def test_affichage_tronque_avec_ellipse():
    assert meme_cv("CV_Hakim_Arezki_Architecte_Dom…", LONG)


def test_affichage_tronque_sans_ellipse():
    assert meme_cv("CV_Hakim_Arezki_Architecte_Domaine", LONG)


def test_prefixe_trop_court_refuse():
    """Un préfixe court désigne trop de fichiers pour être sûr."""
    assert not meme_cv("CV_Hakim", LONG)


def test_autre_cv_refuse():
    assert not meme_cv("FR_ARCHITECTE_IA_GENAI.pdf", LONG)


def test_nom_attendu_court_ne_matche_pas_un_fichier_plus_long():
    assert not meme_cv("FR_ARCHITECTE_IA_GENAI_v2.pdf", "FR_ARCHITECTE_IA_GENAI.pdf")


def test_vide_refuse():
    assert not meme_cv(None, LONG)
    assert not meme_cv("", LONG)


# --------------------------------------------------------------------------
# Contrôle du fichier local avant dépôt (chemin de dépôt du 19/09/2026)

import tempfile
from src.apply.freework import verifier_fichier_cv


def _fichier(nom, contenu=b"%PDF-1.4 contenu"):
    d = tempfile.mkdtemp()
    p = os.path.join(d, nom)
    open(p, "wb").write(contenu)
    return p


def test_fichier_pdf_valide():
    ok, raison = verifier_fichier_cv(_fichier("cv.pdf"))
    assert ok and raison == "ok"


def test_fichier_docx_valide():
    assert verifier_fichier_cv(_fichier("cv.docx"))[0]


def test_fichier_absent_refuse():
    ok, raison = verifier_fichier_cv("/nulle/part/cv.pdf")
    assert not ok and "introuvable" in raison


def test_format_refuse():
    ok, raison = verifier_fichier_cv(_fichier("cv.png"))
    assert not ok and "format" in raison


def test_fichier_vide_refuse():
    ok, raison = verifier_fichier_cv(_fichier("cv.pdf", b""))
    assert not ok and "vide" in raison


def test_aucun_chemin_refuse():
    assert not verifier_fichier_cv(None)[0]
