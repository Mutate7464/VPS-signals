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

Usage (WI-013: omitted `--market` launches BOTH, USD then CAD, sequentially)::

    uv run python scripts/wi009b_launch.py --epochs 20 --early-stop-patience 4 --val-dates 60
    uv run python scripts/wi009b_launch.py --market CAD      # one market
    uv run python scripts/wi009b_launch.py --status          # poll: is it still running?

Log/pid sidecars are market-suffixed: `logs/wi009b_train_{market}.out` / `.pid`.
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
LOGS = ROOT / "logs"
sys.path.insert(0, str(ROOT))

from src.market_cli import add_market_argument, cli_markets, run_markets  # noqa: E402


def launcher_paths(market: str) -> dict[str, Path]:
    """The launcher's log and pid sidecar for one market (WI-013)."""
    return {
        "log": LOGS / f"wi009b_train_{market}.out",
        "pid": LOGS / f"wi009b_train_{market}.pid",
    }


def paths(market: str) -> dict[str, Path]:
    """Every output path this launcher resolves for one market (its log/pid sidecars)."""
    return launcher_paths(market)


def build_parser() -> argparse.ArgumentParser:
    """The CLI parser for this entry point (one shared `--market` flag)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--status", action="store_true", help="Print the current log tail and exit.")
    add_market_argument(ap)
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--early-stop-patience", type=int, default=4)
    ap.add_argument("--val-dates", type=int, default=60)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--grad-clip", type=float, default=1.0)
    ap.add_argument("--standardize", action="store_true")
    ap.add_argument("--report-prefix", default="wi009b")
    ap.add_argument("--tag", default="wi009b")
    ap.add_argument("--extra", default="", help="Extra flags passed through to the trainer.")
    return ap


def parse_args(argv=None):
    return build_parser().parse_args(argv)


def tail(path: Path, n: int = 25) -> None:
    if not path.exists():
        print(f"[launch] no log at {path}")
        return
    lines = path.read_text(errors="replace").splitlines()
    print("\n".join(lines[-n:]))


def status(market: str) -> int:
    lp = launcher_paths(market)
    LOG, PIDFILE = lp["log"], lp["pid"]
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
    print(f"[launch] market={market} pid={pid} running={running} log={LOG}")
    print(f"[launch] markers: START={log_text.count('START ')} END={log_text.count('END ')} "
          f"EXIT={log_text.count('EXIT:')}")
    tail(LOG, 25)
    return 0 if not running else 1


def main(argv=None) -> int:
    args = parse_args(argv)
    markets = cli_markets(args.market, prog="wi009b_launch")
    if markets is None:
        return 2
    if args.status:
        return run_markets(markets, lambda m: status(m))
    print(f"[launch] PLAN: markets={', '.join(markets)} (sequential)")
    return launch(markets, args)


def launch(markets: list[str], args) -> int:
    """Start one detached process per market, chained sequentially."""
    LOGS.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update(
        {
            "OMP_NUM_THREADS": "2",
            "OPENBLAS_NUM_THREADS": "2",
            "MKL_NUM_THREADS": "2",
            "PYTHONUNBUFFERED": "1",
        }
    )

    parts: list[str] = []
    logs: list[Path] = []
    for market in markets:
        lp = launcher_paths(market)
        logs.append(lp["log"])
        cmd = [
            sys.executable, "-u", "scripts/train_contrastive.py",
            "--market", market,
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

        # Wrap in a shell so the END/EXIT markers are written by the detached
        # process itself, not by this (short-lived) launcher. Each market appends
        # to its own market-suffixed log (WI-013).
        inner = " ".join(shlex.quote(c) for c in cmd)
        with lp["log"].open("a") as fh:
            fh.write(f"START {dt.datetime.now().isoformat()} {inner}\n")
        parts.append(
            f"{{ {inner}; rc=$?; echo 'END '\"$(date -Is)\"; echo EXIT:$rc; }} "
            f">> {shlex.quote(str(lp['log']))} 2>&1"
        )
        lp["pid"].write_text("")

    proc = subprocess.Popen(
        ["/bin/sh", "-c", " ; ".join(parts)],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        env=env,
    )
    for market in markets:
        launcher_paths(market)["pid"].write_text(f"{proc.pid}\n")
    print(f"[launch] started pid={proc.pid} markets={' '.join(markets)} (sequential)")
    for log in logs:
        print(f"[launch] poll: uv run python scripts/wi009b_launch.py --market "
              f"{log.stem.rsplit('_', 1)[-1]} --status")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())