"""Branchement du regroupement dans la collecte (EPIC-7). Données figées,
sans réseau : réutilise les cas réels d'EPIC-2 (tests.test_grouping) et
vérifie le passage complet regroupement -> notation -> rapport, ainsi que le
garde-fou contre la double candidature via l'historique (critère 6).
"""
import dataclasses, json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sources.base import RawMission
from src.matching.matcher import Match
from src.store import Store
import scripts.collect as collect

from tests.test_grouping import (
    MEUDON_GROUP, MEUDON_NICHOLSON, MEUDON_CRAFTMAN, MEUDON_SIGNEPLUS,
    VOLT_GROUP, REASSURANCE_GROUP, LEVALLOIS_HEXAGONE,
    DATA_SEUL_TJM, DATA_SANS_TJM_A, DATA_SANS_TJM_B,
)


def _match(raw: RawMission, verdict: str = "apply", **kw) -> Match:
    base = dict(aid=raw.uid, title=raw.title, company=raw.company,
                tjm_min=raw.tjm_min, tjm_max=raw.tjm_max,
                axis_id="ARCHITECTE_IA_GENAI", axis_label="Architecte IA GenAI",
                lang="fr", cv_path="", fit=80, value=80, decision_score=80,
                verdict=verdict)
    base.update(kw)
    return Match(**base)


class FakeMatcher:
    """Note sur le TJM haut : ne recalcule rien du moteur réel, sert juste
    à vérifier que scripts.collect appelle bien le matching une fois par
    groupe, sur les bons champs — le scoring lui-même est du ressort de
    src/matching/, déjà testé ailleurs."""

    def __init__(self):
        self.calls: list[dict] = []

    def match(self, mission: dict) -> Match:
        self.calls.append(mission)
        verdict = "apply" if (mission["tjm_max"] or 0) >= 450 else "shortlist"
        return Match(aid=mission["aid"], title=mission["title"],
                     company=mission["company"], tjm_min=mission["tjm_min"],
                     tjm_max=mission["tjm_max"], axis_id="AX", axis_label="Axe",
                     lang="fr", cv_path="", fit=80, value=80, decision_score=80,
                     verdict=verdict)


# --------------------------------------------------------------------------- #
#  Regroupement avant notation : un seul appel au matcher par groupe
# --------------------------------------------------------------------------- #

def test_un_seul_appel_matcher_par_groupe():
    fm = FakeMatcher()
    resultats = collect.noter_missions(MEUDON_GROUP, fm, store=None)
    assert len(resultats) == 1
    assert len(fm.calls) == 1


def test_notation_porte_sur_lannonce_du_mieux_disant():
    fm = FakeMatcher()
    resultats = collect.noter_missions(MEUDON_GROUP, fm, store=None)
    match, ref, groupe = resultats[0]
    assert ref is groupe.best
    assert ref.company == "Nicholson SAS"
    assert fm.calls[0]["company"] == "Nicholson SAS"
    assert fm.calls[0]["tjm_max"] == 500


def test_notation_sur_premiere_annonce_si_mieux_disant_indetermine():
    """Groupe sans aucun TJM : on note quand même (sur la première annonce),
    mais rien ne prétend qu'elle est la mieux-disante."""
    fm = FakeMatcher()
    resultats = collect.noter_missions([DATA_SANS_TJM_A, DATA_SANS_TJM_B], fm, store=None)
    assert len(resultats) == 1
    match, ref, groupe = resultats[0]
    assert groupe.best is None
    assert ref is groupe.missions[0]


def test_plusieurs_groupes_distincts_notes_separement():
    fm = FakeMatcher()
    lot = MEUDON_GROUP + VOLT_GROUP + REASSURANCE_GROUP + [LEVALLOIS_HEXAGONE]
    resultats = collect.noter_missions(lot, fm, store=None)
    assert len(resultats) == 4
    assert len(fm.calls) == 4


# --------------------------------------------------------------------------- #
#  Critère 6 — l'historique ne déclenche pas deux candidatures pour deux
#  annonces du même groupe
# --------------------------------------------------------------------------- #

def test_historique_empeche_deuxieme_candidature_meme_groupe():
    tmp = tempfile.mkdtemp()
    store = Store(os.path.join(tmp, "radar.db"))
    # jour 1 : la mission a déjà été vue et notée via Nicholson
    store.record(MEUDON_NICHOLSON, _match(MEUDON_NICHOLSON, verdict="apply"))

    # jour 2 : l'annonce Nicholson a expiré, seule Craftman republie la même
    # mission -- même groupe, uid différent (société différente)
    fm = FakeMatcher()
    resultats = collect.noter_missions([MEUDON_CRAFTMAN], fm, store=store)

    assert resultats == []
    assert fm.calls == []          # jamais renoté : pas de deuxième candidature


