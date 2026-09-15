"""
Source Free-Work.

Découverte via les sitemaps XML publics (pas de crawl brutal) puis
pré-filtrage sur le segment "famille de métier" de l'URL avant de charger
la moindre page de détail. Sur ~7000 offres, ce filtre en laisse quelques
centaines : on divise par vingt le nombre de requêtes.

Les rendements par famille sont mesurés sur candidatures.db :
  Architecte d'entreprise / urbaniste SI   42 % au-dessus de 650 €
  Manager de transition                    67 %
  Consultant en architecture               39 %
  Architecte de base de données            25 %
"""
from __future__ import annotations
import re

from .base import (Source, RawMission, fetch, html_to_text,
                   parse_tjm, parse_duration, parse_remote)

SITEMAPS = [
    "https://statics.free-work.com/sitemap-job-postings-fr--tech.xml",
]

# Fragments recherchés dans le segment famille-de-métier de l'URL.
FAMILY_KEYWORDS = [
    "architecte", "urbaniste", "architecture",
    "directeur", "directrice", "responsable-de-projet", "manager-de-transition",
    "chief-data", "responsable-de-la-data", "project-management-officer", "pmo",
    "tech-lead", "lead-developer",
    "data-scientist", "machine-learning", "intelligence-artificielle",
    "consultant-e-decisionnel", "business-intelligence",
    "chef-fe-de-projet", "chef-de-projet",
    "cto", "directeur-rice-technique",
]

_LOC = re.compile(r"(?m)^\s*<loc>\s*(.*?)\s*</loc>")
_JOB_URL = re.compile(r"/job-mission/([^/]+)/([^/?#]+)")

_TITLE = re.compile(r"(?is)<h1[^>]*>(.*?)</h1>")
_OGTITLE = re.compile(r'(?i)<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']')
_SKILL = re.compile(r"(?i)/jobs/([a-z0-9\-]+)\"[^>]*>\s*([^<]{2,40})\s*<")


class FreeWork(Source):
    name = "freework"

    def discover(self, cfg: dict) -> list[str]:
        keywords = [k.lower() for k in cfg.get("family_keywords", FAMILY_KEYWORDS)]
        limit = cfg.get("max_urls", 400)
        seen, out = set(), []
        for sm in cfg.get("sitemaps", SITEMAPS):
            try:
                xml = fetch(sm, timeout=40)
            except Exception:                                    # noqa: BLE001
                continue
            for url in _LOC.findall(xml):
                m = _JOB_URL.search(url)
                if not m:
                    continue
                family = m.group(1).lower()
                if keywords and not any(k in family for k in keywords):
                    continue
                if url in seen:
                    continue
                seen.add(url)
                out.append(url)
                if len(out) >= limit:
                    return out
        return out

    def parse(self, url: str) -> RawMission | None:
        try:
            html = fetch(url)
        except Exception:                                        # noqa: BLE001
            return None
        text = html_to_text(html)

        title = ""
        m = _TITLE.search(html) or _OGTITLE.search(html)
        if m:
            title = html_to_text(m.group(1)).strip()
        if not title:
            fam = _JOB_URL.search(url)
            title = (fam.group(2).replace("-", " ").title() if fam else url)

        head = text[:2500]
        lo, hi = parse_tjm(head)
        if lo is None:
            lo, hi = parse_tjm(text)
        dv, dp = parse_duration(head)

        fam = _JOB_URL.search(url)
        skills = self._skills(html)

        return RawMission(
            source=self.name,
            url=url,
            title=title,
            company=self._company(text),
            job_family=fam.group(1).replace("-", " ") if fam else None,
            tjm_min=lo, tjm_max=hi,
            remote=parse_remote(head) or parse_remote(text),
            loc=self._location(head),
            dur_val=dv, dur_per=dp,
            skills=skills,
            descr=text[:6000],
        )

    # ---------------- extracteurs spécifiques ----------------

    @staticmethod
    def _skills(html: str) -> list[str]:
        out, seen = [], set()
        for _, label in _SKILL.findall(html):
            s = label.strip()
            k = s.lower()
            if 2 <= len(s) <= 40 and k not in seen:
                seen.add(k)
                out.append(s)
        return out[:25]

    @staticmethod
    def _company(text: str) -> str | None:
        m = re.search(r"(?i)\b(publi[ée]e?\s+par|soci[ée]t[ée]|entreprise)\s*:?\s*([^\n]{2,60})", text)
        return m.group(2).strip() if m else None

    @staticmethod
    def _location(text: str) -> str | None:
        m = re.search(r"(?i)(Île-de-France|Ile-de-France|Paris|Hauts-de-Seine|"
                      r"Auvergne-Rhône-Alpes|Occitanie|Nouvelle-Aquitaine|Bretagne|"
                      r"Grand Est|Hauts-de-France|Normandie|PACA|Provence|"
                      r"Luxembourg|Belgique|Suisse|Remote|Télétravail)[^\n]{0,40}", text)
        return m.group(0).strip()[:60] if m else None
