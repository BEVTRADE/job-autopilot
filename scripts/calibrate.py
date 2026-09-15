"""
Calibration du moteur de matching sur l'historique réel des 1901 candidatures.

Répond à trois questions :
  1. Le moteur remonte-t-il des missions mieux payées que le comportement passé ?
  2. Vers quels axes de CV oriente-t-il, et est-ce cohérent avec les clusters ?
  3. Combien de missions passeraient chaque jour le filtre ?
"""
import json, os, sqlite3, statistics, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src.matching.matcher import Matcher, Params            # noqa: E402

DB = os.path.join(ROOT, "reprise", "candidatures.db")
SRC = os.path.join(ROOT, "reprise", "cv_sources")

AXIS_FILE = {
    "ARCHITECTE_ENTREPRISE_URBANISTE": "FR_ARCHITECTE_ENTREPRISE_URBANISTE.md",
    "DIRECTEUR_PROGRAMME_DATA_IA":     "FR_DIRECTEUR_PROGRAMME_DATA_IA.md",
    "ARCHITECTE_IA_GENAI":             "FR_ARCHITECTE_IA_GENAI.md",
    "CONSULTANT_DATA_BI":              "FR_CONSULTANT_DATA_BI.md",
}


def med(xs):
    xs = [x for x in xs if x]
    return round(statistics.median(xs)) if xs else 0


def main():
    cv_texts = {}
    for aid, fn in AXIS_FILE.items():
        p = os.path.join(SRC, fn)
        if os.path.exists(p):
            cv_texts[aid] = open(p, encoding="utf-8").read()

    m = Matcher(cv_texts=cv_texts, params=Params())

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute("""
        select m.*, c.label as cluster_label
        from missions m left join clusters c using(aid)
    """).fetchall()

    skills_by_aid = {}
    for aid, sk in con.execute("select aid, skill from mission_skills"):
        skills_by_aid.setdefault(aid, []).append(sk)

    results = []
    for r in rows:
        d = dict(r)
        d["skills"] = skills_by_aid.get(r["aid"], [])
        mt = m.match(d)
        results.append((mt, d))

    tot = len(results)
    verdicts = {}
    for mt, _ in results:
        verdicts[mt.verdict] = verdicts.get(mt.verdict, 0) + 1

    all_tjm = [d["tjm_min"] for _, d in results if d["tjm_min"]]
    apply_tjm = [d["tjm_min"] for mt, d in results if mt.verdict == "apply" and d["tjm_min"]]
    short_tjm = [d["tjm_min"] for mt, d in results if mt.verdict == "shortlist" and d["tjm_min"]]
    cur_tjm = [d["tjm_min"] for _, d in results if d["bucket"] == "en_cours" and d["tjm_min"]]

    print("=" * 74)
    print(f"CALIBRATION — {tot} missions historiques")
    print("=" * 74)
    print("\nVerdicts")
    for k in ("apply", "shortlist", "reject"):
        n = verdicts.get(k, 0)
        print(f"  {k:<10} {n:>5}   {n/tot*100:>5.1f} %")

    print("\nTJM plancher médian")
    print(f"  toutes missions            {med(all_tjm):>4} €   (n={len(all_tjm)})")
    print(f"  candidatures en cours      {med(cur_tjm):>4} €   (n={len(cur_tjm)})  <- comportement actuel")
    print(f"  retenues 'shortlist'       {med(short_tjm):>4} €   (n={len(short_tjm)})")
    print(f"  retenues 'apply'           {med(apply_tjm):>4} €   (n={len(apply_tjm)})  <- moteur")

    hi = sum(1 for t in apply_tjm if t >= 650)
    hi_cur = sum(1 for t in cur_tjm if t >= 650)
    print(f"\nPart au-dessus de 650 €")
    print(f"  comportement actuel        {hi_cur/max(len(cur_tjm),1)*100:>5.1f} %")
    print(f"  moteur (apply)             {hi/max(len(apply_tjm),1)*100:>5.1f} %")

    print("\nRépartition des CV recommandés sur les 'apply'")
    ax = {}
    for mt, _ in results:
        if mt.verdict == "apply":
            ax[mt.axis_label] = ax.get(mt.axis_label, 0) + 1
    for k, v in sorted(ax.items(), key=lambda x: -x[1]):
        print(f"  {k:<42} {v:>4}   {v/max(sum(ax.values()),1)*100:>5.1f} %")

    print("\nCohérence axe recommandé / cluster d'origine (top 12)")
    pair = {}
    for mt, d in results:
        if mt.verdict in ("apply", "shortlist"):
            k = (d["cluster_label"] or "?", mt.axis_label)
            pair[k] = pair.get(k, 0) + 1
    for (cl, a), n in sorted(pair.items(), key=lambda x: -x[1])[:12]:
        print(f"  {cl[:38]:<38} -> {a[:32]:<32} {n:>4}")

    out = os.path.join(ROOT, "data", "calibration.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    top = sorted((mt for mt, _ in results if mt.verdict == "apply"),
                 key=lambda x: -x.decision_score)[:40]
    json.dump([t.to_dict() for t in top], open(out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"\nTop 40 exporté -> data/calibration.json")

    print("\nÉchantillon — 8 meilleures missions selon le moteur")
    for t in top[:8]:
        print(f"  {t.decision_score:>3} | fit {t.fit:>3} | {str(t.tjm_min or '-'):>4}-{str(t.tjm_max or '-'):<4} € | "
              f"{t.axis_id[:26]:<26} | {t.title[:44]}")


if __name__ == "__main__":
    main()
