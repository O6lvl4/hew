#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
compiler="${ALMIDE_BIN:-almide}"
"$compiler" test
"$compiler" build
python3 ci/smoke.py
python3 ci/providers.py

# A ratchet, not a target: the lowest of any repository here, and the one worth defending.
# It is only ever allowed to go down. Raising it needs a reason written beside it.
if command -v codopsy-almd >/dev/null; then
  codopsy-almd --quiet --max 12 src/
else
  echo "codopsy-almd not on PATH: structural check skipped (almide install github.com/O6lvl4/codopsy-almd)"
fi
