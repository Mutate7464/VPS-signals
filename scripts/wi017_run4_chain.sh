#!/usr/bin/env bash
# WI-017 run 4 chain: full alignment matrix (593 symbols, 5 folds)
set -uo pipefail
cd /home/yycuser/projects/signals
echo "=== wi017 run4 full grid start $(date -u +%FT%TZ)"
uv run python -m src.wi017.run4_alignment
rc=$?
echo "EXIT:$rc"
echo "=== wi017 run4 end $(date -u +%FT%TZ)"
exit $rc