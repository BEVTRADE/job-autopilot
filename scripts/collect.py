#!/usr/bin/env python3
"""
Collecte quotidienne : découverte -> lecture -> matching -> rapport.

    python3 scripts/collect.py                 # toutes les sources actives
    python3 scripts/collect.py --source freework --limit 40
    python3 scripts/collect.py --no-store      # essai sans écrire l'historique

Aucune candidature n'est envoyée : ce script ne fait que remonter et classer.
"""
from __future__ import annotations
import argparse, datetime as dt, html, json, os, sys, time, webbrowser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.matching.matcher import Matcher, Params            # noqa: E402
from src.sources.freework import FreeWork                   # noqa: E402
from src.sources.boamp import Boamp                         # noqa: E402
from src.store import Store                                 # noqa: E402

SOURCES = {"freework": FreeWork(), "boamp": Boamp()}

AXIS_MD = {
    "ARCHITECTE_ENTREPRISE_URBANISTE": "FR_ARCHITECTE_ENTREPRISE_URBANISTE.md",
    "DIRECTEUR_PROGRAMME_DATA_IA":     "FR_DIRECTEUR_PROGRAMME_DATA_IA.md",
    "ARCHITECTE_IA_GENAI":             "FR_ARCHITECTE_IA_GENAI.md",
    "CONSULTANT_DATA_BI":              "FR_CONSULTANT_DATA_BI.md",
}


def load_cv_texts():
    src = os.path.join(ROOT, "reprise", "cv_sources")
    out = {}
    for aid, fn in AXIS_MD.items():
        p = os.path.join(src, fn)
        if os.path.exists(p):
            out[aid] = open(p, encoding="utf-8").read()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", action="append", choices=list(SOURCES))
    ap.add_argument("--limit", type=int, default=250, help="URL max par source")
    ap.add_argument("--delay", type=float, default=1.0, help="pause entre requêtes (s)")
    ap.add_argument("--no-store", action="store_true")
    ap.add_argument("--open", action="store_true", help="ouvrir le rapport")
    args = ap.parse_args()

    names = args.source or list(SOURCES)
    matcher = Matcher(cv_texts=load_cv_texts(), params=Params())
    store = None if args.no_store else Store(os.path.join(ROOT, "data", "radar.db"))

    results, stats_all = [], {}
    for name in names:
        src = SOURCES[name]
        started = dt.datetime.now().isoformat(timespec="seconds")
        print(f"\n── {name} ─────────────────────────────────")
        try:
            urls = src.discover({"max_urls": args.limit})
        except Exception as e:                                   # noqa: BLE001
            print(f"   découverte impossible : {e}")
            continue
        print(f"   {len(urls)} URL candidates")

        stats = {"discovered": len(urls), "parsed": 0,
                 "apply": 0, "shortlist": 0, "reject": 0, "skipped": 0}

        for i, url in enumerate(urls, 1):
            raw = src.parse(url)
            if raw is None or not raw.title:
                continue
            stats["parsed"] += 1
            if store and store.is_known(raw.uid):
                stats["skipped"] += 1
                continue

            m = matcher.match({
                "aid": raw.uid, "title": raw.title, "company": raw.company,
                "job": raw.job_family, "skills": raw.skills, "descr": raw.descr,
                "tjm_min": raw.tjm_min, "tjm_max": raw.tjm_max,
                "remote": raw.remote, "dur_val": raw.dur_val, "dur_per": raw.dur_per,
            })
            stats[m.verdict] += 1
            if store:
                store.record(raw, m)
            if m.verdict in ("apply", "shortlist"):
                results.append((m, raw))
            if i % 25 == 0:
                print(f"   {i}/{len(urls)}  retenues {stats['apply']+stats['shortlist']}")
            time.sleep(args.delay)

        if store:
            store.log_run(name, started, stats)
        stats_all[name] = stats
        print(f"   lues {stats['parsed']} · déjà vues {stats['skipped']} · "
              f"apply {stats['apply']} · shortlist {stats['shortlist']} · "
              f"rejetées {stats['reject']}")

    results.sort(key=lambda x: -x[0].decision_score)
    path = write_report(results, stats_all)
    print(f"\n{len(results)} missions retenues → {path}")
    if args.open:
        webbrowser.open(f"file://{path}")


