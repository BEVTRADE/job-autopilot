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
# 04-modale-cv-ouverture, 11-mes-candidatures : l'ancienne URL,
# /fr/tech-it/dashboard/applications, renvoyait un 404.
CANDIDATURES = f"{BASE}/fr/applications"

_M = "[data-testid='file-chooser-modal']"

# Relevés sur le DOM réel le 19/09/2026 par scripts/sonde_freework.py ; chaque
# entrée est testée contre l'instantané de son étape (tests/test_freework_dom.py)
# et inventoriée dans docs/inventaire-selecteurs-freework.md.
SEL = {
    # 02-panneau-candidature
    "message": "#job-application-message",
    # Ancré sur le formulaire : le bouton n'a ni id ni data-testid.
    "submit": "form:has(#job-application-message) button[type=submit]",
    # 02 : deux boutons « Éditer » (Profil, CV) ; seul celui du CV a un id.
    "editer_cv": "#default-resume-edit",
    "cv_partage_lien": "#default-resume-attachment",
    "session": "[data-testid='user-menu']",
    # 04 à 08 : modale des CV. Deux <form> y coexistent, la liste (« Partager
    # le CV ») et le dépôt (« Envoyer mon CV ») : l'ancien `form button[type=submit]`
    # renvoyait les deux, et « Mettre à jour » dans la modale Profil (03).
    "modale_cv": _M,
    "carte_fichier": f"{_M} [data-testid='file-list'] > [data-testid^='file-item-']",
    "nom_fichier": "figcaption",
    "partager_cv": f"{_M} form:has([data-testid='file-list']) button[type=submit]",
    # « Ajouter un CV » est un accordéon OUVERT à l'ouverture de la modale (04) ;
    # cliquer dessus le referme (05). N'y cliquer que si « Parcourir… » est absent.
    "ajouter_cv": "[data-testid='add-resume-button']",
    # Seul sélecteur à libellé : « Parcourir… » et « Changer » (06) partagent le
    # même conteneur, sans attribut propre.
    "parcourir": f"{_M} [data-testid='file-upload-input'] button:has-text('Parcourir')",
    "envoyer_cv": f"{_M} form:has([data-testid='file-upload-input']) button[type=submit]",
}


def _norm_nom(t: str) -> str:
    """Nom de fichier comparable : minuscules, sans extension ni ellipse."""
    t = (t or "").strip().lower()
    t = t.replace("\u2026", "").replace("...", "").strip()
    return re.sub(r"\.(pdf|docx?)$", "", t)


def meme_cv(affiche: str | None, attendu: str) -> bool:
    """Le nom affiché par Free-Work désigne-t-il le CV attendu ?

    Free-Work tronque les noms longs à l'affichage (constaté le 19/09 : le
    basculement vers un CV de 52 caractères échouait sans message clair). On
    accepte l'égalité exacte, ou un affichage qui est un préfixe d'au moins
    vingt caractères du nom attendu. Jamais l'inverse : un nom attendu court
    ne doit pas correspondre à un fichier plus long qui le contiendrait.
    """
    a, b = _norm_nom(affiche or ""), _norm_nom(attendu)
    if not a or not b:
        return False
    if a == b:
        return True
    return len(a) >= 20 and b.startswith(a)


EXTENSIONS_CV = (".pdf", ".docx", ".doc")
TAILLE_MAX_CV = 10 * 1024 * 1024        # prudence : limite Free-Work non documentée


def verifier_fichier_cv(chemin: str | None) -> tuple[bool, str]:
    """Le fichier local peut-il être déposé ? Renvoie (ok, raison)."""
    if not chemin:
        return False, "aucun fichier fourni"
    if not os.path.isfile(chemin):
        return False, f"fichier introuvable : {chemin}"
    if not chemin.lower().endswith(EXTENSIONS_CV):
        return False, f"format refusé, attendu {', '.join(EXTENSIONS_CV)} : {chemin}"
    taille = os.path.getsize(chemin)
    if taille == 0:
        return False, f"fichier vide : {chemin}"
    if taille > TAILLE_MAX_CV:
        return False, f"fichier trop lourd, {taille // 1024} Ko : {chemin}"
    return True, "ok"


