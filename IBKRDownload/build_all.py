#!/usr/bin/env python3
"""All-in-one build pipeline: watchlist → IBKR download → sync to VPS.

Sequential execution across three stages:
  1. build_watchlist.py  — rebuild canonical watchlists from IV/TC/IBKRtemp sources
  2. ibkr_ingest.py      — download/update OHLCV data from IBKR (auto-scans sources)
  3. sync_back.py         — rsync data + configs to VPS via SSH

Usage:
  python build_all.py                     # full pipeline: USD + CAD + HOLDINGS
  python build_all.py --market USD        # single market only
  python build_all.py --delta-only        # fast daily delta update
  python build_all.py --dry-run           # preview without side effects
  python build_all.py --skip-sync         # skip VPS rsync
  python build_all.py --limit 5           # test with 5 tickers per market
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def _run_step(name: str, cmd: list[str], dry_run: bool = False) -> bool:
    """Run a subprocess step. Returns True on success."""
    tag = "[DRY RUN] " if dry_run else ""
    print(f"\n{'='*60}")
    print(f"STEP: {name}")
    print(f"{'='*60}")
    print(f"  {tag}$ {' '.join(cmd)}")
    print()

    if dry_run:
        return True

    result = subprocess.run(cmd, cwd=str(SCRIPT_DIR))
    ok = result.returncode == 0
    status = "✅ OK" if ok else f"❌ FAILED (exit {result.returncode})"
    print(f"\n  {name}: {status}")
    return ok


def main():
    parser = argparse.ArgumentParser(
        description="All-in-one: build watchlists → IBKR download → sync to VPS"
    )
    parser.add_argument(
        "--market", choices=["USD", "CAD", "HOLDINGS", "both"], default="both",
        help="Which market(s) to process (default: both = USD + CAD + HOLDINGS)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview all steps without side effects",
    )
    parser.add_argument(
        "--delta-only", action="store_true",
        help="Daily fast mode — skip Bulk/Mid downloads",
    )
    parser.add_argument(
        "--skip-sync", action="store_true",
        help="Run build + download but skip VPS rsync",
    )
    parser.add_argument(
        "--limit", type=int, default=0,
        help="Limit IBKR download to N tickers per market (testing)",
    )
    parser.add_argument(
        "--no-scan-sources", action="store_true",
        help="Disable auto-discovery of new tickers from IV/TC/IBKRtemp files",
    )
    args = parser.parse_args()

    markets: list[str]
    if args.market == "both":
        markets = ["USD", "CAD"]
    else:
        markets = [args.market]

    # Also process HOLDINGS if market=both or market=HOLDINGS
    include_holdings = args.market in ("both", "HOLDINGS")

    start_time = time.monotonic()
    errors: list[str] = []

    # ── Stage 1: Build Watchlists ──────────────────────────────────────
    for mkt in markets:
        cmd = [
            sys.executable, str(SCRIPT_DIR / "build_watchlist.py"),
            "--market", mkt,
            "--base-dir", str(SCRIPT_DIR.parent),
        ]
        if args.dry_run:
            cmd.append("--dry-run")
        if not _run_step(f"build_watchlist ({mkt})", cmd, dry_run=args.dry_run):
            errors.append(f"build_watchlist:{mkt}")
            if not args.dry_run:
                print("\n❌ Watchlist build failed — aborting pipeline.")
                sys.exit(1)

    # ── Stage 2: IBKR Ingest ───────────────────────────────────────────
    ingest_base = [
        sys.executable, str(SCRIPT_DIR / "ibkr_ingest.py"),
    ]
    if args.dry_run:
        ingest_base.append("--dry-run")
    if args.delta_only:
        ingest_base.append("--delta-only")
    if args.limit > 0:
        ingest_base.extend(["--limit", str(args.limit)])
    if args.no_scan_sources:
        ingest_base.append("--no-scan-sources")

    for mkt in markets:
        cmd = ingest_base + ["--market", mkt]
        if not _run_step(f"ibkr_ingest ({mkt})", cmd, dry_run=args.dry_run):
            errors.append(f"ibkr_ingest:{mkt}")

    if include_holdings:
        cmd = ingest_base + ["--market", "HOLDINGS"]
        if not _run_step("ibkr_ingest (HOLDINGS)", cmd, dry_run=args.dry_run):
            errors.append("ibkr_ingest:HOLDINGS")

    # Check if any download had hard failures
    download_failures = [e for e in errors if e.startswith("ibkr_ingest:")]
    if download_failures and not args.dry_run:
        print(f"\n⚠️  {len(download_failures)} download(s) had errors: {download_failures}")
        if not args.skip_sync:
            print("   Skipping sync due to download errors.")

    # ── Stage 3: Sync to VPS ───────────────────────────────────────────
    if not args.skip_sync and not download_failures:
        sync_cmd = [
            sys.executable, str(SCRIPT_DIR / "sync_back.py"),
        ]
        if args.dry_run:
            sync_cmd.append("--dry-run")
        if not _run_step("sync_back (VPS)", sync_cmd, dry_run=args.dry_run):
            errors.append("sync_back")
    elif args.skip_sync:
        print("\n  --skip-sync: skipping VPS rsync")
    else:
        print("\n  Skipping sync (download errors)")

    # ── Summary ────────────────────────────────────────────────────────
    elapsed = time.monotonic() - start_time
    print(f"\n{'='*60}")
    if errors:
        print(f"Pipeline complete with {len(errors)} error(s) in {elapsed:.0f}s:")
        for e in errors:
            print(f"  ❌ {e}")
        sys.exit(1)
    else:
        tag = "[DRY RUN] " if args.dry_run else ""
        print(f"{tag}Pipeline complete ✅  ({elapsed:.0f}s)")
        print(f"  Markets: {markets}")
        if include_holdings:
            print(f"  Holdings: included")
        print(f"  Sync: {'skipped' if args.skip_sync else 'enabled'}")


if __name__ == "__main__":
    main()