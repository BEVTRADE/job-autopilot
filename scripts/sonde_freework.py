#!/usr/bin/env python3
"""
Sonde du parcours de candidature Free-Work — EPIC-8.

Parcourt le formulaire de candidature étape par étape sur une offre réelle,
avec la session persistante déjà connectée, et enregistre à chaque étape le
HTML et une capture pleine page dans tests/pages/freework/<n>-<étape>.html
et .png. La numérotation est fixe : l'étape 4 est toujours la modale des CV,
même si l'étape 3 n'a pas pu être atteinte.

Ne clique JAMAIS sur « Je postule ». Deux garanties dans le code :
  1. aucune référence à SEL["submit"] ;
  2. tout clic passe par `cliquer()`, qui refuse tout élément dont le texte
     contient « postul » (« Postuler », « Je postule »).

Écritures sur le compte, limitées à ce que le parcours demande :
  - dépôt du CV local, seulement s'il n'est pas déjà dans la liste ;
  - bascule du CV partagé sur ce CV, puis restauration du CV de repos
    (ADR-009) en fin de sonde, même en cas d'échec en cours de route.

    .venv/bin/python scripts/sonde_freework.py
    .venv/bin/python scripts/sonde_freework.py --cv-fichier chemin/vers/cv.pdf
"""
from __future__ import annotations
import argparse, glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from src.apply.base import PROFILE, humanize            # noqa: E402
from src.apply.freework import SEL, BASE, meme_cv       # noqa: E402
from apply import CV_REPOS                              # noqa: E402

OFFRE = (f"{BASE}/fr/tech-it/job-mission/"
         "architecte-de-base-de-donnees/architecte-de-domaine-simulation")
CANDIDATURES = f"{BASE}/fr/applications"
OUT = os.path.join(ROOT, "tests", "pages", "freework")

CV_DEFAUT = os.path.join(
    ROOT, "clients", "simulation-atos", "03_cv",
    "CV_Hakim_Arezki_Architecte_Domaine_Simulation.pdf")

# Numérotation fixe : les tests s'appuient sur ces noms.
ETAPES = {
    1: "page-offre",
    2: "panneau-candidature",
    3: "modale-profil",
    4: "modale-cv-ouverture",
    5: "apres-clic-ajouter-cv",
    6: "apres-choix-fichier",
    7: "apres-depot",
    8: "apres-selection-carte",
    9: "apres-confirmation",
    10: "questions-filtrantes",
    11: "mes-candidatures",
}

INTERDIT = re.compile(r"postul", re.I)
manquantes: list[int] = []


EMAIL = re.compile(r"[\w.%+-]+@[\w-]+(?:\.[\w-]+)*\.[a-z]{2,}", re.I)


def enregistrer(page, n: int) -> None:
    base = os.path.join(OUT, f"{n:02d}-{ETAPES[n]}")
    # Les instantanés sont versionnés : aucune adresse e-mail n'y reste.
    html = EMAIL.sub("anonyme@example.invalid", page.content())
    open(base + ".html", "w", encoding="utf-8").write(html)
    page.screenshot(path=base + ".png", full_page=True)
    print(f"  [{n:02d}] {ETAPES[n]}")


def cliquer(loc) -> None:
    """Seul point de clic de la sonde. Refuse tout ce qui ressemble à un envoi."""
    el = loc.first
    texte = (el.inner_text() or "") + " " + (el.get_attribute("aria-label") or "")
    if INTERDIT.search(texte):
        raise RuntimeError(f"clic refusé, libellé d'envoi : {texte.strip()!r}")
    el.click()


def manque(n: int, pourquoi: str) -> None:
    manquantes.append(n)
    print(f"  [{n:02d}] {ETAPES[n]} — NON ATTEINTE : {pourquoi}")


def cartes(page) -> list[tuple[str, object]]:
    out = []
    loc = page.locator("[data-testid^='file-item-']")
    for k in range(loc.count()):
        c = loc.nth(k)
        out.append(((c.locator("figcaption").first.inner_text()
                     if c.locator("figcaption").count() else c.inner_text()).strip(), c))
    return out


def cv_partage(page) -> str:
    a = page.locator("#default-resume-attachment")
    return (a.first.inner_text() or "").strip() if a.count() else ""


def ouvrir_modale_cv(page) -> bool:
    if not page.locator("#default-resume-edit").count():
        return False
    cliquer(page.locator("#default-resume-edit"))
    humanize()
    return page.locator("[data-testid='file-chooser-modal']").count() > 0


