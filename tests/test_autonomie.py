"""EPIC-9 : message de fin d'exécution et statut de session expirée."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.report.notify import message
from src.report import digest


def test_session_expiree_prioritaire_et_urgente():
    titre, corps, urgent = message({"session_expiree": 1, "envoyee": 2}, 5)
    assert "session" in titre.lower() and urgent and "login" in corps


def test_envoi_normal_non_urgent():
    titre, corps, urgent = message({"envoyee": 2, "simulee": 0}, 4)
    assert corps == "2 envoyées" and not urgent


def test_blocage_rend_urgent():
    titre, corps, urgent = message({"envoyee": 1, "bloquee": 1}, 3)
    assert urgent and "1 à reprendre" in corps and "action" in titre.lower()


def test_rien_tente_le_dit():
    _, corps, urgent = message({}, 0)
    assert "aucune tentée" in corps and not urgent


def test_statut_session_connu_du_rapport():
    assert "session_expiree" in digest.STATUTS
    assert "session_expiree" in digest.LIBELLE
