#!/usr/bin/env bash
# fib overnight chain (2026-11-06) — deterministic orchestrator.
# The model (GLM via opencode surgical-builder) ONLY writes code+tests for one WI per session.
# Everything else — staging, locks, manifest audit, smoke/full runs, golden-value checks,
# local commits (never pushed), stop decisions — is done here by shell, not by the model.
#
# Launch (repo root):  bash docs/workflow/briefs/2026-11-06-fib-overnight/chain.sh
# Dry run:             DRY_RUN=1 bash docs/workflow/briefs/2026-11-06-fib-overnight/chain.sh
# Options: MODEL=openrouter/z-ai/glm-5.3 (default) · START_AT=WI-023 (resume after a stop)
set -uo pipefail
cd /home/yycuser/projects/signals || exit 1

MODEL="${MODEL:-openrouter/z-ai/glm-5.3}"
DRY="${DRY_RUN:-0}"
START_AT="${START_AT:-WI-021}"
OC=/home/yycuser/.opencode/bin/opencode
B=docs/workflow/briefs/2026-11-06-fib-overnight
OUT=reports/fib_swings
LOG=logs/fib_overnight
SCR=/home/yycuser/.hermes/cache/scratch/fib_overnight_smoke
SMOKE=AAPL,MSFT,NVDA,JPM,XOM,RY,TD,SHOP,CNQ,ENB
U="uv run python $B/chain_util.py"
REPORT="$OUT/OVERNIGHT_REPORT.md"
[ "$DRY" = 1 ] && REPORT=/dev/null
mkdir -p "$LOG"

WIS=(WI-021-fib-pass4-accounting-fix WI-023-fib-trade-labels-exit-grid WI-022-fib-regime-overlay WI-024-fib-meta-label WI-025-fib-quantile-magnitude)
declare -A RUN=(
  [WI-021]="scripts/fib_walkforward.py"
  [WI-023]="scripts/fib_trade_labels.py"
  [WI-022]="scripts/fib_regime_overlay.py"
  [WI-024]="scripts/fib_event_features.py scripts/fib_meta_model.py"
  [WI-025]="scripts/fib_quantile_model.py"
)

say() { echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG/chain.out"; }
do_() { if [ "$DRY" = 1 ]; then say "DRY: $*"; else "$@"; fi; }
wipath() { ls docs/kanban/*/"$1".md 2>/dev/null | head -1; }

PROMPT_BASE='Execute docs/kanban/in_progress/%s.md strictly within its locked file manifest (write_files). Read ONLY that WI file and the files listed under read_only_files. Implement Section 2 literally: every formula, constant, column name, file name, threshold and date in it is fixed - never substitute your own, never add features, never tune parameters, never change thresholds. Tests use synthetic data only. Do NOT run the full-universe job and do NOT read files under data/ or large files under reports/. Run the exact test_command until it exits 0 (max one fix attempt after a failure), append the Execution Telemetry footer to the WI file, then stop with a 2-line summary.'

# ---- preflight ----
[ -x "$OC" ] || { say "PREFLIGHT FAIL: opencode missing"; exit 1; }
git diff --cached --quiet || { say "PREFLIGHT FAIL: index has staged changes — commit or unstage first"; exit 1; }
for f in "${WIS[@]}"; do [ -n "$(wipath "$f")" ] || { say "PREFLIGHT FAIL: $f.md not found"; exit 1; }; done

build() {  # $1=WI-id $2=file-stem $3=attempt $4=failure-text ; rc 2 = manifest violation
  local p wif; p=$(printf "$PROMPT_BASE" "$2"); wif=$(wipath "$2")
  if [ -n "${4:-}" ]; then p="$p

PREVIOUS ATTEMPT FAILED. Your code is still on disk. Fix ONLY this failure, change nothing else:
$4"; fi
  say "$1 build attempt $3 (model $MODEL)"
  $U snapshot "$LOG/$1.pre$3.json"
  do_ timeout 5400 "$OC" run --agent surgical-builder -m "$MODEL" --auto --format json --title "$1-a$3" "$p" > "$LOG/$1.build$3.jsonl" 2>&1
  say "$1 build attempt $3 exited $?"
  if ! $U audit "$LOG/$1.pre$3.json" "$wif" "$wif" > "$LOG/$1.audit$3.txt"; then
    say "$1 MANIFEST VIOLATION: $(cat "$LOG/$1.audit$3.txt")"; return 2
  fi
  return 0
}

verify() {  # $1=WI-id $2=file-stem ; writes $LOG/$1.fail on failure ; rc 0 = accept
  local wi=$1 f=$2 tc wif s; wif=$(wipath "$f")
  tc=$(grep '^test_command:' "$wif" | sed 's/^test_command: //')
  if [ "$DRY" = 1 ]; then say "DRY: $tc ; smoke+full: ${RUN[$wi]} ; checks.py $wi"; return 0; fi
  bash -c "$tc" > "$LOG/$wi.test.out" 2>&1 || { { echo "TEST FAILED: $tc"; tail -25 "$LOG/$wi.test.out"; } > "$LOG/$wi.fail"; say "$wi tests FAILED"; return 1; }
  say "$wi tests passed"
  rm -rf "$SCR"; mkdir -p "$SCR"
  find "$OUT" -maxdepth 1 -type f \( -name '*.csv' -o -name '*.json' -o -name '*.parquet' \) -exec cp {} "$SCR/" \;
  for s in ${RUN[$wi]}; do
    FIB_SMOKE=$SMOKE timeout 900 uv run python "$s" --out "$SCR" > "$LOG/$wi.smoke.out" 2>&1
    grep -q 'EXIT:0' "$LOG/$wi.smoke.out" || { { echo "SMOKE RUN FAILED: FIB_SMOKE=$SMOKE uv run python $s --out <scratch dir>"; tail -25 "$LOG/$wi.smoke.out"; } > "$LOG/$wi.fail"; say "$wi smoke FAILED ($s)"; return 1; }
  done
  say "$wi smoke passed"
  for s in ${RUN[$wi]}; do
    /usr/bin/time -v timeout 2400 uv run python "$s" --out "$OUT" > "$LOG/$wi.full.out" 2>&1
    grep -q 'EXIT:0' "$LOG/$wi.full.out" || { { echo "FULL RUN FAILED: uv run python $s --out $OUT"; grep -v '^\s' "$LOG/$wi.full.out" | tail -25; } > "$LOG/$wi.fail"; say "$wi full run FAILED ($s)"; return 1; }
    say "$wi full $s: $(grep -E 'Elapsed|Maximum resident' "$LOG/$wi.full.out" | tr -s ' ' | tr '\n' ';')"
  done
  if ! uv run python "$B/checks.py" "$wi" "$OUT" > "$LOG/$wi.check.out" 2>&1; then
    { echo "ACCEPTANCE CHECK REJECTED (golden values in the WI). From $REPORT:"; awk "/^## $wi /{p=1} p" "$REPORT" | tail -20; } > "$LOG/$wi.fail"
    say "$wi acceptance REJECT"; return 1
  fi
  say "$wi acceptance ACCEPT"; return 0
}

# ---- setup: back up pass-4 outputs once; commit staging docs once ----
if [ ! -d "$OUT/_pass4_v1" ]; then
  do_ mkdir -p "$OUT/_pass4_v1"
  for x in trailing_events_w39.csv walkforward_validation.csv precision_at10.csv rally_grade_priors.csv; do do_ cp -p "$OUT/$x" "$OUT/_pass4_v1/"; done
  say "pass-4 outputs backed up to $OUT/_pass4_v1/"
fi
if [ -n "$(git status --porcelain -- docs/kanban/draft "$B" docs/tech_approach/fib_swings)" ]; then
  do_ git add docs/kanban/draft "$B" docs/tech_approach/fib_swings
  do_ git commit -q -m "docs(fib): overnight chain brief, WI-021..025 drafts, P1 design + test plan"
  say "setup commit done"
fi
echo -e "\n# Fib overnight chain — started $(date -u +%FT%TZ), model $MODEL" >> "$REPORT"

STATUS=ALL_DONE
started=0
for f in "${WIS[@]}"; do
  wi=${f:0:6}
  [ "$wi" = "$START_AT" ] && started=1
  [ $started = 1 ] || { say "$wi skipped (START_AT=$START_AT)"; continue; }
  case "$(wipath "$f")" in
    */done/*) say "$wi already done — skipping"; continue ;;
    */in_progress/*) ;;
    *) do_ git mv "$(wipath "$f")" "docs/kanban/in_progress/$f.md" ;;
  esac
  if [ "$DRY" != 1 ]; then $U lock add "$wi" "$(wipath "$f")" > /dev/null || { STATUS="BLOCKED_LOCK_$wi"; say "$wi lock clash"; break; }; fi
  ok=0
  for a in 1 2; do
    failtxt=""; [ $a = 2 ] && failtxt=$(cat "$LOG/$wi.fail" 2>/dev/null)
    build "$wi" "$f" "$a" "$failtxt"; rc=$?
    [ $rc = 2 ] && { cp "$LOG/$wi.audit$a.txt" "$LOG/$wi.fail"; break; }   # manifest violation: no retry
    if verify "$wi" "$f"; then ok=1; break; fi
  done
  mapfile -t wf < <($U manifest "$(wipath "$f")")
  if [ $ok = 1 ]; then
    do_ git mv "$(wipath "$f")" "docs/kanban/done/$f.md"
    do_ git add "${wf[@]}" "docs/kanban/done/$f.md"
    do_ git commit -q -m "feat($wi): $(grep '^title:' "$(wipath "$f")" | sed 's/^title: //') [overnight chain; PM review pending]"
    say "$wi DONE committed $(git rev-parse --short HEAD)"
    [ "$DRY" != 1 ] && $U lock release "$wi" > /dev/null
  else
    if [ "$DRY" != 1 ]; then
      { echo; echo "## BLOCKED by overnight chain $(date -u +%FT%TZ)"; echo '```'; cat "$LOG/$wi.fail" 2>/dev/null; echo '```'; } >> "$(wipath "$f")"
      git mv "$(wipath "$f")" "docs/kanban/blocked/$f.md"
      $U lock release "$wi" > /dev/null
    fi
    say "$wi BLOCKED (uncommitted code left on disk for review: ${wf[*]})"
    echo -e "\n## $wi — BLOCKED (see docs/kanban/blocked/$f.md)" >> "$REPORT"
    STATUS="BLOCKED_AT_$wi"; break
  fi
done

echo -e "\n**Chain finished $(date -u +%FT%TZ): $STATUS** — local commits only, no pushes, no BOARD edits; PM review pending." >> "$REPORT"
say "CHAIN $STATUS"
[ "$DRY" != 1 ] && bash scripts/notify_gate.sh --once --message "fib overnight chain: $STATUS — see reports/fib_swings/OVERNIGHT_REPORT.md" >> "$LOG/chain.out" 2>&1
echo "EXIT:0 $STATUS" >> "$LOG/chain.out"
