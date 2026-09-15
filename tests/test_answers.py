"""Banque de réponses : ce qui doit être reconnu, et ce qui doit être refusé."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.apply.answers import repondre, SEUIL

RECONNUES = [
    "Disposez-vous d'une expérience concrète sur des architectures LLM "
    "(RAG, agents, embeddings) en contexte de production ?",
    "Quel est votre niveau en Python et pouvez-vous partager un exemple de "
    "réalisation récente ?",
    "Êtes-vous en mesure d'intervenir en freelance à Paris ou en mode hybride "
    "dès que possible ?",
]

REFUSEES = [
    "Quelle est votre couleur préférée ?",
    "Avez-vous déjà travaillé sur des automates programmables Siemens S7 ?",
    "",
]


def test_reconnues():
    for q in RECONNUES:
        texte, score, cle = repondre(q)
        assert texte is not None, f"non reconnue : {q[:60]}"
        assert score >= SEUIL
        assert cle
        assert len(texte) > 30


def test_refusees():
    for q in REFUSEES:
        texte, score, cle = repondre(q)
        assert texte is None, f"réponse inventée pour : {q[:60]!r}"
        assert cle is None


def test_limite_longueur():
    texte, _, _ = repondre(RECONNUES[0], limite=80)
    assert texte is not None and len(texte) <= 80
