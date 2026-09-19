"""Diagnostic de la session Free-Work — EPIC-12, niveau 1.

Ouvre le profil persistant comme le font apply.py et la sonde, vérifie la
connexion avec session_active(), puis inventorie ce qui porte
l'authentification : cookies du domaine free-work.com, clés du stockage local
et du stockage de session, bases IndexedDB.

Aucune valeur n'est jamais affichée ni enregistrée : pour chaque élément, son
nom, sa longueur et son expiration. Chaque passage écrit un instantané dans
~/.job-autopilot/diag/ ; `--comparer` met en regard les deux derniers.

    python scripts/diag_session.py             # relevé
    python scripts/diag_session.py --comparer  # ce qui a disparu entre les deux derniers
"""
from __future__ import annotations
import argparse, datetime as dt, glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src.apply.base import HOME, PROFILE                 # noqa: E402
from src.apply.freework import FreeWorkApplier, BASE     # noqa: E402

DOMAINE = "free-work.com"
DOSSIER = os.path.join(HOME, "diag")


def _expiration(ts: float) -> str:
    """Playwright donne -1 pour un cookie de session, sans date d'expiration."""
    if ts is None or ts < 0:
        return "session"
    return dt.datetime.fromtimestamp(ts).isoformat(timespec="minutes")


def inventaire_cookies(cookies: list[dict]) -> list[dict]:
    """Cookies du domaine, réduits à ce qui n'est pas secret."""
    out = []
    for c in cookies:
        if DOMAINE not in (c.get("domain") or ""):
            continue
        out.append({
            "nom": c["name"], "domaine": c["domain"], "chemin": c.get("path", "/"),
            "longueur": len(c.get("value") or ""),
            "expire": _expiration(c.get("expires")),
            "httpOnly": bool(c.get("httpOnly")), "secure": bool(c.get("secure")),
            "sameSite": c.get("sameSite", ""),
        })
    return sorted(out, key=lambda c: (c["domaine"], c["nom"]))


# Exécuté dans la page : jamais de valeur, seulement clé et longueur.
JS_STOCKAGES = """async () => {
  const lire = (s) => Object.keys(s).map(k => ({cle: k, longueur: (s.getItem(k) || '').length}));
  let bases = [];
  try { bases = (await indexedDB.databases()).map(d => d.name); } catch (e) {}
  return {local: lire(localStorage), session: lire(sessionStorage), indexeddb: bases};
}"""


def releve(page, ctx) -> dict:
    agent = FreeWorkApplier(page, cv_repos="", dry_run=True)
    connecte = agent.session_active()          # navigue sur /fr/tech-it
    st = page.evaluate(JS_STOCKAGES)
    return {
        "date": dt.datetime.now().isoformat(timespec="seconds"),
        "connecte": connecte,
        "cookies": inventaire_cookies(ctx.cookies()),
        "stockage_local": st["local"],
        "stockage_session": st["session"],
        "indexeddb": st["indexeddb"],
    }


def afficher(r: dict) -> None:
    print(f"connexion (session_active) : {'OUI' if r['connecte'] else 'NON'}")
    ck = r["cookies"]
    n_session = sum(1 for c in ck if c["expire"] == "session")
    print(f"\ncookies {DOMAINE} : {len(ck)} dont {n_session} de session (sans expiration)")
    for c in ck:
        drap = ("H" if c["httpOnly"] else "-") + ("S" if c["secure"] else "-")
        print(f"  {c['nom']:<34} {c['domaine']:<22} {c['expire']:<17} "
              f"{c['longueur']:>5} car. {drap}")
    for titre, cle in (("stockage local", "stockage_local"),
                       ("stockage de session", "stockage_session")):
        print(f"\n{titre} : {len(r[cle])} clé(s)")
        for e in r[cle]:
            print(f"  {e['cle']:<44} {e['longueur']:>6} car.")
    print(f"\nIndexedDB : {', '.join(r['indexeddb']) or 'aucune base'}")


def _cles(r: dict) -> dict[str, str]:
    """Éléments d'un relevé, indexés par nature+nom, avec leur expiration."""
    d = {f"cookie {c['domaine']} {c['nom']}": c["expire"] for c in r["cookies"]}
    d.update({f"local {e['cle']}": "-" for e in r["stockage_local"]})
    d.update({f"session {e['cle']}": "-" for e in r["stockage_session"]})
    d.update({f"indexeddb {n}": "-" for n in r["indexeddb"]})
    return d


def comparer(avant: dict, apres: dict) -> list[str]:
    a, b = _cles(avant), _cles(apres)
    lignes = [f"connexion : {'OUI' if avant['connecte'] else 'NON'} → "
              f"{'OUI' if apres['connecte'] else 'NON'}"]
    for k in sorted(a.keys() - b.keys()):
        lignes.append(f"  disparu   {k}  (expirait : {a[k]})")
    for k in sorted(b.keys() - a.keys()):
        lignes.append(f"  apparu    {k}  (expire : {b[k]})")
    for k in sorted(a.keys() & b.keys()):
        if a[k] != b[k]:
            lignes.append(f"  modifié   {k}  ({a[k]} → {b[k]})")
    if len(lignes) == 1:
        lignes.append("  aucune différence")
    return lignes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--comparer", action="store_true",
                    help="compare les deux derniers relevés, sans ouvrir le navigateur")
    ap.add_argument("--headless", action="store_true")
    args = ap.parse_args()

    if args.comparer:
        fichiers = sorted(glob.glob(os.path.join(DOSSIER, "*.json")))[-2:]
        if len(fichiers) < 2:
            sys.exit("il faut deux relevés : lancer le diagnostic deux fois")
        av, ap_ = (json.load(open(f, encoding="utf-8")) for f in fichiers)
        print(f"{os.path.basename(fichiers[0])} → {os.path.basename(fichiers[1])}")
        print("\n".join(comparer(av, ap_)))
        return

    from playwright.sync_api import sync_playwright
    os.makedirs(PROFILE, exist_ok=True)
    print(f"profil : {PROFILE}")
    with sync_playwright() as pw:
        try:
            # Mêmes paramètres qu'apply.py et la sonde : c'est le comportement
            # de ces deux-là qu'on mesure.
            ctx = pw.chromium.launch_persistent_context(
                PROFILE, headless=args.headless, slow_mo=120,
                viewport={"width": 1440, "height": 950},
                locale="fr-FR", timezone_id="Europe/Paris",
                args=["--disable-blink-features=AutomationControlled"])
        except Exception as e:                                 # noqa: BLE001
            sys.exit(f"profil inutilisable (navigateur déjà ouvert dessus ?) : "
                     f"{str(e).splitlines()[0]}")
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            r = releve(page, ctx)
        finally:
            ctx.close()

    afficher(r)
    os.makedirs(DOSSIER, exist_ok=True)
    chemin = os.path.join(DOSSIER, dt.datetime.now().strftime("%Y%m%d-%H%M%S") + ".json")
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=1)
    os.chmod(chemin, 0o600)
    print(f"\nrelevé enregistré : {chemin}")


if __name__ == "__main__":
    main()
