"""Extraction TED (Tenders Electronic Daily) sur notices réelles enregistrées,
sans réseau.

Ces fixtures sont les réponses JSON telles que rendues par
POST https://api.ted.europa.eu/v3/notices/search le 18 septembre 2026 pour
trois notices françaises réelles (champ ND). Le titre brut de TED porte un
préfixe générique dérivé du CPV ("France – Services de ... – ") qui doit être
retiré : le garder ferait tomber toutes les notices IT sous un intitulé
quasi identique et fausserait le regroupement par empreinte (EPIC-2/7).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.sources.ted import Ted

PAGES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages")


def _parse(filename: str, nd: str):
    with open(os.path.join(PAGES, filename), encoding="utf-8") as f:
        rec = json.load(f)
    url = f"https://ted.europa.eu/fr/notice/-/detail/{nd}"
    src = Ted()
    src._cache = {url: rec}
    return src.parse(url)


def test_afpa_management_de_transition():
    m = _parse("ted_afpa_management_transition.json", "534470-2026")
    assert m.title == "Prestation de Management de Transition SI"
    assert m.company == "AFPA"
    assert m.loc == "FRA"
    assert (m.dur_val, m.dur_per) == (6, "month")
    # pas de TJM sur un marché public : un montant total de marché
    # (215 999 €) ne doit jamais être confondu avec un tarif journalier
    assert (m.tjm_min, m.tjm_max) == (None, None)
    assert m.descr.endswith("recrutement pérenne de l'Afpa.")


def test_incubation_mantes_la_jolie_titre_sans_prefixe_cpv():
    m = _parse("ted_incubation_mantes.json", "533775-2026")
    assert m.title == "Gestion d'un programme d'incubation"
    assert "France" not in m.title
    assert "Services de conseil" not in m.title
    assert m.company == "CU Grand Paris Seine & Oise"
    assert m.loc == "Mantes La Jolie"
    assert (m.dur_val, m.dur_per) == (12, "month")
    assert "L'accompagnement des porteurs de projets" in m.descr


def test_sii_centres_sante_duree_absente_geree_sans_planter():
    m = _parse("ted_sii_centres_sante.json", "534822-2026")
    assert m.title == ("Solution de gestion pour les Centres Municipaux de "
                        "Santé de Tremblay-en-France et Bobigny- Remplacement "
                        "du logiciel métier MAIDIS")
    assert m.company == "SII Syndicat Mixte des Systèmes d'Information"
    assert m.loc == "Bobigny"
    assert (m.dur_val, m.dur_per) == (None, None)
    assert "liquidation judiciaire" in m.descr
    # description complète : se termine sur la phrase réelle, pas coupée
    assert m.descr.rstrip().endswith(
        "membres du Syndicat Mixte des Systèmes d'Information (SII).")
