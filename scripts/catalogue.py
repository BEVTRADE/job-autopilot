"""
Passe systématique sur le catalogue de compétences (EPIC-4 / chantier 2).

Confronte le vocabulaire des huit CV — le catalogue déclaré dans
profile/cv_catalog.json (titres, compétences signature, renforçantes) et le
texte des huit fiches FR/EN de reprise/cv_sources — à celui des missions déjà
collectées dans reprise/candidatures.db. Signale les étiquettes de
compétence fréquentes qu'aucun axe ne couvre.

Trois points aveugles trouvés par hasard début septembre — gouvernance IA,
fraude et LCB-FT, acculturation — ont fait chuter le score d'une mission de
51 à 90 une fois corrigés. Cette passe cherche les suivants méthodiquement.

Ne modifie jamais profile/cv_catalog.json : le rapport propose, la décision
d'ajouter, d'ignorer ou de déclarer hors profil reste humaine.

    python3 scripts/catalogue.py [--min-freq N]

Sortie : data/catalogue.md, et un résumé sur la sortie standard.
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, sqlite3, statistics, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src.matching.matcher import Matcher, Params            # noqa: E402
from src.matching.text import norm                          # noqa: E402

DB = os.path.join(ROOT, "reprise", "candidatures.db")
SRC = os.path.join(ROOT, "reprise", "cv_sources")
CATALOG = os.path.join(ROOT, "profile", "cv_catalog.json")
OUT = os.path.join(ROOT, "data", "catalogue.md")

MIN_FREQ_DEFAUT = 5


def med(xs: list[int]) -> int:
    xs = [x for x in xs if x]
    return round(statistics.median(xs)) if xs else 0


def charger_textes_cv(cat: dict) -> dict[str, str]:
    """Les huit CV : la fiche FR et la fiche EN de chaque axe, concaténées."""
    textes = {}
    for axe in cat["axes"]:
        morceaux = []
        for langue in ("fr", "en"):
            nom = os.path.splitext(os.path.basename(axe["files"][langue]))[0] + ".md"
            chemin = os.path.join(SRC, nom)
            if os.path.exists(chemin):
                morceaux.append(open(chemin, encoding="utf-8").read())
        textes[axe["id"]] = "\n".join(morceaux)
    return textes


def groupes_exclus(cat: dict) -> dict[str, list[str]]:
    dx = cat.get("domain_exclusions", {})
    return {g: [norm(t) for t in termes] for g, termes in dx.get("groups", {}).items()}


def groupes_hors_profil(terme: str, groupes: dict[str, list[str]]) -> list[str]:
    n = norm(terme)
    return [g for g, termes in groupes.items() if any(e in n or n in e for e in termes)]


def analyser(min_freq: int) -> dict:
    cat = json.load(open(CATALOG, encoding="utf-8"))
    matcher = Matcher(catalog_path=CATALOG, cv_texts=charger_textes_cv(cat), params=Params())
    groupes = groupes_exclus(cat)

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    total_missions = con.execute("select count(*) from missions").fetchone()[0]
    skills = [r[0] for r in con.execute("select distinct skill from mission_skills")]

    inconnus = [s for s in skills if not matcher.covers(s)]

    lignes = []
    if inconnus:
        lignes = con.execute(
            "select ms.skill, m.aid, m.title, m.company, m.tjm_min, m.tjm_max "
            "from mission_skills ms join missions m using(aid) "
            "where ms.skill in ({})".format(",".join("?" * len(inconnus))),
            inconnus,
        ).fetchall()

    par_terme: dict[str, list[sqlite3.Row]] = {}
    for r in lignes:
        par_terme.setdefault(r["skill"], []).append(r)

    candidats, hors_profil = [], []
    for terme, lignes_t in par_terme.items():
        freq = len({r["aid"] for r in lignes_t})
        if freq < min_freq:
            continue
        tjms = [r["tjm_min"] for r in lignes_t if r["tjm_min"]]
        exemple = max(lignes_t, key=lambda r: r["tjm_min"] or 0)
        entree = {
            "terme": terme,
            "frequence": freq,
            "tjm_median": med(tjms),
            "exemple": {
                "titre": exemple["title"],
                "societe": exemple["company"] or "société non précisée",
                "tjm_min": exemple["tjm_min"],
                "tjm_max": exemple["tjm_max"],
                "aid": exemple["aid"],
            },
        }
        gr = groupes_hors_profil(terme, groupes)
        if gr:
            entree["groupes"] = gr
            hors_profil.append(entree)
        else:
            candidats.append(entree)

    candidats.sort(key=lambda x: (-x["tjm_median"], -x["frequence"]))
    hors_profil.sort(key=lambda x: (-x["tjm_median"], -x["frequence"]))

    return {
        "total_missions": total_missions,
        "total_termes": len(skills),
        "total_inconnus": len(inconnus),
        "min_freq": min_freq,
        "candidats": candidats,
        "hors_profil": hors_profil,
    }


def fmt_tjm(r: dict) -> str:
    lo, hi = r["tjm_min"], r["tjm_max"]
    if lo and hi and lo != hi:
        return f"{lo}-{hi} €"
    if lo or hi:
        return f"{lo or hi} €"
    return "TJM non communiqué"


def fmt_exemple(e: dict) -> str:
    return f"« {e['titre']} » — {e['societe']} ({fmt_tjm(e)})"


def tableau(lignes: list[dict], avec_groupe: bool) -> str:
    entetes = ["TJM médian", "Fréquence", "Terme"]
    if avec_groupe:
        entetes.append("Groupe exclu")
    entetes.append("Exemple d'annonce réelle")
    out = ["| " + " | ".join(entetes) + " |", "|" + "---|" * len(entetes)]
    for r in lignes:
        cols = [f"{r['tjm_median']} €", str(r["frequence"]), r["terme"]]
        if avec_groupe:
            cols.append(", ".join(r["groupes"]))
        cols.append(fmt_exemple(r["exemple"]))
        out.append("| " + " | ".join(cols) + " |")
    return "\n".join(out)


def ecrire_rapport(res: dict) -> str:
    jour = dt.date.today().isoformat()
    lignes = [
        "# Rapport catalogue — écart entre le vocabulaire des CV et celui des missions",
        "",
        f"Généré le {jour}. {res['total_missions']} missions historiques, "
        f"{res['total_termes']} étiquettes de compétence distinctes, "
        f"{res['total_inconnus']} absentes du catalogue déclaré (huit CV + "
        "`profile/cv_catalog.json`).",
        "",
        f"Seuil de fréquence retenu ici : au moins {res['min_freq']} missions "
        "(`--min-freq` pour changer). En dessous, le signal est trop faible "
        "pour distinguer un point aveugle d'un cas isolé.",
        "",
        "Classement par TJM médian décroissant : un terme absent porté par des "
        "missions à 800 € coûte plus cher qu'un terme absent à 400 €.",
        "",
        "**Aucune modification automatique de `profile/cv_catalog.json`. Ce "
        "rapport propose des candidats ; la décision d'ajouter, d'ignorer ou "
        "de confirmer hors profil reste humaine.**",
        "",
        "## Candidats à examiner — compétence réelle possiblement non déclarée",
        "",
        "Ces termes ne recoupent aucun groupe `domain_exclusions` du "
        "catalogue : rien n'indique qu'ils soient hors profil. À vérifier un "
        "par un avant tout ajout.",
        "",
    ]
    lignes.append(tableau(res["candidats"], avec_groupe=False) if res["candidats"]
                  else "*Aucun candidat au-dessus du seuil de fréquence.*")
    lignes += [
        "",
        "## Hors profil — déjà exclu du catalogue",
        "",
        "Ces termes recoupent un groupe `domain_exclusions` déjà déclaré dans "
        "`profile/cv_catalog.json` (EPC, broadcast, ERP fonctionnel, BPM/case "
        "management, comptabilité, réseau/infra). Listés pour transparence, "
        "pas comme candidats à l'ajout.",
        "",
    ]
    lignes.append(tableau(res["hors_profil"], avec_groupe=True) if res["hors_profil"]
                  else "*Aucun terme hors profil au-dessus du seuil de fréquence.*")
    lignes.append("")
    return "\n".join(lignes)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-freq", type=int, default=MIN_FREQ_DEFAUT,
                     help=f"fréquence minimale pour figurer au rapport (défaut {MIN_FREQ_DEFAUT})")
    args = ap.parse_args()

    res = analyser(args.min_freq)
    rapport = ecrire_rapport(res)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(rapport)

    print("=" * 74)
    print(f"CATALOGUE — {res['total_missions']} missions, {res['total_termes']} étiquettes, "
          f"{res['total_inconnus']} absentes du catalogue")
    print("=" * 74)
    print(f"\nSeuil : fréquence >= {res['min_freq']}")
    print(f"  candidats à examiner   {len(res['candidats']):>4}")
    print(f"  hors profil (exclus)   {len(res['hors_profil']):>4}")

    print("\nTop 15 candidats par TJM médian décroissant")
    for r in res["candidats"][:15]:
        print(f"  {r['tjm_median']:>4} €  n={r['frequence']:<4} {r['terme']}")

    print(f"\nRapport complet -> data/catalogue.md")


if __name__ == "__main__":
    main()
