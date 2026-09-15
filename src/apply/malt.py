"""
Malt — connecteur en lecture et réponse, pas en candidature.

Malt n'expose aucune liste de missions à parcourir : le modèle est entrant,
les clients proposent et le freelance répond sous 48 heures. Il n'y a donc
rien à « découvrir » ni à « soumettre ». Ce que l'automatisation peut faire
utilement, c'est ne pas laisser une proposition expirer.

Capacités déclarées : lire, repondre.
"""
from __future__ import annotations
import re

from .base import Result, guard, humanize, journal

CAPACITES = {"lire", "repondre"}
OPPORTUNITES = "https://www.malt.fr/dashboard/freelancer/opportunities"


class Malt:
    name = "malt"

    def __init__(self, page, dry_run: bool = True):
        self.page = page
        self.dry_run = dry_run

    def propositions(self) -> list[dict]:
        """Les propositions reçues, avec leur échéance de réponse."""
        guard()
        self.page.goto(OPPORTUNITES, wait_until="domcontentloaded")
        self.page.wait_for_timeout(3000)
        out = []
        for c in self.page.locator("[data-testid*='opportunity'], article, li").all():
            try:
                t = (c.inner_text() or "").strip()
            except Exception:                                # noqa: BLE001
                continue
            if len(t) < 40 or "€" not in t and "jour" not in t.lower():
                continue
            lien = c.locator("a").first
            url = lien.get_attribute("href") if lien.count() else None
            reste = re.search(r"(\d+)\s*(h|heure|jour)", t, re.I)
            out.append({
                "titre": t.split("\n")[0][:120],
                "extrait": re.sub(r"\s+", " ", t)[:600],
                "url": url,
                "echeance": reste.group(0) if reste else None,
            })
        return out[:30]

    def repondre(self, url: str, texte: str, uid: str, titre: str) -> Result:
        """Répond à une proposition. Jamais sans validation préalable."""
        guard()
        if self.dry_run:
            return journal(Result(uid, url, titre, "simulee",
                                  "dry_run — réponse Malt non envoyée")) or Result(
                uid, url, titre, "simulee", "dry_run — réponse Malt non envoyée")
        self.page.goto(url, wait_until="domcontentloaded")
        humanize(1.5, 3.0)
        champ = self.page.locator("textarea").first
        if champ.count() == 0:
            return journal(Result(uid, url, titre, "bloquee",
                                  "zone de réponse introuvable"))
        champ.click(); champ.fill(""); champ.type(texte, delay=14)
        humanize()
        if len((champ.input_value() or "").strip()) < 30:
            return journal(Result(uid, url, titre, "bloquee", "saisie non prise en compte"))
        return journal(Result(uid, url, titre, "bloquee",
                              "envoi Malt volontairement non automatisé : "
                              "réponse pré-remplie, validation manuelle requise"))
