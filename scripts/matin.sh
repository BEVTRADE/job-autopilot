#!/usr/bin/env bash
# Exécution du matin : collecte, candidatures, rapport.
#
#   scripts/matin.sh                 simulation, rien n'est envoyé
#   scripts/matin.sh --envoyer       envoi réel
#
# Arrêt d'urgence à tout moment :  touch ~/.job-autopilot/STOP
set -uo pipefail

RACINE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RACINE"

PY="$RACINE/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"

JOUR="$(date +%F)"
LOGS="$RACINE/data/logs"
mkdir -p "$LOGS"
LOG="$LOGS/$JOUR.log"

ENVOYER=""
MAX="${MAX:-3}"
MIN_FIT="${MIN_FIT:-70}"
CV="${CV:-}"   # vide : le CV est choisi par mission
[ "${1:-}" = "--envoyer" ] && ENVOYER="--envoyer"

trace() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

if [ -e "$HOME/.job-autopilot/STOP" ]; then
  trace "kill-switch présent — arrêt immédiat"
  exit 0
fi

VERROU="$HOME/.job-autopilot/verrou"
mkdir -p "$HOME/.job-autopilot"
if ! mkdir "$VERROU" 2>/dev/null; then
  trace "une exécution est déjà en cours ($VERROU) — arrêt"
  exit 0
fi
trap 'rmdir "$VERROU" 2>/dev/null' EXIT

trace "=== job-autopilot, $JOUR, ${ENVOYER:-simulation} ==="

trace "1/3 collecte"
if ! "$PY" scripts/collect.py --source freework --limit 200 --delay 0.8 >>"$LOG" 2>&1; then
  trace "collecte en échec — voir $LOG"
fi

RETENUES="$RACINE/data/output/$JOUR/retenues.json"
if [ ! -s "$RETENUES" ]; then
  trace "aucune mission retenue aujourd'hui — pas de candidature"
else
  NB="$("$PY" -c "import json,sys; print(len(json.load(open(sys.argv[1]))))" "$RETENUES")"
  trace "2/3 candidatures — $NB retenue(s), plafond $MAX, fit minimal $MIN_FIT"
  if ! "$PY" scripts/apply.py --from "$RETENUES" --max "$MAX" \
        --min-fit "$MIN_FIT" ${CV:+--cv "$CV"} $ENVOYER >>"$LOG" 2>&1; then
    trace "soumission en échec — voir $LOG"
  fi
fi

trace "3/3 rapport"
"$PY" -m src.report.digest "$JOUR" >>"$LOG" 2>&1 || trace "rapport en échec"

RAPPORT="$RACINE/data/output/$JOUR/rapport-matin.md"
if [ -f "$RAPPORT" ]; then
  trace "rapport : $RAPPORT"
  command -v open >/dev/null && [ -z "${SANS_OUVERTURE:-}" ] && open "$RAPPORT" || true
fi
"$PY" -m src.report.notify "$JOUR" >>"$LOG" 2>&1 || true
trace "=== fin ==="
