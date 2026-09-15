"""
LinkedIn — découverte et lecture. La soumission reste désactivée par défaut.

Motif, à lire avant d'activer quoi que ce soit : l'automatisation des
candidatures est contraire aux conditions d'utilisation de LinkedIn, et la
détection y est active. Le risque n'est pas un échec technique mais la
restriction du compte — c'est-à-dire la perte du canal qui, sur ce profil,
porte les missions les mieux payées.

Capacités déclarées : decouvrir, lire.
`soumettre` n'est ajoutée que si `autoriser_soumission=True` est passé
explicitement, et reste plafonnée à trois candidatures par jour.
"""
from __future__ import annotations
import re

from .base import Result, guard, humanize, journal

RECHERCHE = ("https://www.linkedin.com/jobs/search/"
             "?keywords={q}&location=%C3%8Ele-de-France&f_TPR=r86400&f_AL=true")
PLAFOND_JOUR = 3


class LinkedIn:
    name = "linkedin"

    def __init__(self, page, dry_run: bool = True,
                 autoriser_soumission: bool = False):
        self.page = page
        self.dry_run = dry_run
        self.capacites = {"decouvrir", "lire"}
        if autoriser_soumission:
            self.capacites.add("soumettre")

    def decouvrir(self, mots_cles: list[str], limite: int = 40) -> list[str]:
        urls, vus = [], set()
        for q in mots_cles:
            guard()
            self.page.goto(RECHERCHE.format(q=q.replace(" ", "%20")),
                           wait_until="domcontentloaded")
            self.page.wait_for_timeout(3500)
            for a in self.page.locator("a[href*='/jobs/view/']").all():
                h = (a.get_attribute("href") or "").split("?")[0]
                if h and h not in vus:
                    vus.add(h)
                    urls.append(h if h.startswith("http")
                                else "https://www.linkedin.com" + h)
                    if len(urls) >= limite:
                        return urls
            humanize(2.5, 5.0)          # cadence prudente
        return urls

    def lire(self, url: str) -> dict | None:
        guard()
        self.page.goto(url, wait_until="domcontentloaded")
        self.page.wait_for_timeout(2500)
        try:
            titre = self.page.locator("h1").first.inner_text().strip()
            corps = self.page.locator("body").inner_text()
        except Exception:                                    # noqa: BLE001
            return None
        soc = re.search(r"(?m)^([A-Z][^\n]{2,60})\n", corps)
        return {"url": url, "title": titre,
                "company": soc.group(1).strip() if soc else None,
                "descr": re.sub(r"\s+", " ", corps)[:6000],
                "easy_apply": self.page.locator(
                    "button:has-text('Candidature simplifiée'), "
                    "button:has-text('Easy Apply')").count() > 0}

    def postuler(self, url: str, uid: str, titre: str, envoyes_aujourdhui: int) -> Result:
        if "soumettre" not in self.capacites:
            return journal(Result(uid, url, titre, "bloquee",
                                  "soumission LinkedIn désactivée — activation explicite requise"))
        if envoyes_aujourdhui >= PLAFOND_JOUR:
            return journal(Result(uid, url, titre, "bloquee",
                                  f"plafond quotidien atteint ({PLAFOND_JOUR})"))
        if self.dry_run:
            return journal(Result(uid, url, titre, "simulee", "dry_run actif"))
        return journal(Result(uid, url, titre, "bloquee",
                              "chemin de soumission non implémenté volontairement — "
                              "voir la note en tête de module"))
