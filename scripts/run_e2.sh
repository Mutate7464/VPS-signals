#!/usr/bin/env bash
# run_e2.sh — Launch the E2 pipeline re-run (USD on real data).
# Stops hermes-gateway during the run; restarts on completion or failure.
# Usage:
#   bash scripts/run_e2.sh --market USD --min-date 2016-01-01 --placebo-seeds 1
#   bash scripts/run_e2.sh --dry-run                    # fixture, no service stop
#   bash scripts/run_e2.sh --dry-run --simulate-fail    # test the trap
#   bash scripts/run_e2.sh --service-test               # round-trip hermes stop/start

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
RUN_LOG="$PROJECT_DIR/logs/e2_run.out"
mkdir -p "$PROJECT_DIR/logs"

DRY_RUN=false
SIMULATE_FAIL=false
NO_STOP=false
SERVICE_TEST=false
RESTART_OPENCODE=false
MARKET="USD"
MIN_DATE="2016-01-01"
PLACEBO_SEEDS=1

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --simulate-fail) SIMULATE_FAIL=true ;;
        --no-stop) NO_STOP=true ;;
        --service-test) SERVICE_TEST=true ;;
        --restart-opencode) RESTART_OPENCODE=true ;;
        --market) shift; MARKET="$1"; shift || true ;;
        --market=*) MARKET="${arg#*=}" ;;
        --min-date) shift; MIN_DATE="$1"; shift || true ;;
        --min-date=*) MIN_DATE="${arg#*=}" ;;
        --placebo-seeds) shift; PLACEBO_SEEDS="$1"; shift || true ;;
        --placebo-seeds=*) PLACEBO_SEEDS="${arg#*=}" ;;
        *) ;;
    esac
    # handle --market=USD style
    if [[ "$arg" == --market=* ]]; then
        MARKET="${arg#*=}"
    fi
done

log() { echo "[e2 $(date '+%H:%M:%S')] $*" | tee -a "$RUN_LOG"; }

# --------------------------------------------------------------------
# Trap cleanup
# --------------------------------------------------------------------
cleanup() {
    local exit_code=$?
    log "cleanup — exit code $exit_code"
    log "free -m:"; free -m | head -2 >> "$RUN_LOG" 2>/dev/null || true
    if [ "$NO_STOP" = false ] && [ "$SERVICE_TEST" = false ] || [ "$SERVICE_TEST" = true ]; then
        log "restarting hermes-gateway..."
        systemctl --user start hermes-gateway 2>&1 | tee -a "$RUN_LOG" || log "WARNING: hermes-gateway restart failed"
        sleep 3
        systemctl --user is-active hermes-gateway && log "hermes-gateway: active" || log "WARNING: hermes-gateway not active"
    fi
    if [ "$RESTART_OPENCODE" = true ] && [ "$NO_STOP" = false ]; then
        log "restarting opencode serve..."
        nohup "$HOME/.opencode/bin/opencode" serve --service >/dev/null 2>&1 &
        log "opencode serve: restarted (pid $!)"
    else
        log "opencode serve not auto-restarted. Reopen manually."
    fi
    log "done"
}
trap cleanup EXIT

# --------------------------------------------------------------------
# Service test
# --------------------------------------------------------------------
if [ "$SERVICE_TEST" = true ]; then
    log "SERVICE TEST: stopping hermes-gateway..."
    systemctl --user stop hermes-gateway
    sleep 5
    if pgrep -f ".hermes/tools/python" >/dev/null; then
        log "WARNING: hermes python workers still running after stop"
    else
        log "hermes workers stopped"
    fi
    # trap will restart
    if [ "$SIMULATE_FAIL" = true ]; then
        exit 99
    fi
    exit 0
fi

# --------------------------------------------------------------------
# Dry run
# --------------------------------------------------------------------
if [ "$DRY_RUN" = true ]; then
    log "DRY RUN — using fixture data, no service stop"
    export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONUNBUFFERED=1
    cd "$PROJECT_DIR"
    if ! uv run python scripts/e2_preflight.py --market "$MARKET" --min-date "$MIN_DATE"; then
        log "preflight FAILED"; exit 1
    fi
    uv run python -m src.stat_metadata --market "$MARKET" || log "stat_metadata FAILED"
    if [ "$SIMULATE_FAIL" = true ]; then
        log "simulating failure"; exit 99
    fi
    uv run python -m src.model_qa --market "$MARKET" || log "model_qa FAILED"
    log "dry run complete"
    exit 0
fi

# --------------------------------------------------------------------
# Real run
# --------------------------------------------------------------------
log "E2 REAL RUN  market=$MARKET  min_date=$MIN_DATE  placebo_seeds=$PLACEBO_SEEDS"
log "free -m:"
free -m >> "$RUN_LOG"
log "top memory processes:"
ps aux --sort=-rss | head -6 >> "$RUN_LOG"

if [ "$NO_STOP" = false ]; then
    log "stopping hermes-gateway..."
    systemctl --user stop hermes-gateway
    sleep 5
    # Wait up to 30s for hermes workers to exit
    for i in $(seq 1 6); do
        if pgrep -f ".hermes/tools/python" >/dev/null; then
            log "waiting for hermes workers... ($((i*5))s)"
            sleep 5
        else
            log "hermes workers exited"
            break
        fi
    done
    if pgrep -f ".hermes/tools/python" >/dev/null; then
        log "WARNING: hermes workers still running — proceeding anyway"
    fi
fi

# Memory cgroup cap
USE_CGROUP=false
if systemd-run --user --scope true 2>/dev/null; then
    USE_CGROUP=true
    log "systemd-run cgroup available — MemoryMax=5500M"
else
    log "systemd-run not available — relying on in-code memory guard"
fi

export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONUNBUFFERED=1
cd "$PROJECT_DIR"

run_step() {
    local name="$1"; shift
    log "=== STEP: $name ==="
    if $USE_CGROUP; then
        systemd-run --user --scope -p MemoryMax=5500M -p MemorySwapMax=0 \
            /usr/bin/time -v "$@" 2>&1 | tee -a "$RUN_LOG"
    else
        /usr/bin/time -v "$@" 2>&1 | tee -a "$RUN_LOG"
    fi
    local rc=${PIPESTATUS[0]}
    if [ "$rc" -ne 0 ]; then
        log "ERROR: $name failed (exit $rc)"
        return 1
    fi
    log "$name: OK"
}

run_step "preflight" uv run python scripts/e2_preflight.py --market "$MARKET" --min-date "$MIN_DATE" || exit 1
run_step "feature_engine" uv run python -m src.feature_engine --market "$MARKET" --min-date "$MIN_DATE" || exit 1
run_step "stat_metadata" uv run python -m src.stat_metadata --market "$MARKET" || exit 1
run_step "xgb_trainer" uv run python -m src.xgb_trainer --market "$MARKET" --min-date "$MIN_DATE" --placebo-seeds "$PLACEBO_SEEDS" || exit 1
run_step "model_qa" uv run python -m src.model_qa --market "$MARKET" || exit 1

log "E2 RUN COMPLETE — SUCCESS"
log "=== free -m ==="
free -m | tee -a "$RUN_LOG"
exit 0