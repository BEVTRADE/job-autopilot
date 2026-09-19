"""
Indeed — offres lues dans les alertes e-mail du candidat, jamais sur le site.

Pourquoi pas le site : les conditions d'utilisation d'Indeed interdisent
explicitement aux chercheurs d'emploi d'automatiser le processus de
candidature (« Use of any automation, scripting, or bots to automate the
Indeed Apply process outside of Indeed's official vendors and tooling is
prohibited », https://www.indeed.com/legal, vérifié le 19/09/2026). Indeed
ne propose par ailleurs aucune API de recherche d'offres aux candidats.

Ce que fait ce connecteur : le candidat configure ses alertes Indeed, qui
lui arrivent par courriel. Il dépose les courriels (.eml) dans
data/alertes/indeed/ — ou un outil de sa messagerie le fait pour lui. Ce
module les lit, en extrait les offres et les injecte dans la chaîne comme
n'importe quelle source. Aucun appel réseau, aucune visite du site.

La candidature Indeed reste manuelle : voir src/apply/indeed.py.

À VALIDER sur une vraie alerte : l'extraction repose sur l'identifiant
d'offre `jk`, présent dans les liens Indeed (viewjob, rc/clk, pagead/clk),
et sur le texte du lien comme intitulé. Le reste du gabarit des courriels
n'a pas encore été observé ; les tests utilisent un courriel construit.
"""
from __future__ import annotations
import email, glob, html, os, re
from email import policy
from urllib.parse import parse_qs, urlparse, unquote

from .base import RawMission

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOSSIER = os.path.join(ROOT, "data", "alertes", "indeed")
URL_OFFRE = "https://fr.indeed.com/viewjob?jk={jk}"

_LIEN = re.compile(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.I | re.S)
_BALISE = re.compile(r"<[^>]+>")
_JK = re.compile(r"^[0-9a-f]{16}$")


def cle_offre(href: str) -> str | None:
    """Identifiant d'offre Indeed (`jk`, 16 caractères hexadécimaux)."""
    href = html.unescape(href or "")
    for _ in range(3):                          # liens de suivi parfois encodés
        u = urlparse(href)
        if "indeed." not in (u.netloc or ""):
            q = parse_qs(u.query)
            cible = (q.get("url") or q.get("u") or q.get("target") or [None])[0]
            if not cible:
                return None
            href = unquote(cible)
            continue
        q = parse_qs(u.query)
        jk = (q.get("jk") or q.get("vjk") or [None])[0]
        return jk if jk and _JK.match(jk) else None
    return None


def _texte(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(_BALISE.sub(" ", fragment))).strip()


def _corps_html(msg) -> str:
    part = msg.get_body(preferencelist=("html",))
    return part.get_content() if part is not None else ""


def extraire(contenu_eml: bytes) -> list[RawMission]:
    """Offres contenues dans un courriel d'alerte Indeed, dédoublonnées par jk."""
    msg = email.message_from_bytes(contenu_eml, policy=policy.default)
    expediteur = (msg.get("From") or "").lower()
    if "indeed" not in expediteur:
        return []
    corps = _corps_html(msg)
    offres, vues = [], set()
    for href, interieur in _LIEN.findall(corps):
        jk = cle_offre(href)
        titre = _texte(interieur)
        if not jk or jk in vues or len(titre) < 4:
            continue
        vues.add(jk)
        offres.append(RawMission(source="indeed", url=URL_OFFRE.format(jk=jk),
                                 title=titre, published=msg.get("Date")))
    return offres


def collecter(dossier: str = DOSSIER) -> list[RawMission]:
    """Toutes les offres des courriels déposés, dédoublonnées entre courriels."""
    offres, vues = [], set()
    for chemin in sorted(glob.glob(os.path.join(dossier, "*.eml"))):
        try:
            contenu = open(chemin, "rb").read()
        except OSError:
            continue
        for o in extraire(contenu):
            if o.url not in vues:
                vues.add(o.url)
                offres.append(o)
    return offres
