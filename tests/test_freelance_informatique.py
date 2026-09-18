"""Extraction Freelance-Informatique sur pages réelles enregistrées, sans réseau.

Le TJM structuré ("Tarif Journalier Moyen") de cette source est verrouillé
derrière un lien de connexion sur la quasi-totalité des annonces observées le
18 septembre 2026 ; seule la prose du corps de l'annonce le porte
("TJM maximum 470 euros", "TJM de 700 à 750 €", ...). Ces tests figent trois
formulations réellement rencontrées.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.sources import freelance_informatique as fi_mod
from src.sources.freelance_informatique import FreelanceInformatique

PAGES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages")


def _load(name: str) -> str:
    with open(os.path.join(PAGES, name), encoding="utf-8") as f:
        return f.read()


def _parse(filename: str, url: str):
    """Charge une page enregistrée à la place d'un appel réseau."""
    html = _load(filename)
    original = fi_mod.fetch
    fi_mod.fetch = lambda u, **kw: html
    try:
        return FreelanceInformatique().parse(url)
    finally:
        fi_mod.fetch = original


def test_pmo_transverse_tjm_plafond_simple():
    m = _parse("freelance_informatique_pmo.html",
               "https://www.freelance-informatique.fr/mission-pmo-a-paris-13eme-260908B002")
    assert m.title == "PMO transverse"
    assert m.company is None
    assert (m.tjm_min, m.tjm_max) == (None, 470)
    assert m.loc == "75013 Paris"
    assert (m.dur_val, m.dur_per) == (3, "month")
    # corps complet, pas seulement l'amorce avec le TJM
    assert "Direction Plateforme Collaborateurs" in m.descr
    assert len(m.descr) > 500


def test_dba_tjm_plafond_avec_maximum_apres():
    m = _parse("freelance_informatique_dba.html",
               "https://www.freelance-informatique.fr/mission-dba-multi-sgbd-sur-paris-13eme-260908B001")
    assert m.title == "DBA ORACLE/SQL SERVER"
    assert m.company is None
    assert (m.tjm_min, m.tjm_max) == (None, 460)
    assert m.loc == "75013 Paris"
    assert (m.dur_val, m.dur_per) == (24, "month")
    assert m.remote == "partial"
    assert "40 DBA" in m.descr


def test_ingenieur_linux_tjm_fourchette():
    m = _parse("freelance_informatique_linux.html",
               "https://www.freelance-informatique.fr/mission-ingenieur-e-systemes-linux-senior-hybride-260831C002")
    assert m.title == "Ingénieur(e) Systèmes Linux Senior - Hybride"
    assert (m.tjm_min, m.tjm_max) == (700, 750)
    assert m.loc == "75007 Paris"
    assert (m.dur_val, m.dur_per) == (12, "month")
    # description complète : elle se termine sur la phrase réelle de l'annonce,
    # pas coupée en plein milieu par une troncature trop courte
    assert m.descr.rstrip().endswith("Hybride, 3 jours sur site.")


def test_json_ld_avec_caractere_de_controle_non_echappe():
    """Le bloc JobPosting de la page DBA contient un retour à la ligne littéral
    dans la description : json.loads strict lève ValueError, d'où strict=False."""
    html = _load("freelance_informatique_dba.html")
    ld = FreelanceInformatique._job_posting_ld(html)
    assert ld is not None
    assert ld["title"] == "DBA ORACLE/SQL SERVER"
