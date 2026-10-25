#!/usr/bin/env python3
"""Detached launcher for the WI-009b full-history contrastive training run.

Why detached
------------
The full-history CAD run is a long job on a 2 vCPU / 8 GB host with no swap. A
foreground agent-shell run can be killed mid-way and then looks "successful" if
only the tail of the log is read. This launcher therefore starts the training as
an independent process (`start_new_session=True`, so it survives the session),
writes everything to `logs/wi009b_train.out`, and returns the pid immediately.
The caller polls the log for the `EXIT:<code>` marker.

Log markers
-----------
    START  <iso timestamp> <argv>
    ...training output, including per-stage STEP ...: START/END lines...
    END    <iso timestamp>
    EXIT:<code>

Usage:
    uv run python scripts/wi009b_launch.py --epochs 20 --early-stop-patience 4 --val-dates 60
    uv run python scripts/wi009b_launch.py --status          # poll: is it still running?
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "logs" / "wi009b_train.out"
PIDFILE = ROOT / "logs" / "wi009b_train.pid"


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--status", action="store_true", help="Print the current log tail and exit.")
    ap.add_argument("--market", default="CAD")
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--early-stop-patience", type=int, default=4)
    ap.add_argument("--val-dates", type=int, default=60)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--grad-clip", type=float, default=1.0)
    ap.add_argument("--standardize", action="store_true")
    ap.add_argument("--report-prefix", default="wi009b")
    ap.add_argument("--tag", default="wi009b")
    ap.add_argument("--extra", default="", help="Extra flags passed through to the trainer.")
    return ap.parse_args()


def tail(path: Path, n: int = 25) -> None:
    if not path.exists():
        print(f"[launch] no log at {path}")
        return
    lines = path.read_text(errors="replace").splitlines()
    print("\n".join(lines[-n:]))


def status() -> int:
    pid = None
    if PIDFILE.exists():
        pid = int(PIDFILE.read_text().strip() or 0)
    running = False
    if pid:
        try:
            os.kill(pid, 0)
            running = True
        except OSError:
            running = False
    log_text = LOG.read_text(errors="replace") if LOG.exists() else ""
    print(f"[launch] pid={pid} running={running} log={LOG}")
    print(f"[launch] markers: START={log_text.count('START ')} END={log_text.count('END ')} "
          f"EXIT={log_text.count('EXIT:')}")
    tail(LOG, 25)
    return 0 if not running else 1


def main() -> int:
    args = parse_args()
    if args.status:
        return status()

    (ROOT / "logs").mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, "-u", "scripts/train_contrastive.py",
        "--market", args.market,
        "--epochs", str(args.epochs),
        "--early-stop-patience", str(args.early_stop_patience),
        "--val-dates", str(args.val_dates),
        "--lr", str(args.lr),
        "--grad-clip", str(args.grad_clip),
        "--report-prefix", args.report_prefix,
        "--tag", args.tag,
    ]
    if args.standardize:
        cmd.append("--standardize")
    if args.extra:
        cmd.extend(args.extra.split())

    env = dict(os.environ)
    env.update(
        {
            "OMP_NUM_THREADS": "2",
            "OPENBLAS_NUM_THREADS": "2",
            "MKL_NUM_THREADS": "2",
            "PYTHONUNBUFFERED": "1",
        }
    )

    # Wrap in a shell so the END/EXIT markers are written by the detached
    # process itself, not by this (short-lived) launcher.
    inner = " ".join(shlex.quote(c) for c in cmd)
    wrapper = f"{inner}; rc=$?; echo 'END '\"$(date -Is)\"; echo EXIT:$rc"
    shell_cmd = ["/bin/sh", "-c", wrapper]

    with LOG.open("a") as fh:
        fh.write(f"START {dt.datetime.now().isoformat()} {inner}\n")
        fh.flush()
        proc = subprocess.Popen(
            shell_cmd,
            cwd=str(ROOT),
            stdout=fh,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            env=env,
        )
    PIDFILE.write_text(f"{proc.pid}\n")
    print(f"[launch] started pid={proc.pid} → {LOG}")
    print(f"[launch] poll with: uv run python scripts/wi009b_launch.py --status")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())