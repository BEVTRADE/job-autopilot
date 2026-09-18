"""Historique et dédoublonnage. SQLite, stdlib."""
from __future__ import annotations
import json, os, sqlite3, datetime as dt

SCHEMA = """
create table if not exists seen (
  uid text primary key,
  source text, url text, title text, company text,
  tjm_min int, tjm_max int, verdict text, fit int, value int, score int,
  axis text, first_seen text, last_seen text, payload text
);
create table if not exists runs (
  id integer primary key autoincrement,
  started text, finished text, source text,
  discovered int, parsed int, applied int, shortlisted int, rejected int
);
create index if not exists idx_seen_last on seen(last_seen);
"""


class Store:
    def __init__(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.con = sqlite3.connect(path)
        self.con.row_factory = sqlite3.Row
        self.con.executescript(SCHEMA)
        self.con.commit()

    def is_known(self, uid: str, days: int = 120) -> bool:
        cut = (dt.datetime.now() - dt.timedelta(days=days)).isoformat()
        r = self.con.execute(
            "select 1 from seen where uid=? and last_seen>=?", (uid, cut)).fetchone()
        return r is not None

    def record(self, raw, match) -> None:
        now = dt.datetime.now().isoformat(timespec="seconds")
        self.con.execute("""
            insert into seen(uid,source,url,title,company,tjm_min,tjm_max,
                             verdict,fit,value,score,axis,first_seen,last_seen,payload)
            values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            on conflict(uid) do update set last_seen=excluded.last_seen,
                verdict=excluded.verdict, score=excluded.score
        """, (raw.uid, raw.source, raw.url, raw.title, raw.company,
              raw.tjm_min, raw.tjm_max, match.verdict, match.fit, match.value,
              match.decision_score, match.axis_id, now, now,
              json.dumps({"raw": raw.to_dict(), "match": match.to_dict()},
                         ensure_ascii=False)))
        self.con.commit()

    def recent_raw(self, days: int = 120) -> list[dict]:
        """Champs bruts (dont le corps de l'annonce) des annonces vues
        récemment, quel que soit l'intermédiaire. Sert à comparer l'empreinte
        d'un groupe du jour à celle d'une annonce déjà vue sous un autre uid
        (autre société) — sans ça, la même mission republiée par un nouvel
        intermédiaire redéclencherait une candidature (EPIC-7, critère 6)."""
        cut = (dt.datetime.now() - dt.timedelta(days=days)).isoformat()
        rows = self.con.execute(
            "select payload from seen where last_seen>=?", (cut,)).fetchall()
        out = []
        for r in rows:
            try:
                out.append(json.loads(r["payload"])["raw"])
            except (KeyError, ValueError, TypeError):
                continue
        return out

    def log_run(self, source: str, started: str, stats: dict) -> None:
        self.con.execute("""
            insert into runs(started,finished,source,discovered,parsed,
                             applied,shortlisted,rejected)
            values(?,?,?,?,?,?,?,?)
        """, (started, dt.datetime.now().isoformat(timespec="seconds"), source,
              stats.get("discovered", 0), stats.get("parsed", 0),
              stats.get("apply", 0), stats.get("shortlist", 0), stats.get("reject", 0)))
        self.con.commit()
