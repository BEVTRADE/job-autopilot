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

from src.matching.matcher import Matcher, Params             # noqa: E402
from src.sources.freework import FreeWork                    # noqa: E402
from src.sources.boamp import Boamp                          # noqa: E402
from src.sources.freelance_informatique import FreelanceInformatique  # noqa: E402
from src.sources.ted import Ted                               # noqa: E402
from src.sources.freelancerepublik import FreelanceRepublik   # noqa: E402
from src.store import Store                                  # noqa: E402
from src.grouping import (group_missions, fingerprint,       # noqa: E402
                           similarity, DEFAULT_THRESHOLD, MissionGroup)

SOURCES = {
    "freework": FreeWork(),
    "boamp": Boamp(),
    "freelance_informatique": FreelanceInformatique(),
    "ted": Ted(),
    "freelancerepublik": FreelanceRepublik(),
}

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


def former_groupes(raws: list, threshold: float = DEFAULT_THRESHOLD) -> list[MissionGroup]:
    """Regroupement des annonces lues, après la lecture et avant la
    notation (EPIC-7) : la même mission publiée par plusieurs intermédiaires
    ne doit plus être traitée comme des missions distinctes."""
    return group_missions(raws, threshold=threshold)


def empreintes_historiques(store) -> list[frozenset]:
    """Empreintes des annonces déjà vues récemment, tous intermédiaires
    confondus. `None` (pas de store) donne un historique vide, donc aucun
    blocage — comportement inchangé de `--no-store`."""
    if store is None:
        return []
    return [fingerprint(r.get("title") or "", r.get("descr") or "")
            for r in store.recent_raw()]


def deja_connu(groupe: MissionGroup, historique: list[frozenset],
               threshold: float = DEFAULT_THRESHOLD) -> bool:
    """Un groupe est déjà connu si l'empreinte d'au moins une de ses
    annonces recoupe une annonce vue récemment, quel que soit
    l'intermédiaire. Sans ce contrôle au niveau du groupe (et non de
    l'uid exact), la même mission relancerait une candidature à chaque
    nouvel intermédiaire qui la republie — le point que vise le critère 6
    d'EPIC-7."""
    if not historique:
        return False
    fps = [fingerprint(m.title, m.descr) for m in groupe.missions]
    return any(similarity(fp, hfp) >= threshold for fp in fps for hfp in historique)


def noter_groupe(groupe: MissionGroup, matcher: Matcher):
    """Note le groupe sur l'annonce du mieux-disant. Si le mieux-disant est
    indéterminé (aucun TJM dans le groupe), note sur la première annonce —
    sans jamais prétendre qu'elle est la mieux placée commercialement."""
    ref = groupe.best or groupe.missions[0]
    m = matcher.match({
        "aid": ref.uid, "title": ref.title, "company": ref.company,
        "job": ref.job_family, "skills": ref.skills, "descr": ref.descr,
        "tjm_min": ref.tjm_min, "tjm_max": ref.tjm_max,
        "remote": ref.remote, "dur_val": ref.dur_val, "dur_per": ref.dur_per,
    })
    return m, ref


