"""Notification de fin d'exécution. macOS si disponible, sinon sortie standard.

    python3 -m src.report.notify              # aujourd'hui
    python3 -m src.report.notify 2026-09-19
"""
from __future__ import annotations
import datetime as dt, shutil, subprocess, sys

from src.report import digest

A_TRAITER = ("session_expiree", "bloquee", "echec")


def message(compte: dict, retenues: int) -> tuple[str, str, bool]:
    """(titre, corps, urgent). Urgent quand une action humaine est requise."""
    if compte.get("session_expiree"):
        return ("Radar : session expirée",
                "Aucune candidature tentée. Relancer make login.", True)
    env, sim = compte.get("envoyee", 0), compte.get("simulee", 0)
    bloq = compte.get("bloquee", 0) + compte.get("echec", 0)
    morceaux = []
    if env:
        morceaux.append(f"{env} envoyée{'s' if env > 1 else ''}")
    if sim:
        morceaux.append(f"{sim} simulée{'s' if sim > 1 else ''}")
    if bloq:
        morceaux.append(f"{bloq} à reprendre")
    if not morceaux:
        morceaux.append(f"{retenues} retenue{'s' if retenues > 1 else ''}, aucune tentée")
    titre = "Radar : action requise" if bloq else "Radar du matin"
    return titre, " · ".join(morceaux), bool(bloq)


def envoyer(titre: str, corps: str, urgent: bool) -> str:
    if shutil.which("osascript"):
        son = ' sound name "Basso"' if urgent else ""
        t = titre.replace('"', "'"); c = corps.replace('"', "'")
        subprocess.run(["osascript", "-e",
                        f'display notification "{c}" with title "{t}"{son}'],
                       check=False, capture_output=True)
        return "macos"
    print(f"[{titre}] {corps}")
    return "stdout"


def main(day: str | None = None) -> None:
    day = day or dt.date.today().isoformat()
    _, brut = digest.construire(day)
    envoyer(*message(brut["compte"], brut["retenues"]))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