# --------------------------------------------------------------------------- #

def write_report(results, stats) -> str:
    day = dt.date.today().isoformat()
    out_dir = os.path.join(ROOT, "data", "output", day)
    os.makedirs(out_dir, exist_ok=True)

    json.dump([{"match": m.to_dict(), "raw": r.to_dict()} for m, r in results],
              open(os.path.join(out_dir, "retenues.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    e = html.escape
    rows = []
    for m, r in results:
        badge = "apply" if m.verdict == "apply" else "short"
        tjm = f"{m.tjm_min or '?'}–{m.tjm_max or '?'} €" if m.tjm_min else "non communiqué"
        miss = ", ".join(m.skills_missing[:6]) or "—"
        rows.append(f"""
        <tr class="{badge}">
          <td class="sc"><b>{m.decision_score}</b><small>fit {m.fit} · val {m.value}</small></td>
          <td><a href="{e(r.url)}" target="_blank">{e(m.title[:90])}</a>
              <small>{e(m.company or r.source)}</small></td>
          <td>{e(tjm)}</td>
          <td>{e(m.axis_label)}<small>{e(m.lang.upper())}</small></td>
          <td class="miss"><small>{e(miss)}</small></td>
        </tr>""")

    summary = " · ".join(
        f"{k} : {v['parsed']} lues, {v['apply']+v['shortlist']} retenues"
        for k, v in stats.items()) or "aucune source"

    doc = f"""<!doctype html><html lang="fr"><meta charset="utf-8">
<title>Radar missions — {day}</title>
<style>
 :root{{color-scheme:light dark;--bg:#fbfaf8;--fg:#1a1a19;--mut:#6b6862;
        --line:#e5e2dc;--card:#fff;--ok:#1a7f4b;--warn:#9a6a00}}
 @media(prefers-color-scheme:dark){{:root{{--bg:#161614;--fg:#ece9e3;--mut:#9a958c;
        --line:#2e2b27;--card:#1e1c19;--ok:#4ade80;--warn:#fbbf24}}}}
 body{{margin:0;background:var(--bg);color:var(--fg);
      font:15px/1.5 ui-sans-serif,-apple-system,Segoe UI,sans-serif}}
 .wrap{{max-width:1100px;margin:0 auto;padding:32px 20px 60px}}
 h1{{font-size:22px;margin:0 0 4px}} .sub{{color:var(--mut);margin:0 0 28px;font-size:13px}}
 .box{{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:10px}}
 table{{border-collapse:collapse;width:100%;min-width:760px}}
 th,td{{padding:11px 14px;text-align:left;border-bottom:1px solid var(--line);
        vertical-align:top}}
 th{{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--mut)}}
 tr:last-child td{{border-bottom:0}}
 small{{display:block;color:var(--mut);font-size:12px;margin-top:2px}}
 a{{color:inherit;text-decoration:none;font-weight:600}} a:hover{{text-decoration:underline}}
 .sc b{{font-size:17px}} .apply .sc b{{color:var(--ok)}} .short .sc b{{color:var(--warn)}}
 .miss{{max-width:230px}} .empty{{padding:40px;text-align:center;color:var(--mut)}}
</style>
<div class="wrap">
<h1>Radar missions — {day}</h1>
<p class="sub">{e(summary)}</p>
<div class="box"><table>
<tr><th>Score</th><th>Mission</th><th>TJM</th><th>CV recommandé</th><th>Compétences absentes</th></tr>
{''.join(rows) or '<tr><td colspan="5" class="empty">Aucune mission retenue aujourd’hui.</td></tr>'}
</table></div></div></html>"""

    p = os.path.join(out_dir, "rapport.html")
    open(p, "w", encoding="utf-8").write(doc)
    return p


if __name__ == "__main__":
    main()
