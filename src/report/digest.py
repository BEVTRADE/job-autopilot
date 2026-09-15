"""
Consolidation du matin : ce qui a été repéré, envoyé, bloqué.

Lit les traces produites par la collecte et par la soumission, et n'invente
rien : une mission absente du journal n'a pas été tentée, et c'est dit.

    python3 -m src.report.digest              # aujourd'hui
    python3 -m src.report.digest 2026-09-15   # un jour précis
"""
from __future__ import annotations
import datetime as dt, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

STATUTS = ["envoyee", "simulee", "deja_postule", "bloquee", "echec"]
LIBELLE = {
    "envoyee": "envoyées et confirmées",
    "simulee": "simulées, dry-run actif",
    "deja_postule": "déjà candidat",
    "bloquee": "bloquées, reprise manuelle",
    "echec": "échecs techniques",
}


def jour_dir(day: str) -> str:
    return os.path.join(ROOT, "data", "output", day)


def lire_journal(day: str) -> list[dict]:
    p = os.path.join(ROOT, "data", "journal.jsonl")
    if not os.path.exists(p):
        return []
    out = []
    for ligne in open(p, encoding="utf-8"):
        ligne = ligne.strip()
        if not ligne:
            continue
        try:
            e = json.loads(ligne)
        except json.JSONDecodeError:
            continue
        if str(e.get("horodatage", "")).startswith(day):
            out.append(e)
    return out


def lire_retenues(day: str) -> list[dict]:
    p = os.path.join(jour_dir(day), "retenues.json")
    if not os.path.exists(p):
        return []
    try:
        return json.load(open(p, encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def file_attente(entrees: list[dict]) -> list[dict]:
    """Les candidatures à reprendre à la main, avec le motif."""
    return [{"titre": e.get("title"), "url": e.get("url"),
             "motif": e.get("detail"), "cv": e.get("cv"),
             "horodatage": e.get("horodatage")}
            for e in entrees if e.get("status") in ("bloquee", "echec")]


def construire(day: str) -> tuple[str, dict]:
    entrees = lire_journal(day)
    retenues = lire_retenues(day)
    compte = {s: sum(1 for e in entrees if e.get("status") == s) for s in STATUTS}
    attente = file_attente(entrees)

    L = [f"# Rapport du {day}", ""]

    if not retenues and not entrees:
        L += ["Aucune trace pour cette date : ni collecte, ni tentative de",
              "candidature. Le script du matin n'a probablement pas tourné.", ""]
        return "\n".join(L), {"compte": compte, "attente": attente,
                              "retenues": 0, "tentees": 0}

    L += [f"Missions retenues par le moteur : **{len(retenues)}**",
          f"Candidatures tentées : **{len(entrees)}**", ""]

    if any(compte.values()):
        L += ["| Issue | Nombre |", "|---|---|"]
        L += [f"| {LIBELLE[s]} | {compte[s]} |" for s in STATUTS if compte[s]]
        L += [""]

    envoyees = [e for e in entrees if e.get("status") == "envoyee"]
    if envoyees:
        L += ["## Envoyées", ""]
        for e in envoyees:
            L.append(f"- {e.get('title')} — CV {e.get('cv')}")
        L += [""]

    if attente:
        L += ["## À reprendre à la main", ""]
        for a in attente:
            L.append(f"- {a['titre']}")
            L.append(f"  {a['motif']}")
            L.append(f"  {a['url']}")
        L += ["", "Ces candidatures ont été interrompues avant l'envoi. Le script",
              "n'invente jamais de réponse à une question qu'il ne reconnaît pas.", ""]

    tentes = {e.get("url") for e in entrees}
    non_tentees = [r for r in retenues if r.get("raw", {}).get("url") not in tentes]
    if non_tentees:
        L += ["## Retenues mais non tentées", ""]
        for r in non_tentees[:15]:
            m, raw = r.get("match", {}), r.get("raw", {})
            L.append(f"- [{m.get('decision_score')}] {m.get('title')} — {raw.get('url')}")
        if len(non_tentees) > 15:
            L.append(f"- … et {len(non_tentees) - 15} autres")
        L += [""]

    return "\n".join(L), {"compte": compte, "attente": attente,
                          "retenues": len(retenues), "tentees": len(entrees)}


def ecrire(day: str | None = None) -> tuple[str, str]:
    day = day or dt.date.today().isoformat()
    texte, brut = construire(day)
    d = jour_dir(day)
    os.makedirs(d, exist_ok=True)
    p_md = os.path.join(d, "rapport-matin.md")
    p_js = os.path.join(d, "file_attente.json")
    open(p_md, "w", encoding="utf-8").write(texte + "\n")
    json.dump(brut["attente"], open(p_js, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    return p_md, p_js


if __name__ == "__main__":
    a, b = ecrire(sys.argv[1] if len(sys.argv) > 1 else None)
    print(a)
    print(b)
