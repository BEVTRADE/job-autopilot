"""Normalisation de texte et similarité — stdlib uniquement, aucune dépendance."""
from __future__ import annotations
import math, re, unicodedata
from collections import Counter

_WORD = re.compile(r"[a-z0-9#+.]{2,}")

STOP = {
    "de","des","du","la","le","les","un","une","et","en","au","aux","pour","par","sur","dans",
    "avec","sans","chez","the","and","for","with","of","to","in","on","a","an","is","are",
    "ans","experience","expérience","ainsi","que","qui","son","ses","leur","plus","est","sont",
    "nous","vous","notre","votre","ce","cette","ces","il","elle","mission","poste","profil",
    "client","candidat","recherche","recherchons","contexte","projet","projets",
}

def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")

def norm(s: str | None) -> str:
    if not s:
        return ""
    return strip_accents(str(s)).lower()

def tokens(s: str | None) -> list[str]:
    return [w for w in _WORD.findall(norm(s)) if w not in STOP and not w.isdigit()]


class TfIdf:
    """TF-IDF + cosinus, implémentation minimale."""

    def __init__(self, docs: dict[str, str]):
        self.keys = list(docs)
        tf = {k: Counter(tokens(v)) for k, v in docs.items()}
        df = Counter()
        for c in tf.values():
            df.update(c.keys())
        n = max(len(tf), 1)
        self.idf = {t: math.log((n + 1) / (d + 1)) + 1.0 for t, d in df.items()}
        self.vecs = {k: self._vec(c) for k, c in tf.items()}

    def _vec(self, counts: Counter) -> dict[str, float]:
        v = {t: (1 + math.log(c)) * self.idf.get(t, 1.0) for t, c in counts.items()}
        n = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {t: x / n for t, x in v.items()}

    def vec(self, text: str) -> dict[str, float]:
        return self._vec(Counter(tokens(text)))

    @staticmethod
    def cos(a: dict[str, float], b: dict[str, float]) -> float:
        if len(a) > len(b):
            a, b = b, a
        return sum(x * b.get(t, 0.0) for t, x in a.items())
