"""Socle commun aux sources de missions. Stdlib uniquement."""
from __future__ import annotations
import gzip, hashlib, io, json, re, time, urllib.error, urllib.request
from dataclasses import dataclass, field, asdict

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")


@dataclass
class RawMission:
    source: str
    url: str
    title: str = ""
    company: str | None = None
    job_family: str | None = None
    tjm_min: int | None = None
    tjm_max: int | None = None
    remote: str | None = None
    loc: str | None = None
    dur_val: int | None = None
    dur_per: str | None = None
    published: str | None = None
    skills: list[str] = field(default_factory=list)
    descr: str = ""

    @property
    def uid(self) -> str:
        """Identifiant stable pour le dédoublonnage inter-sources."""
        key = f"{_slug(self.title)}|{_slug(self.company or '')}"
        return hashlib.sha1(key.encode()).hexdigest()[:16]

    def to_dict(self):
        d = asdict(self)
        d["uid"] = self.uid
        return d


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def fetch(url: str, timeout: int = 25, retries: int = 2) -> str:
    """GET simple, décompression gzip, réessais espacés."""
    last = None
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml,application/xml,application/json;q=0.9,*/*;q=0.8",
                "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip",
            })
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    data = gzip.GzipFile(fileobj=io.BytesIO(data)).read()
                return data.decode("utf-8", "replace")
        except Exception as e:                      # noqa: BLE001
            last = e
            if i < retries:
                time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"fetch failed {url}: {last}")


def fetch_json(url: str, **kw):
    return json.loads(fetch(url, **kw))


# --------------------------------------------------------------------------- #
#  HTML -> texte, sans dépendance externe
# --------------------------------------------------------------------------- #

_DROP = re.compile(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>")
_TAG = re.compile(r"(?s)<[^>]+>")
_WS = re.compile(r"[ \t\xa0]+")
_NL = re.compile(r"\n{3,}")

_ENT = {"&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"',
        "&#39;": "'", "&eacute;": "é", "&egrave;": "è", "&agrave;": "à",
        "&ccedil;": "ç", "&ocirc;": "ô", "&ecirc;": "ê", "&euro;": "€"}


def html_to_text(html: str) -> str:
    t = _DROP.sub(" ", html)
    t = re.sub(r"(?i)</(p|div|li|tr|h[1-6]|section|article)>", "\n", t)
    t = re.sub(r"(?i)<br\s*/?>", "\n", t)
    t = _TAG.sub(" ", t)
    for k, v in _ENT.items():
        t = t.replace(k, v)
    t = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), t)
    t = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), t)
    t = _WS.sub(" ", t)
    return _NL.sub("\n\n", t).strip()


# --------------------------------------------------------------------------- #
#  Extracteurs communs
# --------------------------------------------------------------------------- #

# "500-550 €⁄j", "650 € / jour", "600-700€/j"  — ⁄ est U+2044, pas un slash
_TJM = re.compile(
    r"(\d{3,4})\s*(?:-|–|à|to)\s*(\d{3,4})\s*(?:€|EUR)\s*[/⁄]?\s*(?:j|jour|day)"
    r"|(\d{3,4})\s*(?:€|EUR)\s*[/⁄]\s*(?:j|jour|day)", re.I)

_DUR = re.compile(r"(\d{1,3})\s*(mois|ans?|semaines?|months?|years?|weeks?)", re.I)

_REMOTE = [
    (re.compile(r"(?i)100\s*%\s*(t[ée]l[ée]travail|remote)|full\s*remote|t[ée]l[ée]travail\s*total"), "full"),
    (re.compile(r"(?i)t[ée]l[ée]travail\s*(partiel|hybride)|hybride|\d\s*j(ours?)?\s*(de\s*)?t[ée]l[ée]travail|partial"), "partial"),
    (re.compile(r"(?i)sur\s*site|pas\s*de\s*t[ée]l[ée]travail|no\s*remote|100\s*%\s*présentiel"), "none"),
]


def parse_tjm(text: str) -> tuple[int | None, int | None]:
    m = _TJM.search(text)
    if not m:
        return None, None
    if m.group(1):
        a, b = int(m.group(1)), int(m.group(2))
        return min(a, b), max(a, b)
    v = int(m.group(3))
    return v, v


def parse_duration(text: str) -> tuple[int | None, str | None]:
    m = _DUR.search(text)
    if not m:
        return None, None
    n, unit = int(m.group(1)), m.group(2).lower()
    if unit.startswith(("an", "year")):
        return n, "year"
    if unit.startswith(("sem", "week")):
        return n, "week"
    return n, "month"


def parse_remote(text: str) -> str | None:
    for rx, val in _REMOTE:
        if rx.search(text):
            return val
    return None


class Source:
    """Interface d'une source de missions."""
    name: str = "base"

    def discover(self, cfg: dict) -> list[str]:
        """Retourne les URL de missions candidates."""
        raise NotImplementedError

    def parse(self, url: str) -> RawMission | None:
        """Charge et structure une mission."""
        raise NotImplementedError
