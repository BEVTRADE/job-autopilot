"""Socle de soumission : session persistante et garde-fous."""
from __future__ import annotations
import datetime as dt, json, os, random, time
from dataclasses import dataclass, field, asdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOME = os.path.expanduser("~/.job-autopilot")
PROFILE = os.path.join(HOME, "browser-profile")
STOP = os.path.join(HOME, "STOP")


@dataclass
class Result:
    uid: str
    url: str
    title: str
    status: str                     # envoyee | deja_postule | bloquee | echec | simulee
    detail: str = ""
    cv: str | None = None
    questions: list[dict] = field(default_factory=list)
    capture: str | None = None
    horodatage: str = field(default_factory=lambda: dt.datetime.now().isoformat(timespec="seconds"))

    def to_dict(self):
        return asdict(self)


class KillSwitch(Exception):
    pass


def guard():
    if os.path.exists(STOP):
        raise KillSwitch(f"arrêt demandé : {STOP} présent")


def humanize(lo: float = 0.6, hi: float = 1.8):
    """Pause irrégulière entre deux actions."""
    time.sleep(random.uniform(lo, hi))


def out_dir(day: str | None = None) -> str:
    day = day or dt.date.today().isoformat()
    d = os.path.join(ROOT, "data", "output", day, "candidatures")
    os.makedirs(d, exist_ok=True)
    return d


def journal(res: Result) -> str:
    """Trace inaltérable, une ligne JSON par tentative."""
    p = os.path.join(ROOT, "data", "journal.jsonl")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(res.to_dict(), ensure_ascii=False) + "\n")
    return p
