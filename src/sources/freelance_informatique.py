"""
Source Freelance-Informatique.

Découverte par pagination du listing public (`/offres-freelance?page=N`),
rendu serveur, sans compte. ~450 missions actives (docs/sources.md).

Bizarreries propres à cette source :

- Le TJM structuré ("Tarif Journalier Moyen") est verrouillé derrière un
  lien de connexion (`data-obf`, base64 d'une URL `/connexion?...`) sur la
  quasi-totalité des annonces observées. Le TJM réel, quand il est donné,
  n'apparaît qu'en prose dans le corps de l'annonce : "TJM maximum 470
  euros", "Le TJM ne pourra pas excéder 620 euros HT.J", "TJM de 700 à 750
  €". C'est donc le corps, pas le champ dédié, qui porte l'information.
- Le bloc JSON-LD JobPosting, quand présent, contient parfois un caractère
  de contrôle non échappé (retour à la ligne littéral) dans la description,
  ce qui fait échouer `json.loads` strict — d'où `strict=False`.
- `hiringOrganization.name` vaut toujours "Freelance-Informatique" : c'est
  la plateforme, jamais le client final, qui n'est pas nommé. La société
  n'est donc pas un champ fiable ici.
"""
from __future__ import annotations
import json, re

from .base import (Source, RawMission, fetch, html_to_text,
                    parse_duration, parse_remote)

BASE = "https://www.freelance-informatique.fr"
LISTING = BASE + "/offres-freelance"

_HREF = re.compile(r'href="(/mission-[^"?#]+)"')
_JSONLD = re.compile(r'(?is)<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>')
_TITLE = re.compile(r"(?is)<h1[^>]*>(.*?)</h1>")
_DESCR_DIV = re.compile(r'(?is)<div class="mission-description">(.*?)</div>\s*(?:</div>|<div class="subtitle")')
_DUREE = re.compile(r'(?is)title="Durée">.*?<div>\s*([^<]+?)\s*</div>\s*</div>')
_LOC_LI = re.compile(r'(?is)title="Localisation">.*?class="text-reset">\s*([^<]+?)\s*</a>')

_TJM_RANGE = re.compile(r"(?i)TJM[^\n]{0,20}?(\d{3,4})\s*(?:€|EUR)?\s*(?:à|-|–)\s*(\d{3,4})\s*(?:€|EUR)")
_TJM_CEIL = re.compile(r"(?i)TJM[^\n]{0,45}?(\d{3,4})\s*(?:€|euros?)")


class FreelanceInformatique(Source):
    name = "freelance_informatique"

    def discover(self, cfg: dict) -> list[str]:
        limit = cfg.get("max_urls", 200)
        max_pages = cfg.get("max_pages", 10)
        seen, out = set(), []
        for page in range(1, max_pages + 1):
            url = LISTING if page == 1 else f"{LISTING}?page={page}"
            try:
                html = fetch(url, timeout=30)
            except Exception:                                    # noqa: BLE001
                continue
            hrefs = _HREF.findall(html)
            if not hrefs:
                break
            for h in hrefs:
                full = BASE + h
                if full in seen:
                    continue
                seen.add(full)
                out.append(full)
                if len(out) >= limit:
                    return out
        return out

    def parse(self, url: str) -> RawMission | None:
        try:
            html = fetch(url)
        except Exception:                                        # noqa: BLE001
            return None

        ld = self._job_posting_ld(html)

        title = ""
        if ld and ld.get("title"):
            title = html_to_text(str(ld["title"])).strip()
        if not title:
            m = _TITLE.search(html)
            title = html_to_text(m.group(1)).strip() if m else url

        descr = self._descr(ld, html)
        tjm_min, tjm_max = self._tjm(descr)
        dv, dp = self._duration(html, descr)

        return RawMission(
            source=self.name,
            url=url,
            title=title,
            company=None,
            tjm_min=tjm_min, tjm_max=tjm_max,
            remote=parse_remote(descr) or self._remote_pct(descr),
            loc=self._location(ld, html),
            dur_val=dv, dur_per=dp,
            descr=descr,
        )

    # ---------------- extracteurs spécifiques ----------------

    @staticmethod
    def _job_posting_ld(html: str) -> dict | None:
        for raw in _JSONLD.findall(html):
            try:
                data = json.loads(raw, strict=False)
            except (ValueError, TypeError):
                continue
            for d in (data if isinstance(data, list) else [data]):
                if isinstance(d, dict) and d.get("@type") == "JobPosting":
                    return d
        return None

    @staticmethod
    def _descr(ld: dict | None, html: str) -> str:
        d = (ld or {}).get("description")
        if d:
            return html_to_text(d)[:6000]
        m = _DESCR_DIV.search(html)
        if m:
            return html_to_text(m.group(1))[:6000]
        return html_to_text(html)[:6000]

    @staticmethod
    def _tjm(descr: str) -> tuple[int | None, int | None]:
        m = _TJM_RANGE.search(descr)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            return min(a, b), max(a, b)
        m = _TJM_CEIL.search(descr)
        if m:
            return None, int(m.group(1))
        return None, None

    @staticmethod
    def _duration(html: str, descr: str) -> tuple[int | None, str | None]:
        m = _DUREE.search(html)
        if m:
            dv, dp = parse_duration(m.group(1))
            if dv is not None:
                return dv, dp
        return parse_duration(descr)

    @staticmethod
    def _location(ld: dict | None, html: str) -> str | None:
        addr = ((ld or {}).get("jobLocation") or {}).get("address") if ld else None
        if isinstance(addr, dict):
            locality = (addr.get("addressLocality") or "").strip()
            postal = (addr.get("postalCode") or "").strip()
            if locality:
                return f"{postal} {locality.title()}".strip()
        m = _LOC_LI.search(html)
        return html_to_text(m.group(1)).strip()[:60] if m else None

    @staticmethod
    def _remote_pct(text: str) -> str | None:
        m = re.search(r"(?i)(\d{2,3})\s*%\s*de\s*t[ée]l[ée]travail", text)
        if m:
            pct = int(m.group(1))
            return "full" if pct >= 90 else "partial"
        if re.search(r"(?i)\d\s*(?:à\s*\d\s*)?jours?\s*de\s*(?:home\s*office|t[ée]l[ée]travail)", text):
            return "partial"
        return None
