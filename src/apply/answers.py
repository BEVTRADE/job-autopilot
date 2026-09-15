"""
Banque de réponses aux questions filtrantes.

Les questions varient d'une offre à l'autre mais tournent autour d'un petit
nombre de thèmes sur ce segment. On apparie par recouvrement de vocabulaire,
et on ne répond que si la correspondance est franche : mieux vaut interrompre
la candidature que produire une réponse à côté.
"""
from __future__ import annotations
import json, os

from ..matching.text import tokens

BANK_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "profile", "reponses_types.json")

SEUIL = 0.42          # recouvrement minimal pour accepter une réponse


def _load() -> list[dict]:
    if not os.path.exists(BANK_PATH):
        return []
    return json.load(open(BANK_PATH, encoding="utf-8"))["reponses"]


def repondre(question: str, limite: int = 1200) -> tuple[str | None, float, str | None]:
    """Renvoie (réponse, score, clé) ou (None, score, None) si rien ne colle."""
    q = set(tokens(question))
    if not q:
        return None, 0.0, None
    best, score, key = None, 0.0, None
    for e in _load():
        decl = set()
        for m in e["declencheurs"]:
            decl |= set(tokens(m))
        if not decl:
            continue
        # dénominateur = le plus court des deux ensembles : une question brève
        # ne doit pas être pénalisée par un déclencheur verbeux, ni l'inverse
        inter = len(q & decl)
        s = inter / max(min(len(q), len(decl)), 1)
        if s > score:
            best, score, key = e["texte"], s, e["cle"]
    if score < SEUIL:
        return None, score, None
    return best[:limite].rstrip(), score, key