def noter_missions(all_raw: list, matcher: Matcher, store=None):
    """Le cœur d'EPIC-7 : regroupe puis note une seule fois par groupe, sur
    l'annonce du mieux-disant. Un groupe déjà connu de l'historique — même
    mission vue via un autre intermédiaire, à une date antérieure — n'est ni
    renoté ni republié (critère 6)."""
    groupes = former_groupes(all_raw)
    historique = empreintes_historiques(store)
    resultats = []
    for g in groupes:
        if deja_connu(g, historique):
            continue
        m, ref = noter_groupe(g, matcher)
        resultats.append((m, ref, g))
    return resultats


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

    all_raw, stats_all, started_all = [], {}, {}
    for name in names:
        src = SOURCES[name]
        started_all[name] = dt.datetime.now().isoformat(timespec="seconds")
        print(f"\n── {name} ─────────────────────────────────")
        try:
            urls = src.discover({"max_urls": args.limit})
        except Exception as e:                                   # noqa: BLE001
            print(f"   découverte impossible : {e}")
            continue
        print(f"   {len(urls)} URL candidates")

        stats = {"discovered": len(urls), "parsed": 0, "skipped": 0,
                 "apply": 0, "shortlist": 0, "reject": 0}

        for i, url in enumerate(urls, 1):
            raw = src.parse(url)
            if raw is None or not raw.title:
                continue
            stats["parsed"] += 1
            if store and store.is_known(raw.uid):
                stats["skipped"] += 1
                continue
            all_raw.append(raw)
            if i % 25 == 0:
                print(f"   {i}/{len(urls)} lues")
            time.sleep(args.delay)

        stats_all[name] = stats
        print(f"   lues {stats['parsed']} · déjà vues {stats['skipped']}")

    # regroupement, après la lecture des annonces et avant la notation
    resultats_notes = noter_missions(all_raw, matcher, store)

    results = []
    for m, ref, groupe in resultats_notes:
        source_stats = stats_all.get(ref.source)
        if source_stats is not None:
            source_stats[m.verdict] += 1
        if store:
            for membre in groupe.missions:
                store.record(membre, m)
        if m.verdict in ("apply", "shortlist"):
            results.append((m, ref, groupe))

    for name in names:
        if store and name in stats_all:
            store.log_run(name, started_all[name], stats_all[name])
        if name in stats_all:
            s = stats_all[name]
            print(f"   {name} · apply {s['apply']} · shortlist {s['shortlist']} · "
                  f"rejetées {s['reject']}")

    results.sort(key=lambda x: -x[0].decision_score)
    path = write_report(results, stats_all)
    print(f"\n{len(results)} missions retenues (regroupées) → {path}")
    if args.open:
        webbrowser.open(f"file://{path}")


# --------------------------------------------------------------------------- #

def write_report(results, stats, out_dir: str | None = None) -> str:
    day = dt.date.today().isoformat()
    out_dir = out_dir or os.path.join(ROOT, "data", "output", day)
    os.makedirs(out_dir, exist_ok=True)

    def groupe_to_dict(groupe: MissionGroup) -> list[dict]:
        return [{"company": mm.company, "url": mm.url,
                 "tjm_min": mm.tjm_min, "tjm_max": mm.tjm_max}
                for mm in groupe.missions]

    json.dump([{"match": m.to_dict(), "raw": r.to_dict(),
                "groupe": groupe_to_dict(g)} for m, r, g in results],
              open(os.path.join(out_dir, "retenues.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    e = html.escape
    rows = []
    for m, r, g in results:
        badge = "apply" if m.verdict == "apply" else "short"

        if g.best is None:
            tjm_txt = "mieux-disant indéterminé (aucun TJM affiché)"
        elif g.spread is None:
            tjm_txt = f"{g.best.tjm_min}–{g.best.tjm_max} € (un seul TJM connu)"
        else:
            tjm_txt = f"{g.best.tjm_min}–{g.best.tjm_max} € · écart {g.spread} €"
        if g.nb_sans_tjm:
            tjm_txt += f" · {g.nb_sans_tjm} sans TJM"

        intermediaires = ", ".join(
            f"{mm.company or '?'} ({mm.tjm_min}-{mm.tjm_max} €)"
            if mm.tjm_min is not None else f"{mm.company or '?'} (TJM ?)"
            for mm in g.missions)
        miss = ", ".join(m.skills_missing[:6]) or "—"
        rows.append(f"""
        <tr class="{badge}">
          <td class="sc"><b>{m.decision_score}</b><small>fit {m.fit} · val {m.value}</small></td>
          <td><a href="{e(r.url)}" target="_blank">{e(g.title[:90])}</a>
              <small>{e(intermediaires)}</small></td>
          <td>{e(tjm_txt)}</td>
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
