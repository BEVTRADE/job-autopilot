"""
Agent de soumission Free-Work — Playwright, exécution locale.

Pourquoi Playwright et pas un navigateur piloté à distance : les clics émis
par le protocole de débogage de Chrome sont des événements de confiance
(`isTrusted`). Les clics synthétisés depuis un volet distant ne le sont pas,
et l'application les ignore silencieusement — vérifié le 4 septembre 2026 :
trois candidatures cliquées, zéro enregistrée.

Séquence, conforme à la spécification du formulaire :
  état du compte → CV partagé → questions filtrantes → message → RELECTURE
  → capture → envoi → vérification dans « Mes candidatures » → CV de repos
"""
from __future__ import annotations
import os, re

from .base import Result, guard, humanize, out_dir, journal, PROFILE
from .answers import repondre

BASE = "https://www.free-work.com"
CANDIDATURES = f"{BASE}/fr/tech-it/dashboard/applications"

SEL = {
    "message": "#job-application-message",
    "submit": "button[type=submit]:has-text('Je postule')",
    "editer_cv": "button:has-text('Éditer')",
    "partager_cv": "button:has-text('Partager le CV')",
    "carte_cv": "figure",
}


class FreeWorkApplier:
    """Pilote une session Free-Work déjà authentifiée."""

    def __init__(self, page, cv_repos: str, dry_run: bool = True,
                 limite_reponse: int = 1200):
        self.page = page
        self.cv_repos = cv_repos
        self.dry_run = dry_run
        self.limite = limite_reponse

    # ------------------------------------------------------------------ #

    def cv_partage(self) -> str | None:
        """Nom du CV actuellement partagé, lu dans le panneau de candidature."""
        for a in self.page.locator("a[href*='/users/documents/']").all():
            t = (a.inner_text() or "").strip()
            if t.lower().endswith((".pdf", ".docx")):
                return t
        return None

    def choisir_cv(self, nom: str) -> bool:
        """Bascule le CV partagé. Relit l'état et ne renvoie True qu'après concordance."""
        if self.cv_partage() == nom:
            return True
        guard()
        btns = self.page.locator(SEL["editer_cv"])
        for i in range(btns.count()):
            btns.nth(i).click()
            humanize()
            carte = self.page.locator(SEL["carte_cv"], has_text=nom)
            if carte.count():
                carte.first.click()
                humanize()
                part = self.page.locator(SEL["partager_cv"])
                if part.count():
                    part.first.click()
                    self.page.wait_for_timeout(2500)
                    return self.cv_partage() == nom          # relecture obligatoire
            self.page.keyboard.press("Escape")
            humanize(0.3, 0.7)
        return False

    def questions(self) -> list[dict]:
        """
        Questions filtrantes : tout champ de saisie du formulaire de candidature
        autre que le message. Retourne l'intitulé et le sélecteur.
        """
        out = []
        champs = self.page.locator(
            "form textarea:not(#job-application-message), form input[type=text]")
        for i in range(champs.count()):
            el = champs.nth(i)
            if not el.is_visible():
                continue
            label = ""
            for js in ("el => el.labels && el.labels[0] ? el.labels[0].innerText : ''",
                       "el => el.getAttribute('aria-label') || ''",
                       "el => { const p = el.closest('div'); return p ? p.innerText : ''; }"):
                label = (el.evaluate(js) or "").strip()
                if len(label) > 12:
                    break
            out.append({"index": i, "intitule": re.sub(r"\s+", " ", label)[:400],
                        "obligatoire": bool(el.evaluate("el => el.required")) or "*" in label})
        return out

    # ------------------------------------------------------------------ #

    def postuler(self, url: str, uid: str, titre: str, cv: str,
                 message: str | None = None) -> Result:
        guard()
        self.page.goto(url, wait_until="domcontentloaded")
        humanize(1.2, 2.4)

        if self.page.locator(SEL["submit"]).count() == 0:
            return self._fin(Result(uid, url, titre, "deja_postule",
                                    "bouton d'envoi absent — probablement déjà candidat"))

        if not self.choisir_cv(cv):
            return self._fin(Result(uid, url, titre, "bloquee",
                                    f"CV partagé non basculé sur {cv}", cv=cv))

        # questions filtrantes
        qs = self.questions()
        repondues = []
        for q in qs:
            texte, score, cle = repondre(q["intitule"], self.limite)
            if texte is None:
                return self._fin(Result(
                    uid, url, titre, "bloquee",
                    f"question sans réponse en banque (score {score:.2f}) : "
                    f"{q['intitule'][:120]}", cv=cv, questions=qs))
            champ = self.page.locator(
                "form textarea:not(#job-application-message), form input[type=text]"
            ).nth(q["index"])
            champ.click()
            champ.fill("")
            champ.type(texte, delay=12)          # frappe réelle
            humanize(0.4, 1.0)
            repondues.append({"intitule": q["intitule"], "cle": cle,
                              "score": round(score, 2), "longueur": len(texte)})

        if message:
            m = self.page.locator(SEL["message"])
            if m.count():
                m.first.click()
                m.first.fill("")
                m.first.type(message, delay=6)
                humanize()

        # relecture bloquante (ADR-007)
        ecarts = self._relire(cv, repondues, message)
        if ecarts:
            return self._fin(Result(uid, url, titre, "bloquee",
                                    "relecture discordante : " + " ; ".join(ecarts),
                                    cv=cv, questions=repondues))

        capture = os.path.join(out_dir(), f"{uid}.png")
        self.page.screenshot(path=capture, full_page=False)

        if self.dry_run:
            return self._fin(Result(uid, url, titre, "simulee",
                                    "dry_run actif — envoi non déclenché",
                                    cv=cv, questions=repondues, capture=capture))

        guard()
        self.page.locator(SEL["submit"]).first.click()
        self.page.wait_for_timeout(3500)

        ok = self.verifier(titre)
        return self._fin(Result(
            uid, url, titre, "envoyee" if ok else "echec",
            "confirmée dans Mes candidatures" if ok else
            "absente de Mes candidatures après envoi",
            cv=cv, questions=repondues, capture=capture))

    # ------------------------------------------------------------------ #

    def _relire(self, cv: str, repondues: list[dict], message: str | None) -> list[str]:
        ecarts = []
        if self.cv_partage() != cv:
            ecarts.append(f"CV partagé = {self.cv_partage()}, attendu {cv}")
        champs = self.page.locator(
            "form textarea:not(#job-application-message), form input[type=text]")
        for i, r in enumerate(repondues):
            v = (champs.nth(i).input_value() or "").strip()
            if len(v) < 30:
                ecarts.append(f"réponse {i + 1} vide ou tronquée ({len(v)} car.)")
        if message:
            m = self.page.locator(SEL["message"])
            if m.count() and len((m.first.input_value() or "").strip()) < 30:
                ecarts.append("message non saisi")
        return ecarts

    def verifier(self, titre: str) -> bool:
        """Seule confirmation fiable : la liste des candidatures."""
        try:
            self.page.goto(CANDIDATURES, wait_until="domcontentloaded")
            self.page.wait_for_timeout(2500)
            corps = self.page.locator("body").inner_text()
            cle = " ".join(titre.split()[:5]).lower()
            return cle in corps.lower()
        except Exception:                                    # noqa: BLE001
            return False

    def restaurer_repos(self) -> bool:
        """ADR-009 : la vitrine ne doit pas rester sur le dernier axe utilisé."""
        return self.cv_partage() == self.cv_repos or self.choisir_cv(self.cv_repos)

    @staticmethod
    def _fin(res: Result) -> Result:
        journal(res)
        return res
