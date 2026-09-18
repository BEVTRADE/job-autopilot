"""Regroupement des annonces par empreinte de contenu. Stdlib uniquement.

L'identité d'une mission n'est pas son URL : la même mission publiée par
plusieurs intermédiaires (docs/sources.md, « La rediffusion, et ce qu'elle
impose ») doit former un seul groupe, pas une entrée par source. L'empreinte
porte sur le titre normalisé et le corps de l'annonce, jamais sur la société,
qui varie d'un intermédiaire à l'autre pour une mission identique.

Volontairement indépendant de src/matching/ : regrouper est une question
d'identité, pas de notation par rapport à un CV.
"""
from __future__ import annotations
import re, unicodedata
from dataclasses import dataclass

from src.sources.base import RawMission

_STOPWORDS = {
    "le", "la", "les", "un", "une", "des", "de", "du", "d", "l", "et", "en",
    "au", "aux", "pour", "dans", "sur", "avec", "sans", "par", "ce", "cette",
    "ces", "son", "sa", "ses", "est", "sont", "ou", "qui", "que", "a", "ans",
    "mission", "poste", "profil", "client", "candidat", "recherche",
    "recherchons", "contexte", "projet", "projets", "experience",
}

_SHINGLE_SIZE = 3
DEFAULT_THRESHOLD = 0.20


def _normalize(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def normalize_title(title: str) -> str:
    """Titre normalisé : minuscules, sans accent ni ponctuation."""
    return _normalize(title)


def _significant_words(text: str) -> list[str]:
    return [w for w in _normalize(text).split()
            if w not in _STOPWORDS and not w.isdigit() and len(w) > 1]


def _shingles(words: list[str], k: int = _SHINGLE_SIZE) -> frozenset[str]:
    if len(words) < k:
        return frozenset(words)
    return frozenset(" ".join(words[i:i + k]) for i in range(len(words) - k + 1))


def fingerprint(title: str, descr: str) -> frozenset[str]:
    """Empreinte de contenu : n-grammes de mots significatifs du titre
    normalisé et du corps de l'annonce."""
    words = _significant_words(title) + _significant_words(descr)
    return _shingles(words)


def similarity(a: frozenset[str], b: frozenset[str]) -> float:
    """Similarité de Jaccard entre deux empreintes."""
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


@dataclass
class MissionGroup:
    """Un groupe d'annonces jugées identiques. Rien n'y est supprimé :
    chaque annonce reste accessible avec sa société et son TJM."""
    missions: list[RawMission]

    @property
    def best(self) -> RawMission:
        """L'intermédiaire le mieux-disant : le TJM haut le plus élevé,
        l'écart au TJM bas départageant les ex æquo."""
        return max(self.missions, key=lambda m: (m.tjm_max or -1, m.tjm_min or -1))

    @property
    def spread(self) -> int | None:
        """Écart de TJM dans le groupe : du plancher le plus bas au
        plafond le plus haut proposés pour la même mission."""
        maxes = [m.tjm_max for m in self.missions if m.tjm_max is not None]
        mins = [m.tjm_min for m in self.missions if m.tjm_min is not None]
        if not maxes or not mins:
            return None
        return max(maxes) - min(mins)

    @property
    def title(self) -> str:
        return self.best.title


def group_missions(missions: list[RawMission],
                    threshold: float = DEFAULT_THRESHOLD) -> list[MissionGroup]:
    """Regroupe des annonces par empreinte de contenu, sans rien supprimer.

    Deux annonces sont dans le même groupe si la similarité de leurs
    empreintes atteint `threshold`. Le regroupement est transitif : si A
    ressemble à B et B à C, les trois rejoignent un seul groupe, même si A
    et C ne dépassent pas le seuil entre elles (paraphrase à trois voix
    d'un même intermédiaire à l'autre).
    """
    n = len(missions)
    fps = [fingerprint(m.title, m.descr) for m in missions]
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    for i in range(n):
        for j in range(i + 1, n):
            if similarity(fps[i], fps[j]) >= threshold:
                union(i, j)

    buckets: dict[int, list[RawMission]] = {}
    for i, m in enumerate(missions):
        buckets.setdefault(find(i), []).append(m)

    return [MissionGroup(missions=ms) for ms in buckets.values()]