def partager(page, nom: str) -> bool:
    """Sélectionne la carte `nom` dans la modale ouverte et confirme."""
    carte = next((c for n, c in cartes(page) if meme_cv(n, nom)), None)
    if carte is None:
        return False
    cliquer(carte)
    humanize()
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cv-fichier", default=CV_DEFAUT,
                    help="fichier local à déposer puis sélectionner")
    ap.add_argument("--headless", action="store_true")
    args = ap.parse_args()
    nom_cv = os.path.basename(args.cv_fichier)

    if not os.path.isfile(args.cv_fichier):
        sys.exit(f"fichier à déposer introuvable : {args.cv_fichier}")

    os.makedirs(OUT, exist_ok=True)
    for f in glob.glob(os.path.join(OUT, "[0-9][0-9]-*")):
        os.remove(f)                     # pas d'instantané périmé mêlé aux neufs

    from playwright.sync_api import sync_playwright
    os.makedirs(PROFILE, exist_ok=True)
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            PROFILE, headless=args.headless, slow_mo=120,
            viewport={"width": 1440, "height": 950},
            locale="fr-FR", timezone_id="Europe/Paris",
            args=["--disable-blink-features=AutomationControlled"])
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        a_restaurer = False

        try:
            # 1. page d'offre
            page.goto(OFFRE, wait_until="domcontentloaded")
            humanize(1.2, 2.0)
            if not page.locator("[data-testid='user-menu']").count():
                sys.exit("session Free-Work absente : relancer make login")
            enregistrer(page, 1)
            print(f"  CV partagé au départ : {cv_partage(page)!r}")

            # 2. panneau de candidature : la section est déjà dans la page, on
            #    la fait défiler, sans cliquer sur aucun « Postuler ».
            page.locator("#job-application-message").scroll_into_view_if_needed()
            humanize(0.5, 1.0)
            enregistrer(page, 2)

            # 3. modale Profil : « Éditer » qui n'est pas celui du CV
            profil = page.locator("form button:has-text('Éditer'):not(#default-resume-edit)")
            print(f"  boutons « Éditer » du profil : {profil.count()}")
            if profil.count():
                cliquer(profil)
                humanize()
                enregistrer(page, 3)
                page.keyboard.press("Escape")       # jamais « Mettre à jour »
                humanize(0.3, 0.7)
            else:
                manque(3, "bouton Éditer du profil introuvable")

            # 4. modale des CV à l'ouverture
            if ouvrir_modale_cv(page):
                enregistrer(page, 4)
            else:
                manque(4, "modale des CV non ouverte")
                raise SystemExit(1)

            deja_la = any(meme_cv(n, nom_cv) for n, _ in cartes(page))
            print(f"  {nom_cv} déjà présent sur Free-Work : {deja_la}")

            # 5. clic sur « Ajouter un CV »
            ajouter = page.locator(SEL["ajouter_cv"])
            if ajouter.count():
                cliquer(ajouter)
                humanize()
                enregistrer(page, 5)
            else:
                manque(5, "bouton Ajouter un CV introuvable")

            # 6. choix du fichier par « Parcourir… ». « Ajouter un CV » est un
            #    accordéon, ouvert à l'ouverture de la modale : le clic de
            #    l'étape 5 l'a refermé, on le rouvre s'il le faut.
            parcourir = page.locator("[data-testid='file-upload-input'] button")
            try:
                if not (parcourir.count() and parcourir.first.is_visible()):
                    cliquer(page.locator(SEL["ajouter_cv"]))
                    humanize()
                with page.expect_file_chooser(timeout=5000) as fc:
                    cliquer(parcourir)
                fc.value.set_files(args.cv_fichier)
                page.wait_for_timeout(1500)
                enregistrer(page, 6)
            except Exception as e:                              # noqa: BLE001
                manque(6, f"choix du fichier impossible : {e}")

            # 7. dépôt effectif, seulement si le fichier n'est pas déjà chez eux
            envoyer = page.get_by_role("button", name=re.compile(r"envoyer mon cv", re.I))
            if deja_la:
                print("  dépôt ignoré : le fichier est déjà dans la liste")
                enregistrer(page, 7)
            elif envoyer.count() and envoyer.first.is_enabled():
                a_restaurer = True
                cliquer(envoyer)
                page.wait_for_timeout(4000)
                enregistrer(page, 7)
            else:
                manque(7, "« Envoyer mon CV » absent ou inactif")

            # 8. sélection de la carte du CV déposé (pas la première venue)
            if partager(page, nom_cv):
                a_restaurer = True
                enregistrer(page, 8)
                # 9. confirmation
                confirmer = page.get_by_role("button", name=re.compile(r"partager le cv", re.I))
                if confirmer.count() and confirmer.first.is_enabled():
                    cliquer(confirmer)
                    page.wait_for_timeout(2500)
                    enregistrer(page, 9)
                    print(f"  CV partagé après confirmation : {cv_partage(page)!r}")
                else:
                    manque(9, "« Partager le CV » absent ou inactif")
            else:
                manque(8, f"carte {nom_cv} absente de la liste")
                manque(9, "pas de sélection, pas de confirmation")

            # 10. questions filtrantes : cette offre n'en a pas forcément
            page.keyboard.press("Escape")
            humanize(0.3, 0.7)
            print("  champs de saisie hors message : "
                  f"{page.locator('form textarea:not(#job-application-message), form input[type=text]').count()}")
            enregistrer(page, 10)

            # 11. « Mes candidatures »
            page.goto(CANDIDATURES, wait_until="domcontentloaded")
            humanize(1.0, 1.8)
            enregistrer(page, 11)

        finally:
            # ADR-009 : la vitrine ne doit pas rester sur le CV de la sonde,
            # quoi qu'il se soit passé.
            try:
                page.goto(OFFRE, wait_until="domcontentloaded")
                humanize(1.0, 1.6)
                if not meme_cv(cv_partage(page), CV_REPOS):
                    print(f"  restauration du CV de repos : {CV_REPOS}")
                    if ouvrir_modale_cv(page) and partager(page, CV_REPOS):
                        cliquer(page.get_by_role("button", name=re.compile(r"partager le cv", re.I)))
                        page.wait_for_timeout(2500)
                    page.goto(OFFRE, wait_until="domcontentloaded")
                    humanize(1.0, 1.6)
                ok = meme_cv(cv_partage(page), CV_REPOS)
                print(f"  CV partagé en fin de sonde : {cv_partage(page)!r} "
                      f"({'restauré' if ok else 'À REMETTRE À LA MAIN'})")
            except Exception as e:                              # noqa: BLE001
                print(f"  restauration impossible : {e} — à remettre à la main")
            ctx.close()

    reussies = len(ETAPES) - len(set(manquantes))
    print(f"\n{reussies}/{len(ETAPES)} instantané(s) écrits dans {OUT}")
    if manquantes:
        print("étapes non atteintes :", ", ".join(str(n) for n in sorted(set(manquantes))))
        sys.exit(1)


if __name__ == "__main__":
    main()
