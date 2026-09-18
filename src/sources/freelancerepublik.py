"""
Source FreelanceRepublik.

Découverte via le sitemap XML public (`/sitemap.xml`), qui liste directement
les URL `/missions/<titre-slugifie>-<id-hexadecimal>` sans pagination à
parcourir. Le domaine est `freelancerepublik.com`, sans tiret — le registre
en portait une version erronée, corrigée le 18 septembre 2026
(docs/sources.md). Missions publiques, sans connexion.

Bizarreries propres à cette source :

- `hiringOrganization.name` du bloc JSON-LD JobPosting vaut toujours
  "Freelance Republik" : c'est la plateforme, jamais le client final, sur
  les 48 annonces vérifiées le 18 septembre 2026. La société n'est donc pas
  un champ fiable ici, comme sur Freelance-Informatique.
- Le TJM n'est affiché qu'sur une minorité d'annonces (5 sur 48 vérifiées),
  toujours introduit par "TJM" en prose libre : "TJM : 780 €/jour", "TJM
  cible : 650 à 770 €", "[suggestion : TJM autour de 800 € / jour]", "TJM
  cible : 550-600 €". D'où un extracteur ancré sur le mot "TJM", pas sur le
  générique `parse_tjm` du socle (qui exige un suffixe "€/jour" absent des
  formulations en fourchette).
- **Le texte de description dupliqué en tête de page (`<div id="jp-desc">`,
  et le champ `description` du JSON-LD, qui portent le même texte) est
  tronqué aux alentours de 4100 caractères** — vérifié le 18 septembre 2026
  sur l'annonce "Technical Product Owner" : les deux coupent en plein mot
  ("...organisation produit stru"). Le corps complet, non tronqué, se
  trouve dans le HTML rendu de `<div class="mission-content w-richtext">`
  (4307 caractères sur cette même annonce, qui se termine normalement).
  C'est cette div, et uniquement elle, qui doit être lue.
- La durée n'apparaît qu'en prose ("Mission temporaire de 7 mois", "durée
  12 mois"), jamais en champ structuré. L'ancrage sur les mots "durée" ou
  "mission" évite de capter un nombre sans rapport ailleurs dans le texte
  (ex. "toutes les 2 semaines" au sujet du rythme de télétravail, pas de la
  durée de la mission).
"""
from __future__ import annotations
import re

from .base import (Source, RawMission, fetch, html_to_text, parse_remote)

BASE = "https://www.freelancerepublik.com"
SITEMAP = BASE + "/sitemap.xml"

_LOC = re.compile(r"(?m)^\s*<loc>\s*(.*?)\s*</loc>")
_H1 = re.compile(r"(?is)<h1[^>]*>(.*?)</h1>")
_META_TAGS = re.compile(
    r'(?is)<div class="jobboard-card-meta">((?:<div class="jobboard-tag[^"]*">[^<]*</div>)+)')
_TAG = re.compile(r'(?is)<div class="jobboard-tag[^"]*">([^<]*)</div>')
_CONTENT = re.compile(
    r'(?is)<div class="mission-content w-richtext">(.*?)</div>\s*<a[^>]+data-wf--button')

_TJM_RANGE = re.compile(
    r"(?i)TJM[^\n]{0,40}?(\d{3,4})\s*(?:€|EUR)?\s*(?:à|-|–)\s*(\d{3,4})\s*(?:€|EUR)")
_TJM_SINGLE = re.compile(r"(?i)TJM[^\n]{0,40}?(\d{3,4})\s*(?:€|EUR)")

_DUR_SINGLE = re.compile(
    r"(?i)(?:dur[ée]e|mission)[^\d]{0,30}?(\d{1,3})\s*(mois|ans?|semaines?)")

_REMOTE_TAG = {"hybride": "partial", "télétravail": "full", "teletravail": "full"}


class FreelanceRepublik(Source):
    name = "freelancerepublik"

    def discover(self, cfg: dict) -> list[str]:
        limit = cfg.get("max_urls", 200)
        try:
            xml = fetch(cfg.get("sitemap", SITEMAP), timeout=30)
        except Exception:                                        # noqa: BLE001
            return []
        return [u for u in _LOC.findall(xml) if "/missions/" in u][:limit]

    def parse(self, url: str) -> RawMission | None:
        try:
            html = fetch(url)
        except Exception:                                        # noqa: BLE001
            return None

        m = _H1.search(html)
        title = html_to_text(m.group(1)).strip() if m else url

        remote_tag, loc_tag = "", ""
        m = _META_TAGS.search(html)
        if m:
            tags = _TAG.findall(m.group(1))
            if len(tags) >= 2:
                remote_tag, loc_tag = tags[0].strip(), tags[1].strip()

        descr = self._descr(html)
        tjm_min, tjm_max = self._tjm(descr)
        dv, dp = self._duration(descr)
        loc = html_to_text(loc_tag).strip()[:60]

        return RawMission(
            source=self.name,
            url=url,
            title=title,
            company=None,
            tjm_min=tjm_min, tjm_max=tjm_max,
            remote=_REMOTE_TAG.get(remote_tag.lower()) or parse_remote(descr),
            loc=loc or None,
            dur_val=dv, dur_per=dp,
            descr=descr,
        )

    # ---------------- extracteurs spécifiques ----------------

    @staticmethod
    def _descr(html: str) -> str:
        """Corps complet de l'annonce : `mission-content`, jamais
        `jp-desc` ni le `description` du JSON-LD, tronqués vers 4100
        caractères (voir docstring du module)."""
        m = _CONTENT.search(html)
        if m:
            return html_to_text(m.group(1))[:6000]
        return html_to_text(html)[:6000]

    @staticmethod
    def _tjm(descr: str) -> tuple[int | None, int | None]:
        m = _TJM_RANGE.search(descr)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            return min(a, b), max(a, b)
        m = _TJM_SINGLE.search(descr)
        if m:
            v = int(m.group(1))
            return v, v
        return None, None

    @staticmethod
    def _duration(descr: str) -> tuple[int | None, str | None]:
        m = _DUR_SINGLE.search(descr)
        if not m:
            return None, None
        n, unit = int(m.group(1)), m.group(2).lower()
        if unit.startswith("mois"):
            return n, "month"
        if unit.startswith("an"):
            return n, "year"
        return n, "week"
