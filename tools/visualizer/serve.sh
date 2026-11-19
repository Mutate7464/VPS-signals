#!/usr/bin/env bash
# Visualizer server (WI-085). One gunicorn worker, 2 threads, bound to 127.0.0.1.
# Reach it through an SSH tunnel:  ssh -N -L 8050:127.0.0.1:8050 <vps>
# The process is read-only over data/ and writes only under state/viz/.
set -euo pipefail

cd "$(dirname "$0")/../.."

HOST="${VIZ_HOST:-127.0.0.1}"
PORT="${VIZ_PORT:-8050}"

exec uv run gunicorn \
  --workers 1 \
  --threads 2 \
  --bind "${HOST}:${PORT}" \
  --timeout 120 \
  --access-logfile - \
  src.visualizer.app:server
