"""
Source BOAMP — marchés publics français.

API Opendatasoft Explore v2.1, open data, sans clé ni quota.
Cible : AMOA SI, urbanisation, schéma directeur, architecture du SI.
Volume faible mais TJM implicites élevés et zéro friction technique.
"""
from __future__ import annotations

from .base import Source, RawMission, fetch_json

API = ("https://boamp-datadila.opendatasoft.com/api/explore/v2.1"
       "/catalog/datasets/boamp/records")

QUERIES = [
    "urbanisation système information",
    "architecture système information",
    "schéma directeur système information",
    "assistance maîtrise ouvrage informatique",
    "intelligence artificielle données",
    "plateforme données décisionnel",
]


class Boamp(Source):
    name = "boamp"

    def discover(self, cfg: dict) -> list[str]:
        self._cache = {}
        limit = cfg.get("per_query", 20)
        for q in cfg.get("queries", QUERIES):
            url = (f"{API}?limit={limit}&order_by=dateparution%20desc"
                   f"&where=" + _quote(f'search(objet,"{q}")'))
            try:
                data = fetch_json(url, timeout=30)
            except Exception:                                    # noqa: BLE001
                continue
            for rec in data.get("results", []):
                idw = str(rec.get("idweb") or "")
                if idw:
                    self._cache[f"https://www.boamp.fr/avis/detail/{idw}"] = rec
        return list(self._cache)

    def parse(self, url: str) -> RawMission | None:
        rec = getattr(self, "_cache", {}).get(url)
        if not rec:
            return None
        objet = rec.get("objet") or ""
        desc = rec.get("descripteur_libelle")
        if isinstance(desc, list):
            skills = [str(x) for x in desc][:20]
        elif desc:
            skills = [str(desc)]
        else:
            skills = []
        return RawMission(
            source=self.name,
            url=url,
            title=objet[:180],
            company=rec.get("nomacheteur"),
            job_family="marché public",
            published=rec.get("dateparution"),
            loc=rec.get("code_departement") or rec.get("lieu"),
            skills=skills,
            descr=objet[:6000],
        )


def _quote(s: str) -> str:
    from urllib.parse import quote
    return quote(s, safe="")