class FreeWorkApplier:
    """Pilote une session Free-Work déjà authentifiée."""

    def __init__(self, page, cv_repos: str, dry_run: bool = True,
                 limite_reponse: int = 1200):
        self.page = page
        self.cv_repos = cv_repos
        self.dry_run = dry_run
        self.limite = limite_reponse

    # ------------------------------------------------------------------ #

    def session_active(self) -> bool:
        """La session Free-Work est-elle ouverte ?

        Marqueur : le menu utilisateur de l'en-tête n'existe que connecté
        (instantanés 01 à 11, tous connectés).
        """
        try:
            self.page.goto(f"{BASE}/fr/tech-it", wait_until="domcontentloaded")
            self.page.wait_for_timeout(2000)
            return self.page.locator(SEL["session"]).count() > 0
        except Exception:                                    # noqa: BLE001
            return False

    def cv_partage(self) -> str | None:
        """Nom du CV actuellement partagé, lu dans le panneau de candidature."""
        lien = self.page.locator(SEL["cv_partage_lien"])
        if not lien.count():
            return None
        return (lien.first.inner_text() or "").strip() or None

    def _cartes(self) -> list[tuple[str, object]]:
        """(nom affiché, élément cliquable) pour chaque CV de la modale."""
        out = []
        cartes = self.page.locator(SEL["carte_fichier"])
        for k in range(cartes.count()):
            c = cartes.nth(k)
            out.append(((c.locator(SEL["nom_fichier"]).first.inner_text() or "").strip(), c))
        return out

    def _modale_cv_ouverte(self) -> bool:
        return self.page.locator(SEL["modale_cv"]).count() > 0

    def _ouvrir_modale_cv(self) -> bool:
        """Ouvre la modale des CV par son bouton « Éditer » (celui du CV partagé,
        pas celui du Profil : `#default-resume-edit` est unique, 02)."""
        if not self._modale_cv_ouverte():
            bouton = self.page.locator(SEL["editer_cv"])
            if not bouton.count():
                return False
            bouton.first.click()
            humanize()
        return self._modale_cv_ouverte()

    def _cliquer_actif(self, cle: str, attente_ms: int = 3000) -> bool:
        """Clique le bouton `cle` une fois actif : « Partager le CV » et « Envoyer
        mon CV » sont désactivés à l'ouverture (04) et s'activent après le choix
        d'une carte (08) ou d'un fichier (06)."""
        b = self.page.locator(SEL[cle])
        if not b.count():
            return False
        for _ in range(attente_ms // 250):
            if b.first.is_enabled():
                b.first.click()
                return True
            self.page.wait_for_timeout(250)
        return False

    def _valider_selection(self) -> bool:
        """Confirme le CV choisi par « Partager le CV » (08). Le libellé
        « Joindre le document » n'existe dans aucun instantané."""
        if self._cliquer_actif("partager_cv"):
            self.page.wait_for_timeout(2500)         # la modale se ferme (09)
            return True
        return False

    def choisir_cv(self, nom: str, chemin: str | None = None) -> bool:
        """Bascule le CV partagé. Relit l'état et ne renvoie True qu'après concordance.

        Si le CV n'est pas encore sur Free-Work et qu'un `chemin` local est
        fourni, il est déposé depuis le poste puis sélectionné. Fournir le
        chemin vaut consentement au dépôt : c'est une écriture sur le compte,
        faite même en dry-run, puisque le dry-run ne porte que sur l'envoi
        de la candidature.
        """
        self.cv_vus: list[str] = []
        self.depot_tente = False
        if meme_cv(self.cv_partage(), nom):
            return True
        guard()
        # `#default-resume-edit` désigne sans ambiguïté le bouton du CV partagé,
        # pas celui du Profil (02) : plus de boucle sur les boutons « Éditer ».
        if not self._ouvrir_modale_cv():
            self.depot_detail = "modale des CV non ouverte"
            return False
        cartes = self._cartes()
        self.cv_vus = [n for n, _ in cartes if n]
        carte = next((c for n, c in cartes if meme_cv(n, nom)), None)
        if carte is None and chemin and not self.depot_tente:
            self.depot_tente = True
            if self.deposer_cv(chemin):
                self._ouvrir_modale_cv()             # au cas où le dépôt l'a refermée
                cartes = self._cartes()
                self.cv_vus = [n for n, _ in cartes if n]
                carte = next((c for n, c in cartes if meme_cv(n, nom)), None)
        if carte is not None:
            carte.click()
            humanize()
            if self._valider_selection():
                return meme_cv(self.cv_partage(), nom)   # relecture obligatoire
        if self._modale_cv_ouverte():
            self.page.keyboard.press("Escape")
            humanize(0.3, 0.7)
        return False

    def deposer_cv(self, chemin: str) -> bool:
        """Dépose un CV local dans la fenêtre d'édition ouverte.

        Parcours observé (instantanés 04, 05, 06) : à l'ouverture de la modale,
        la zone de dépôt est déjà ouverte, avec « Parcourir… ». « Ajouter un CV »
        est un accordéon : cliquer dessus la referme. Le fichier se choisit par
        le sélecteur système ouvert par « Parcourir… » (aucun input[type=file]
        dans le DOM), puis « Envoyer mon CV », inactif jusque-là, le téléverse.

        Le 07, après « Envoyer mon CV », n'a pas encore été observé : le CV de
        simulation était déjà présent lors de la sonde. En cas d'échec, le HTML
        et une capture sont enregistrés pour corriger sur pièce.
        """
        ok, raison = verifier_fichier_cv(chemin)
        if not ok:
            self.depot_detail = raison
            return False
        guard()
        nom = os.path.basename(chemin)
        try:
            if not self._modale_cv_ouverte():
                raise RuntimeError("modale des CV non ouverte")
            parcourir = self.page.locator(SEL["parcourir"])
            if not parcourir.count():                    # accordéon refermé
                ajouter = self.page.locator(SEL["ajouter_cv"])
                if not ajouter.count():
                    raise RuntimeError("bouton « Ajouter un CV » introuvable")
                ajouter.first.click()
                humanize()
                parcourir.first.wait_for(state="visible", timeout=5000)
            with self.page.expect_file_chooser(timeout=5000) as fc:
                parcourir.first.click()
            fc.value.set_files(chemin)
            self.page.wait_for_timeout(1500)
            if not self._cliquer_actif("envoyer_cv"):
                raise RuntimeError("« Envoyer mon CV » absent ou resté inactif après le choix du fichier")
            # téléversement puis rafraîchissement de la liste
            for _ in range(12):
                self.page.wait_for_timeout(1000)
                self._ouvrir_modale_cv()
                if any(meme_cv(n, nom) for n, _ in self._cartes()):
                    self.depot_detail = f"déposé : {nom}"
                    return True
            raise RuntimeError("fichier envoyé mais absent de la liste des CV")
        except Exception as e:                          # noqa: BLE001
            self.depot_detail = f"dépôt échoué : {e}"
            base = os.path.join(out_dir(), "depot-echec")
            try:
                open(base + ".html", "w", encoding="utf-8").write(self.page.content())
                self.page.screenshot(path=base + ".png", full_page=True)
                self.depot_detail += f" — DOM enregistré dans {base}.html"
            except Exception:                           # noqa: BLE001
                pass
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
                       # L'intitulé vit dans un <p> plusieurs niveaux au-dessus du
                       # champ (constaté le 18/09 : div.mb-4.p-3... > p.font-medium
                       # > ... > textarea#custom-answer-N) — closest('div') seul
                       # ne remonte pas assez haut et rendait toujours "".
                       """el => {
                           let node = el;
                           for (let i = 0; i < 6 && node; i++) {
                               node = node.parentElement;
                               if (!node) break;
                               const p = node.querySelector('p');
                               if (p && p.innerText.trim().length > 5) return p.innerText;
                           }
                           return '';
                       }"""):
                label = (el.evaluate(js) or "").strip()
                if len(label) > 12:
                    break
            out.append({"index": i, "intitule": re.sub(r"\s+", " ", label)[:400],
                        "obligatoire": bool(el.evaluate("el => el.required")) or "*" in label})
        return out

    # ------------------------------------------------------------------ #

    def postuler(self, url: str, uid: str, titre: str, cv: str,
                 cv_fichier: str | None = None,
                 message: str | None = None) -> Result:
        guard()
        self.page.goto(url, wait_until="domcontentloaded")
        humanize(1.2, 2.4)

        if self.page.locator(SEL["submit"]).count() == 0:
            return self._fin(Result(uid, url, titre, "deja_postule",
                                    "bouton d'envoi absent — probablement déjà candidat"))

        if not self.choisir_cv(cv, cv_fichier):
            return self._fin(Result(uid, url, titre, "bloquee",
                                    f"CV partagé non basculé sur {cv} — CV présents "
                                    f"sur Free-Work : {', '.join(getattr(self, 'cv_vus', [])) or 'aucun lu'}. "
                                    + (f"Dépôt : {getattr(self, 'depot_detail', '')}."
                                       if cv_fichier else
                                       "Si le fichier n'y figure pas, relancer avec --cv-fichier."),
                                    cv=cv))

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

        # Le formulaire ("Postuler à cette offre") est une section de la page,
        # pas une modale : quand aucun champ n'a dû être touché (CV déjà bon,
        # aucune question, pas de message), la page reste scrollée en haut et
        # la capture ne montrait que l'annonce — constaté le 18/09 sur 3/3
        # candidatures simulées. On recentre explicitement sur le bouton
        # d'envoi avant de capturer.
        self.page.locator(SEL["submit"]).first.scroll_into_view_if_needed()
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
        if not meme_cv(self.cv_partage(), cv):
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
        return meme_cv(self.cv_partage(), self.cv_repos) or self.choisir_cv(self.cv_repos)

    @staticmethod
    def _fin(res: Result) -> Result:
        journal(res)
        return res