def test_historique_nempeche_pas_une_mission_reellement_nouvelle():
    tmp = tempfile.mkdtemp()
    store = Store(os.path.join(tmp, "radar.db"))
    store.record(MEUDON_NICHOLSON, _match(MEUDON_NICHOLSON, verdict="apply"))

    fm = FakeMatcher()
    resultats = collect.noter_missions([LEVALLOIS_HEXAGONE], fm, store=store)

    assert len(resultats) == 1
    assert len(fm.calls) == 1


def test_deja_connu_detecte_le_recoupement_dempreinte():
    tmp = tempfile.mkdtemp()
    store = Store(os.path.join(tmp, "radar.db"))
    store.record(MEUDON_NICHOLSON, _match(MEUDON_NICHOLSON, verdict="apply"))

    historique = collect.empreintes_historiques(store)
    assert len(historique) == 1

    groupe_meme_mission = collect.former_groupes([MEUDON_CRAFTMAN])[0]
    groupe_autre_mission = collect.former_groupes([LEVALLOIS_HEXAGONE])[0]

    assert collect.deja_connu(groupe_meme_mission, historique) is True
    assert collect.deja_connu(groupe_autre_mission, historique) is False


def test_deja_connu_sans_historique_ne_bloque_rien():
    assert collect.deja_connu(collect.former_groupes(MEUDON_GROUP)[0], []) is False


# --------------------------------------------------------------------------- #
#  Rapport : une ligne par mission (groupe), pas par annonce
# --------------------------------------------------------------------------- #

def test_rapport_une_ligne_par_groupe_avec_intermediaires_en_regard():
    fm = FakeMatcher()
    resultats = collect.noter_missions(MEUDON_GROUP + [LEVALLOIS_HEXAGONE], fm, store=None)
    stats = {"freework": {"discovered": 4, "parsed": 4, "skipped": 0,
                           "apply": 0, "shortlist": 0, "reject": 0}}
    for match, ref, groupe in resultats:
        stats["freework"][match.verdict] += 1

    out_dir = tempfile.mkdtemp()
    path = collect.write_report(resultats, stats, out_dir=out_dir)
    html = open(path, encoding="utf-8").read()

    assert html.count("<tr class=") == 2          # deux groupes, pas quatre annonces
    for company in ("Nicholson SAS", "Craftman data", "Signe +"):
        assert company in html
    assert "Hexagone Digitale" in html

    retenues = json.load(open(os.path.join(out_dir, "retenues.json"), encoding="utf-8"))
    assert len(retenues) == 2
    meudon = next(r for r in retenues if r["raw"]["company"] == "Nicholson SAS")
    assert {i["company"] for i in meudon["groupe"]} == {
        "Nicholson SAS", "Craftman data", "Signe +"}


def test_rapport_signale_ecart_et_absence_de_tjm():
    fm = FakeMatcher()
    resultats = collect.noter_missions(
        [DATA_SEUL_TJM, DATA_SANS_TJM_A, DATA_SANS_TJM_B], fm, store=None)
    stats = {"freework": {"discovered": 3, "parsed": 3, "skipped": 0,
                           "apply": 0, "shortlist": 0, "reject": 0}}
    for match, ref, groupe in resultats:
        stats["freework"][match.verdict] += 1

    out_dir = tempfile.mkdtemp()
    path = collect.write_report(resultats, stats, out_dir=out_dir)
    html = open(path, encoding="utf-8").read()

    assert "2 sans TJM" in html
    # l'écart n'est pas affiché comme un chiffre trompeur (largeur de
    # fourchette d'une seule annonce) : une seule annonce a un TJM ici
    assert "écart" not in html.lower() or "50" not in html


def test_rapport_groupe_sans_aucun_tjm_signale_indetermine():
    fm = FakeMatcher()
    resultats = collect.noter_missions([DATA_SANS_TJM_A, DATA_SANS_TJM_B], fm, store=None)
    stats = {"freework": {"discovered": 2, "parsed": 2, "skipped": 0,
                           "apply": 0, "shortlist": 0, "reject": 0}}
    for match, ref, groupe in resultats:
        stats["freework"][match.verdict] += 1

    out_dir = tempfile.mkdtemp()
    path = collect.write_report(resultats, stats, out_dir=out_dir)
    html = open(path, encoding="utf-8").read()
    assert "indéterminé" in html.lower()
