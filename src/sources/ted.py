"""
Source TED (Tenders Electronic Daily) — marchés publics européens.

API REST v3 publique et documentée, sans clé (docs.ted.europa.eu/api). Filtre
sur le pays de l'acheteur (France) et les codes CPV de conseil informatique /
gestion de projet, cohérent avec le profil visé (docs/sources.md : "Grands
programmes SI européens", cadence hebdomadaire plutôt que quotidienne).

Bizarreries propres à cette source :

- Chaque notice est multilingue : le titre (`TI`) et la description
  (`description-proc`) sont des dictionnaires par langue. La clé utile pour
  ce profil est toujours "fra" (langue de dépôt de l'acheteur français) —
  jamais "fr".
- Le titre brut inclut toujours un préfixe générique dérivé du CPV,
  répété sur des centaines de notices sans rapport : "France – Services de
  conseil en gestion de projet – Gestion d'un programme d'incubation". Le
  vrai titre de la consultation est le dernier segment, après le dernier
  tiret cadratin (–, U+2013). Garder le préfixe ferait tomber presque
  toutes les notices IT sous le même intitulé et fausserait le
  regroupement par empreinte (EPIC-2/7).
- Il n'y a pas de TJM : `estimated-value-lot` est le montant total du
  marché (souvent pluriannuel, parfois par lot), pas un tarif journalier.
  Le confondre avec un TJM produirait un chiffre absurde (ex. 215 999 €
  interprété comme un TJM). `tjm_min`/`tjm_max` restent donc `None`, comme
  pour BOAMP.
- `description-proc` est un résumé rédigé par l'acheteur (objet du
  marché), pas le cahier des charges complet : il est court par nature,
  pas tronqué par l'extraction — vérifié sur les trois notices figées.
- Certains champs (durée, ville) sont absents notice par notice ; les
  accepter comme `None` plutôt que planter est le comportement correct
  ici, pas un défaut d'extraction.
"""
from __future__ import annotations
import json, urllib.request

from .base import Source, RawMission, UA

API = "https://api.ted.europa.eu/v3/notices/search"

CPV_CODES = [
    "72000000",  # services de TI : conseil, développement, internet
    "72220000",  # services de conseil en systèmes et conseil technique
    "72224000",  # services de conseil en gestion de projets
    "72246000",  # services de conseil en systèmes
    "79400000",  # conseil en gestion et affaires (management de transition)
]

FIELDS = [
    "ND", "TI", "buyer-name", "buyer-country",
    "place-of-performance-city-lot", "place-of-performance-country-lot",
    "description-proc",
    "duration-period-value-lot", "duration-period-unit-lot",
    "links",
]

_DUR_UNIT = {"MONTH": "month", "YEAR": "year", "WEEK": "week", "DAY": "month"}


class Ted(Source):
    name = "ted"

    def discover(self, cfg: dict) -> list[str]:
        self._cache = {}
        limit = min(cfg.get("max_urls", 80), 100)
        # Un `IN (...)` sans espace après la virgule est rejeté par l'API
        # ("not supported for search field 'classification-cpv'") : vérifié
        # le 18 septembre 2026 lors de la première collecte réelle, alors
        # que chaque code isolé passe.
        cpv = ", ".join(cfg.get("cpv_codes", CPV_CODES))
        since = cfg.get("since", "20260101")
        query = (f"buyer-country=FRA AND classification-cpv IN ({cpv}) "
                 f"AND publication-date >= {since}")
        body = {"query": query, "fields": cfg.get("fields", FIELDS),
                "limit": limit, "scope": cfg.get("scope", "ALL")}
        try:
            data = _post_json(API, body, timeout=30)
        except Exception:                                        # noqa: BLE001
            return []
        out = []
        for rec in data.get("notices", []):
            nd = rec.get("ND")
            if not nd:
                continue
            url = f"https://ted.europa.eu/fr/notice/-/detail/{nd}"
            self._cache[url] = rec
            out.append(url)
        return out

    def parse(self, url: str) -> RawMission | None:
        rec = getattr(self, "_cache", {}).get(url)
        if not rec:
            return None

        title = self._title(rec)
        descr = ((rec.get("description-proc") or {}).get("fra") or "").strip()
        dv, dp = self._duration(rec)

        return RawMission(
            source=self.name,
            url=url,
            title=title,
            company=self._first(rec.get("buyer-name")),
            job_family="marché public",
            loc=self._location(rec),
            dur_val=dv, dur_per=dp,
            descr=descr[:6000],
        )

    # ---------------- extracteurs spécifiques ----------------

    @staticmethod
    def _title(rec: dict) -> str:
        raw = (rec.get("TI") or {}).get("fra") or ""
        segs = raw.split("–")  # tiret cadratin
        return segs[-1].strip() if len(segs) > 1 else raw.strip()

    @staticmethod
    def _first(field: dict | None) -> str | None:
        if not field:
            return None
        vals = field.get("fra")
        if isinstance(vals, list) and vals:
            return str(vals[0])
        return None

    @staticmethod
    def _location(rec: dict) -> str | None:
        cities = rec.get("place-of-performance-city-lot")
        if isinstance(cities, list) and cities:
            city = str(cities[0]).strip().title()
            return city
        countries = rec.get("place-of-performance-country-lot")
        if isinstance(countries, list) and countries:
            return str(countries[0])
        return None

    @staticmethod
    def _duration(rec: dict) -> tuple[int | None, str | None]:
        vals = rec.get("duration-period-value-lot")
        units = rec.get("duration-period-unit-lot")
        if not isinstance(vals, list) or not vals:
            return None, None
        try:
            n = int(vals[0])
        except (TypeError, ValueError):
            return None, None
        unit = _DUR_UNIT.get((units or [None])[0], "month") if isinstance(units, list) else "month"
        return n, unit


def _post_json(url: str, body: dict, timeout: int = 30) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"User-Agent": UA, "Content-Type": "application/json",
                 "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))
