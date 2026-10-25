#!/usr/bin/env bash
# notify_gate.sh — zero-token completion/gate watcher for the signals pipeline.
#
# Watches a log or plan file for a completion marker (regex). On first sight,
# posts ONE message to Discord via webhook (DISCORD_WEBHOOK_URL from .env —
# gitignored; never commit or paste the URL). State file prevents re-notify.
#
# No model tokens: this is pure shell + curl. Hermes only gets involved (PM
# cycle) after the human has been pinged.
#
# Usage (detached, survives the launcher — same Popen pattern as the chains):
#   setsid bash scripts/notify_gate.sh >> logs/notify_gate.out 2>&1 &
#   bash scripts/notify_gate.sh --file logs/wi009b_train.out \
#        --marker 'EXIT:0|EXIT:1' \
#        --message 'WI-009b training done — STATUS line written, run PM cycle'
#
# Or one-shot (for gate briefs that already exist):
#   bash scripts/notify_gate.sh --once --message 'WI-009b at QA/GATE — admin decision needed'
#
# Marker sources this repo uses: `EXIT:0` / `EXIT:1` in run logs;
# `STATUS: DONE|BLOCKED|ERROR` in plan files; gate decisions = PM posts.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FILE=""
MARKER=""
MESSAGE=""
INTERVAL=60          # poll cadence, seconds
MAX_WAIT=86400        # give up after 24h
ONCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --file)     FILE="$2"; shift 2 ;;
    --marker)   MARKER="$2"; shift 2 ;;
    --message)  MESSAGE="$2"; shift 2 ;;
    --interval) INTERVAL="$2"; shift 2 ;;
    --once)     ONCE=1; shift ;;
    *) echo "unknown flag: $1" >&2; exit 2 ;;
  esac
done

[[ -z "$MESSAGE" ]] && { echo "--message is required" >&2; exit 2; }

# Load DISCORD_WEBHOOK_URL from .env (never echoed).
WEBHOOK=""
if [[ -f "$ROOT/.env" ]]; then
  # shellcheck disable=SC1091
  WEBHOOK="$(grep -E '^DISCORD_WEBHOOK_URL=' "$ROOT/.env" | tail -1 | cut -d= -f2- || true)"
fi

post_discord() {
  if [[ -z "$WEBHOOK" ]]; then
    echo "[notify] NO WEBHOOK — DISCORD_WEBHOOK_URL missing from .env; message dropped:" >&2
    echo "[notify] $1" >&2
    return 1
  fi
  python3 - "$WEBHOOK" "$1" <<'PYEOF'
import json, sys, urllib.request
url, text = sys.argv[1], sys.argv[2]
data = json.dumps({"content": text}).encode()
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        print("[notify] discord POST ->", r.status)
except Exception as e:
    print(f"[notify] discord POST FAILED: {e}", file=sys.stderr); sys.exit(1)
PYEOF
}

if [[ "$ONCE" -eq 1 ]]; then
  post_discord "$MESSAGE"
  exit $?
fi

[[ -z "$FILE" || -z "$MARKER" ]] && { echo "--file and --marker required (or --once)" >&2; exit 2; }

STATE="$ROOT/logs/.notify_$(basename "$FILE").done"
[[ -f "$STATE" ]] && { echo "[notify] marker already seen (state $STATE) — nothing to do"; exit 0; }

echo "[notify] watching $FILE for /$MARKER/ every ${INTERVAL}s (max $MAX_WAIT s)"
waited=0
while (( waited < MAX_WAIT )); do
  if [[ -f "$FILE" ]] && grep -qE "$MARKER" "$FILE" 2>/dev/null; then
    echo "[notify] marker seen at t=${waited}s"
    if post_discord "$MESSAGE"; then
      date -u +%FT%TZ > "$STATE"
      echo "[notify] notified; state written to $STATE"
      exit 0
    else
      echo "[notify] webhook failed; retrying next cycle (no state written)" >&2
    fi
  fi
  sleep "$INTERVAL"; waited=$((waited + INTERVAL))
done
echo "[notify] gave up after ${waited}s without seeing /$MARKER/ in $FILE" >&2
exit 1