#!/usr/bin/env bash
# E3 ablation matrix — detached long-running chain (WI-002 plan Steps 4b+6).
set -u
cd ~/projects/signals
for fs in full no_static fib_only legacy19 cs_pct_only; do
  echo "=== feature-set: $fs $(date +%H:%M:%S) ==="
  uv run python -m src.xgb_trainer --market USD --min-date 2016-01-01 \
    --placebo-seeds 3 --feature-set "$fs" --resume || echo "FAILED: $fs"
done
echo "=== E3 CHAIN COMPLETE $(date +%H:%M:%S) ==="
