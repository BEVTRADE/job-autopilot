"""Regroupement des annonces par empreinte de contenu. Stdlib uniquement.

L'identité d'une mission n'est pas son URL : la même mission publiée par
plusieurs intermédiaires (docs/sources.md, « La rediffusion, et ce qu'elle
impose ») doit former un seul groupe, pas une entrée par source. L'empreinte
porte sur le titre normalisé et le corps de l'annonce, jamais sur la société,
qui varie d'un intermédiaire à l'autre pour une mission identique.

Volontairement indépendant de src/matching/ : regrouper est une question
d'identité, pas de notation par rapport à un CV.

Sur-regroupement sur titre seul : traité le 18 septembre 2026. Quand au
moins une des deux annonces n'a pas de corps, le rapprochement exige
l'égalité du titre normalisé (voir `_rapprochables`). Mesure avant et après
sur les 1901 missions de calibration : 1529 groupes et un plus gros groupe
de 45 annonces sans corps, contre 1771 groupes et un plus gros groupe de 8,
toutes du même intermédiaire republiant le même intitulé. Aucune annonce
perdue, 1901 sur 1901 conservées, et le seuil n'a pas bougé.

Limite connue, documentée plutôt que traitée (revue du 18 septembre 2026,
docs/revues/epic2-empreinte.md) : deux annonces identiques dont une seule a
un corps vide retombent sous DEFAULT_THRESHOLD (0,125 mesuré contre un seuil
de 0,20) et ne se regroupent pas. La corriger proprement demanderait un
canal de comparaison distinct pour le titre seul, calibré séparément sur des
données réelles — DEFAULT_THRESHOLD lui-même n'est éprouvé que sur les
fixtures. Le garde-fou anti sur-regroupement ajouté par EPIC-7 (voir
_shingles) va dans le sens inverse : il durcit la comparaison sur texte
court, ce qui aggraverait ce sous-regroupement si on le relâchait sans
calibration. Hors périmètre d'EPIC-7 : nécessite un jeu de calibration réel.
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
    """Trigrammes de mots significatifs. Pas de secours en unigrammes sous
    la taille de shingle : c'est cette dégradation silencieuse qui amalgame
    des titres génériques et courts (« Architecte Solution » / « Architecte
    Solutions ») en un seul groupe sans rapport avec le contenu réel —
    mesuré sur les 1901 missions réelles comme un mega-groupe de 293
    annonces (revue EPIC-2, critère 2). Une empreinte trop courte pour
    former un trigramme est jugée non comparable : elle ressort vide, et
    similarity() traite toute empreinte vide comme non similaire à quoi que
    ce soit, plutôt que de comparer sur un signal trop faible."""
    if len(words) < k:
        return frozenset()
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
    def _avec_tjm(self) -> list[RawMission]:
        return [m for m in self.missions
                if m.tjm_min is not None and m.tjm_max is not None]

    @property
    def nb_sans_tjm(self) -> int:
        """Nombre d'annonces du groupe qui n'affichent aucun TJM — à
        afficher à côté de `spread` pour ne jamais laisser croire que
        l'écart couvre tout le groupe (revue EPIC-2, critère 1)."""
        return len(self.missions) - len(self._avec_tjm)

    @property
    def best(self) -> RawMission | None:
        """L'intermédiaire le mieux-disant parmi ceux qui affichent un
        TJM : le TJM haut le plus élevé, l'écart au TJM bas départageant
        les ex æquo. None si aucune annonce du groupe n'affiche de TJM —
        le mieux-disant est alors indéterminé, jamais choisi arbitrairement
        par l'ordre de tri (revue EPIC-2, critère 2)."""
        pool = self._avec_tjm
        if not pool:
            return None
        return max(pool, key=lambda m: (m.tjm_max, m.tjm_min))

    @property
    def spread(self) -> int | None:
        """Écart de TJM entre intermédiaires, calculé uniquement sur les
        annonces qui affichent un TJM. None s'il y a moins de deux annonces
        comparables : avec une seule (ou zéro), le résultat serait la
        largeur de sa propre fourchette, pas un écart entre intermédiaires
        (revue EPIC-2, critère 1)."""
        pool = self._avec_tjm
        if len(pool) < 2:
            return None
        return max(m.tjm_max for m in pool) - min(m.tjm_min for m in pool)

    @property
    def title(self) -> str:
        ref = self.best
        return (ref or self.missions[0]).title



def _rapprochables(sans_corps_a: bool, sans_corps_b: bool,
                   titre_a: str, titre_b: str) -> bool:
    """Deux annonces sont-elles comparables par empreinte ?

    Quand au moins une des deux n'a pas de corps d'annonce, l'empreinte se
    réduit au titre : deux missions distinctes portant un intitulé courant
    — « Data Engineer Senior », « Architecte technique » — franchissent alors
    le seuil sans être la même mission. Mesuré sur les 1901 missions de
    calibration : les quatre plus gros groupes, de 45 à 10 annonces, étaient
    composés à 100 % d'annonces sans corps, de sociétés et de clients
    différents.

    Dans ce cas on exige l'égalité du titre normalisé, seul signal restant
    qui soit discriminant. Sur deux annonces pourvues d'un corps, le
    rapprochement reste gouverné par le seuil de similarité : ce garde-fou
    ne touche ni au seuil ni à la calibration.
    """
    if not (sans_corps_a or sans_corps_b):
        return True
    return titre_a == titre_b and bool(titre_a)


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

    titres = [normalize_title(m.title) for m in missions]
    sans_corps = [not (m.descr or "").strip() for m in missions]

    for i in range(n):
        for j in range(i + 1, n):
            if not _rapprochables(sans_corps[i], sans_corps[j],
                                  titres[i], titres[j]):
                continue
            if similarity(fps[i], fps[j]) >= threshold:
                union(i, j)

    buckets: dict[int, list[RawMission]] = {}
    for i, m in enumerate(missions):
        buckets.setdefault(find(i), []).append(m)

    return [MissionGroup(missions=ms) for ms in buckets.values()]
