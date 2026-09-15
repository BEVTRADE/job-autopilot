"""Moteur de décision : garde-fous de calibrage."""
import os, sys, dataclasses
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.matching.matcher import Matcher, Params

CV = {"ARCHITECTE_IA_GENAI":
      "architecte ia generative llm rag agents mcp python kubernetes docker "
      "mlops llmops embeddings prompt engineering gouvernance ia",
      "CONSULTANT_DATA_BI":
      "consultant decisionnel power bi sql cognos modelisation reporting"}

BONNE = {"aid": "t1", "title": "Architecte IA Générative", "company": "X",
         "job": "architecte", "skills": ["LLM", "RAG", "Python", "Kubernetes"],
         "descr": "Architecture de plateforme IA générative, agents, RAG, MLOps",
         "tjm_min": 700, "tjm_max": 800, "remote": "partial",
         "dur_val": 12, "dur_per": "mois"}

FAIBLE = {"aid": "t2", "title": "Développeur COBOL mainframe", "company": "Y",
          "job": "developpeur", "skills": ["COBOL", "JCL"],
          "descr": "Maintenance applicative COBOL sur mainframe",
          "tjm_min": 300, "tjm_max": 350, "remote": "none",
          "dur_val": 6, "dur_per": "mois"}


def m():
    return Matcher(cv_texts=CV, params=Params())


def test_bonne_mieux_notee_que_faible():
    a, b = m().match(BONNE), m().match(FAIBLE)
    assert a.decision_score > b.decision_score
    assert a.fit > b.fit


def test_milieu_de_fourchette():
    """Une fourchette 640-700 ne doit pas être évaluée sur son plancher."""
    p = Params()
    haut = dict(BONNE, aid="t3", tjm_min=640, tjm_max=700)
    bas = dict(BONNE, aid="t4", tjm_min=640, tjm_max=640)
    assert Matcher(cv_texts=CV, params=p).match(haut).value > Matcher(cv_texts=CV, params=p).match(bas).value


def test_mode_contact_privilegie_le_fit():
    """En mode contact, un TJM bas ne doit pas écraser une bonne adéquation."""
    pauvre = dict(BONNE, aid="t5", tjm_min=400, tjm_max=450)
    tjm = Matcher(cv_texts=CV, params=Params()).match(pauvre)
    contact = Matcher(cv_texts=CV, params=dataclasses.replace(Params(), mode="contact")).match(pauvre)
    assert contact.decision_score > tjm.decision_score


def test_params_replace_effectif():
    """dataclasses.replace doit réellement changer la valeur (piège du 05/09)."""
    p = dataclasses.replace(Params(), tjm_floor_hard=999)
    assert p.tjm_floor_hard == 999
