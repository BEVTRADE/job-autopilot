#!/usr/bin/env bash
# Installation, à lancer une fois depuis le Terminal macOS.
set -e
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt   # playwright, python-docx, mcp<2, docx-mcp-server…
.venv/bin/playwright install chromium
mkdir -p ~/.job-autopilot
echo
echo "Installé. Connexion Free-Work, une seule fois :"
echo "  .venv/bin/python scripts/apply.py --login"
echo
echo "Puis, en simulation :"
echo "  .venv/bin/python scripts/apply.py --from data/live/contact_scored.json --max 3"
echo
echo "Arrêt d'urgence à tout moment :  touch ~/.job-autopilot/STOP"
