#!/usr/bin/env python3
"""
Soumission des candidatures — à lancer depuis macOS, pas depuis un volet distant.

    python3 scripts/apply.py --login              # une fois, connexion manuelle
    python3 scripts/apply.py --from data/live/contact_scored.json --max 5
    python3 scripts/apply.py --from ... --max 5 --envoyer    # lève le dry-run

Sans --envoyer, rien ne part : le pipeline va jusqu'à la capture d'écran et
s'arrête avant le clic. C'est le mode par défaut.
"""
from __future__ import annotations
import argparse, json, os, random, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.apply.base import PROFILE, STOP, KillSwitch, guard, out_dir   # noqa: E402
from src.apply.freework import FreeWorkApplier                          # noqa: E402

CV_REPOS = "FR_ARCHITECTE_ENTREPRISE_URBANISTE.pdf"


CV_PRETS = os.path.join(ROOT, "cv_prets", "pdf")


def cv_pour_mission(match: dict, cv_force: str | None = None,
                    fichier_force: str | None = None) -> tuple[str, str | None]:
    """(nom du CV sur Free-Work, chemin local à déposer si absent).

    Le moteur choisit l'axe et la langue de chaque mission et renvoie le CV
    correspondant dans `cv_path`. Jusqu'au 19/09, ce choix était ignoré :
    toutes les missions partaient avec le même CV, celui passé en option.
    Un CV forcé en ligne de commande reste prioritaire, pour les
    candidatures manuelles avec un CV dédié.
    """
    if fichier_force:
        return (cv_force or os.path.basename(fichier_force)), fichier_force
    if cv_force:
        return cv_force, None
    source = match.get("cv_path") or ""
    nom = os.path.splitext(os.path.basename(source))[0] + ".pdf" if source \
        else "FR_ARCHITECTE_IA_GENAI.pdf"
    local = os.path.join(CV_PRETS, nom)
    return nom, (local if os.path.isfile(local) else None)


def contexte(headless: bool):
    from playwright.sync_api import sync_playwright
    os.makedirs(PROFILE, exist_ok=True)
    pw = sync_playwright().start()
    ctx = pw.chromium.launch_persistent_context(
        PROFILE, headless=headless, slow_mo=120,
        viewport={"width": 1440, "height": 950},
        locale="fr-FR", timezone_id="Europe/Paris",
        args=["--disable-blink-features=AutomationControlled"])
    return pw, ctx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--login", action="store_true",
                    help="ouvre Free-Work et attend votre connexion, puis quitte")
    ap.add_argument("--from", dest="src", help="fichier de missions notées")
    ap.add_argument("--max", type=int, default=5)
    ap.add_argument("--min-fit", type=int, default=70)
    ap.add_argument("--cv", default=None,
                    help="nom du CV sur Free-Work (défaut : axe générique, "
                         "ou nom du fichier si --cv-fichier)")
    ap.add_argument("--cv-fichier", default=None,
                    help="chemin local d'un CV à déposer sur Free-Work "
                         "s'il n'y est pas encore")
    ap.add_argument("--envoyer", action="store_true", help="lève le dry-run")
    ap.add_argument("--headless", action="store_true")
    args = ap.parse_args()
    if args.cv_fichier:
        args.cv_fichier = os.path.abspath(os.path.expanduser(args.cv_fichier))
    # Le CV est désormais choisi mission par mission : voir cv_pour_mission.

    pw, ctx = contexte(args.headless)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()

    try:
        if args.login:
            page.goto("https://www.free-work.com/fr/tech-it")
            print("Connectez-vous dans la fenêtre, puis revenez ici.")
            input("Appuyez sur Entrée une fois connecté… ")
            print(f"Session enregistrée dans {PROFILE}")
            return

        if not args.src:
            ap.error("--from est requis (ou --login)")

        data = json.load(open(args.src, encoding="utf-8"))
        lot = [d for d in data
               if d["match"]["verdict"] in ("apply", "shortlist")
               and d["match"]["fit"] >= args.min_fit][: args.max]

        print(f"{len(lot)} mission(s) — {'ENVOI RÉEL' if args.envoyer else 'simulation'}")
        if os.path.exists(STOP):
            print(f"kill-switch présent ({STOP}) — rien ne sera fait"); return

        agent = FreeWorkApplier(page, cv_repos=CV_REPOS, dry_run=not args.envoyer)
        if lot and not agent.session_active():
            from src.apply.base import Result, journal
            journal(Result("session", "https://www.free-work.com", "Contrôle de session",
                           "session_expiree",
                           "session Free-Work expirée : aucune candidature tentée. "
                           "Relancer make login."))
            print("SESSION EXPIRÉE — aucune candidature tentée. Relancer : make login")
            sys.exit(3)
        bilan = {}
        for i, d in enumerate(lot, 1):
            m, raw = d["match"], d["raw"]
            print(f"\n[{i}/{len(lot)}] {raw['title'][:64]}")
            try:
                cv, cv_local = cv_pour_mission(m, args.cv, args.cv_fichier)
                print(f"  CV : {cv}" + ("" if cv_local else "  (aucun fichier local)"))
                r = agent.postuler(raw["url"], m["aid"], raw["title"], cv,
                                   cv_fichier=cv_local)
            except KillSwitch as e:
                print(f"  ARRÊT — {e}"); break
            except Exception as e:                            # noqa: BLE001
                print(f"  échec technique : {e}"); bilan["echec"] = bilan.get("echec", 0) + 1
                continue
            bilan[r.status] = bilan.get(r.status, 0) + 1
            print(f"  {r.status} — {r.detail}")
            if i < len(lot):
                pause = random.uniform(90, 150)
                print(f"  pause {pause:.0f}s")
                time.sleep(pause)

        if args.envoyer:
            print("\nrestauration du CV de repos :",
                  "ok" if agent.restaurer_repos() else "ÉCHEC — à corriger à la main")
        print("\nbilan :", bilan)
        print("journal : data/journal.jsonl · captures :", out_dir())
    finally:
        ctx.close(); pw.stop()


if __name__ == "__main__":
    main()
