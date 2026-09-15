#!/usr/bin/env bash
# Tests hors ligne : aucun réseau, aucun navigateur, aucune candidature.
set -uo pipefail
RACINE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RACINE"
PY="$RACINE/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"

if "$PY" -c "import pytest" 2>/dev/null; then
  exec "$PY" -m pytest tests -q
fi

echo "pytest absent, exécution directe des tests"
ECHECS=0
for f in tests/test_*.py; do
  MOD="$(basename "$f" .py)"
  "$PY" - "$MOD" <<'EOF' || ECHECS=$((ECHECS+1))
import importlib, sys, traceback
mod = importlib.import_module("tests." + sys.argv[1])
noms = [n for n in dir(mod) if n.startswith("test_")]
rates = []
for n in noms:
    try:
        getattr(mod, n)()
        print(f"  ok   {n}")
    except Exception:
        rates.append(n)
        print(f"  ÉCHEC {n}")
        traceback.print_exc()
print(f"{sys.argv[1]} : {len(noms) - len(rates)}/{len(noms)}")
sys.exit(1 if rates else 0)
EOF
done
[ "$ECHECS" -eq 0 ] && echo "tous les tests passent" || echo "$ECHECS fichier(s) en échec"
exit "$ECHECS"
