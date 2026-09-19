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
    python scripts/diag_session.py --visiter   # mesure de durée : une ligne dans data/diag-session.jsonl

Mesure de durée (EPIC-12, suite) : `--visiter` ouvre une page réservée aux
connectés, laisse le site renouveler ce qu'il veut renouveler, puis relève
l'état des trois cookies d'authentification. Une ligne par passage dans
data/diag-session.jsonl : présence, longueur et expiration, jamais une valeur.
Le passage prend le verrou du matin (~/.job-autopilot/verrou) et respecte le
kill-switch : il ne croise jamais une exécution du radar.
"""
from __future__ import annotations
import argparse, datetime as dt, glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src.apply.base import HOME, PROFILE, STOP           # noqa: E402
from src.apply.freework import FreeWorkApplier, BASE, CANDIDATURES, SEL  # noqa: E402

DOMAINE = "free-work.com"
DOSSIER = os.path.join(HOME, "diag")

# Mesure de durée. Le verrou est celui de scripts/matin.sh (un dossier, créé
# par mkdir, atomique) : les deux ne se croisent jamais, et le profil
# Chromium n'est jamais ouvert deux fois.
VERROU = os.path.join(HOME, "verrou")
JOURNAL = os.path.join(ROOT, "data", "diag-session.jsonl")
COOKIES_AUTH = ("jwt_s", "jwt_hp", "refresh_token")


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


# ------------------------------------------------------------ mesure de durée

def _expire_iso(ts) -> str | None:
    """Expiration à la seconde (le renouvellement se lit à la minute près, pas mieux)."""
    if ts is None or ts < 0:
        return None
    return dt.datetime.fromtimestamp(ts).isoformat(timespec="seconds")


def ligne_journal(connecte: bool, cookies: list[dict], chemin: str,
                  maintenant: dt.datetime | None = None) -> dict:
    """Une ligne du journal de durée.

    Construite champ par champ à partir du nom, de la longueur et de
    l'expiration : la valeur d'un cookie n'est jamais recopiée, il n'existe
    aucun chemin qui la transporte jusqu'au fichier. `chemin` est le chemin de
    la page d'arrivée, sans paramètres (une redirection vers la connexion en
    porte parfois).
    """
    par_nom = {c["name"]: c for c in cookies if DOMAINE in (c.get("domain") or "")}
    auth = {}
    for nom in COOKIES_AUTH:
        c = par_nom.get(nom)
        auth[nom] = {
            "present": c is not None,
            "longueur": len(c.get("value") or "") if c else 0,
            "expire": _expire_iso(c.get("expires")) if c else None,
        }
    return {
        "date": (maintenant or dt.datetime.now()).isoformat(timespec="seconds"),
        "connecte": bool(connecte),
        "page": chemin,
        **auth,
    }


def ajouter_journal(ligne: dict, fichier: str = JOURNAL) -> None:
    os.makedirs(os.path.dirname(fichier), exist_ok=True)
    with open(fichier, "a", encoding="utf-8") as f:
        f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
    os.chmod(fichier, 0o600)


def prendre_verrou(verrou: str = VERROU) -> bool:
    """Même protocole que matin.sh : mkdir échoue si le dossier existe."""
    os.makedirs(os.path.dirname(verrou), exist_ok=True)
    try:
        os.mkdir(verrou)
        return True
    except FileExistsError:
        return False


def visiter(page, ctx) -> dict:
    """Ouvre la page des candidatures, attend le réseau, puis relève.

    Le relevé des cookies vient après l'attente : c'est ce que le site a
    renouvelé pendant la visite qu'on veut voir.
    """
    page.goto(CANDIDATURES, wait_until="domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=30_000)
    except Exception:                                        # noqa: BLE001
        pass                                                 # page bavarde : on relève quand même
    try:
        page.locator(SEL["session"]).first.wait_for(timeout=8_000)
        connecte = True
    except Exception:                                        # noqa: BLE001
        connecte = False
    chemin = page.url.split("?", 1)[0].split("#", 1)[0].removeprefix(BASE)
    return ligne_journal(connecte, ctx.cookies(), chemin)


def afficher_ligne(l: dict) -> None:
    print(f"{l['date']}  connecté : {'OUI' if l['connecte'] else 'NON'}  page : {l['page']}")
    for nom in COOKIES_AUTH:
        c = l[nom]
        if c["present"]:
            print(f"  {nom:<14} {c['longueur']:>5} car.  expire {c['expire']}")
        else:
            print(f"  {nom:<14} absent")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--comparer", action="store_true",
                    help="compare les deux derniers relevés, sans ouvrir le navigateur")
    ap.add_argument("--visiter", action="store_true",
                    help="mesure de durée : visite une page de connecté, "
                         "ajoute une ligne à data/diag-session.jsonl")
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

    if args.visiter and os.path.exists(STOP):
        sys.exit(f"kill-switch présent ({STOP}) — aucune visite")
    verrou_pris = False
    if args.visiter:
        if not prendre_verrou():
            print(f"une exécution est déjà en cours ({VERROU}) — visite abandonnée")
            return
        verrou_pris = True

    try:
        _ouvrir_et_relever(args)
    finally:
        if verrou_pris:
            try:
                os.rmdir(VERROU)
            except OSError:
                pass


def _ouvrir_et_relever(args) -> None:
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
            r = visiter(page, ctx) if args.visiter else releve(page, ctx)
        finally:
            ctx.close()

    if args.visiter:
        ajouter_journal(r)
        afficher_ligne(r)
        print(f"\nligne ajoutée : {JOURNAL}")
        return
    afficher(r)
    os.makedirs(DOSSIER, exist_ok=True)
    chemin = os.path.join(DOSSIER, dt.datetime.now().strftime("%Y%m%d-%H%M%S") + ".json")
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=1)
    os.chmod(chemin, 0o600)
    print(f"\nrelevé enregistré : {chemin}")


if __name__ == "__main__":
    main()
