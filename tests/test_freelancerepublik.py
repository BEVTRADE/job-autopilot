"""Extraction FreelanceRepublik sur pages réelles enregistrées, sans réseau.

Point vérifié le 18 septembre 2026, déterminant pour le regroupement
(EPIC-7) : le texte dupliqué en tête de page (`<div id="jp-desc">`) et le
champ `description` du JSON-LD JobPosting sont **tronqués vers 4100
caractères** — l'annonce "Technical Product Owner" coupe en plein mot
("...organisation produit stru") dans ces deux emplacements. Le corps
complet (4307 caractères, qui se termine normalement) n'existe que dans le
HTML rendu de `<div class="mission-content w-richtext">`. L'extracteur lit
cette div, jamais les deux autres — le test `test_description_non_tronquee`
le vérifie explicitement.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.sources import freelancerepublik as fr_mod
from src.sources.freelancerepublik import FreelanceRepublik

PAGES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages")


def _load(name: str) -> str:
    with open(os.path.join(PAGES, name), encoding="utf-8") as f:
        return f.read()


def _parse(filename: str, url: str):
    """Charge une page enregistrée à la place d'un appel réseau."""
    html = _load(filename)
    original = fr_mod.fetch
    fr_mod.fetch = lambda u, **kw: html
    try:
        return FreelanceRepublik().parse(url)
    finally:
        fr_mod.fetch = original


def test_functional_analyst_duree_en_prose_et_localisation_hors_france():
    m = _parse("freelancerepublik_functional_analyst.html",
               "https://www.freelancerepublik.com/missions/"
               "functional-analyst-data-analytics-67601fb4")
    assert m.title == "Functional Analyst Data & Analytics"
    assert m.company is None
    assert (m.tjm_min, m.tjm_max) == (None, None)
    assert m.loc == "Brussels, Belgium"
    assert (m.dur_val, m.dur_per) == (12, "month")
    assert m.remote == "partial"
    assert "durée 12 mois" in m.descr
    assert len(m.descr) > 500


def test_chef_de_projet_tjm_fourchette_a_tiret():
    """Fourchette au séparateur inhabituel : un tiret simple, pas "à"."""
    m = _parse("freelancerepublik_chef_de_projet.html",
               "https://www.freelancerepublik.com/missions/"
               "chef-de-projet-technique-technico-fonctionnel-7a293316")
    assert m.title == "Chef de projet technique / Technico-fonctionnel"
    assert m.company is None
    assert (m.tjm_min, m.tjm_max) == (550, 600)
    assert m.loc == "Boulogne-Billancourt, Hauts-de-Seine, France"
    assert m.remote == "partial"
    assert (m.dur_val, m.dur_per) == (None, None)


def test_description_non_tronquee():
    """Le corps complet fait 4307 caractères et se termine normalement.

    Les deux emplacements dupliqués de la page (`jp-desc` et le
    `description` du JSON-LD) coupent tous les deux à 4092-4112
    caractères, en plein mot. Un extracteur qui lirait l'un de ces deux
    champs au lieu de `mission-content` renverrait une description tronquée
    ici — et le regroupement (EPIC-7) dégraderait cette annonce en
    comparaison sur titre seul dès que le corps est absent ou coupé.
    """
    m = _parse("freelancerepublik_technical_product_owner.html",
               "https://www.freelancerepublik.com/missions/"
               "technical-product-owner-54f8d903")
    assert m.title == "Technical Product Owner"
    assert m.remote == "full"
    assert m.loc is None
    assert (m.tjm_min, m.tjm_max) == (None, None)
    assert len(m.descr) > 4200
    assert m.descr.rstrip().endswith(
        "Une culture produit qui valorise l'autonomie, la data et "
        "l'amélioration continue")
    # la troncature connue du JSON-LD/jp-desc coupe avant ce point
    assert "structurée et en pleine montée en maturité" in m.descr
