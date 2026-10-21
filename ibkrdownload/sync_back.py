#!/usr/bin/env python3
"""sync_back.py — Push downloaded data and updated configs from M1 Mac → VPS.

Uses rsync over SSH. Assumes an SSH alias `VPS` is configured on the Mac
(e.g., in ~/.ssh/config) pointing to the Hostinger VPS.

Usage:
  python sync_back.py --dry-run     # preview what would be synced
  python sync_back.py               # push data to VPS
  python sync_back.py --data-only   # sync only OHLCV data (skip configs)
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

import yaml


def load_config() -> dict:
    cfg_path = Path(__file__).resolve().parent / "settings.yaml"
    with open(cfg_path) as f:
        return yaml.safe_load(f)


def rsync(src: str, dst: str, dry_run: bool = False, delete: bool = False) -> bool:
    """Run rsync. Returns True on success."""
    cmd = ["rsync", "-avz", "--progress"]
    if dry_run:
        cmd.append("--dry-run")
    if delete:
        cmd.append("--delete")
    cmd.extend([src, dst])
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Sync ingest data from M1 Mac → VPS")
    parser.add_argument("--dry-run", action="store_true", help="Preview without copying")
    parser.add_argument("--data-only", action="store_true", help="Sync only OHLCV data (skip configs)")
    args = parser.parse_args()

    cfg = load_config()
    sync_cfg = cfg.get("sync", {})
    vps_alias = sync_cfg.get("vps_alias", "VPS")
    vps_path = sync_cfg.get("vps_project_path", "~/projects/signals")

    base_dir = Path(cfg["project"]["base_dir"]).resolve()
    vps_target = f"{vps_alias}:{vps_path}"

    print(f"Syncing from: {base_dir}")
    print(f"Syncing to:   {vps_target}")
    print(f"Mode:         {'DRY RUN' if args.dry_run else 'LIVE'}")
    print()

    errors = []

    # ---- 1. OHLCV Parquet data ----
    ohlcv_src = base_dir / "data" / "raw_ohlcv"
    if ohlcv_src.exists() and any(ohlcv_src.iterdir()):
        print("── OHLCV data ──")
        # Sync market=USD/ and market=CAD/ directories
        for market_dir in ohlcv_src.iterdir():
            if market_dir.is_dir():
                src = str(market_dir) + "/"
                dst = f"{vps_target}/data/raw_ohlcv/{market_dir.name}/"
                if not rsync(src, dst, dry_run=args.dry_run):
                    errors.append(f"OHLCV: {market_dir.name}")
    else:
        print("── OHLCV data ──  (empty — nothing to sync)")

    # ---- 2. Pacing profiles ----
    pacing_src = base_dir / "data" / "pacing_profile_*.json"
    pacing_dir = base_dir / "data"
    if pacing_dir.exists() and list(pacing_dir.glob("pacing_profile_*.json")):
        print("── Pacing profiles ──")
        src = str(base_dir / "data" / "pacing_profile_*.json")
        dst = f"{vps_target}/data/"
        if not rsync(src, dst, dry_run=args.dry_run):
            errors.append("Pacing profiles")

    # ---- 3. Audit CSVs ----
    audit_files = list(base_dir.glob("data/audit_ingestion_*.csv"))
    if audit_files:
        print("── Audit logs ──")
        src = str(base_dir / "data" / "audit_ingestion_*.csv")
        dst = f"{vps_target}/data/"
        if not rsync(src, dst, dry_run=args.dry_run):
            errors.append("Audit logs")

    if args.data_only:
        print("\n--data-only: skipping config sync")
    else:
        # ---- 4. Watchlists (if updated) ----
        print("── Watchlists ──")
        for wl in ["watchlist_300_usd.csv", "watchlist_300_cad.csv", "holdings.csv"]:
            local_wl = base_dir / wl
            if local_wl.exists():
                dst = f"{vps_target}/config/{wl}"
                if not rsync(str(local_wl), dst, dry_run=args.dry_run):
                    errors.append(wl)

        # ---- 5. Sector map ----
        sector_local = base_dir / "sector_map.csv"
        if sector_local.exists():
            print("── Sector map ──")
            dst = f"{vps_target}/config/sector_map.csv"
            if not rsync(str(sector_local), dst, dry_run=args.dry_run):
                errors.append("sector_map.csv")

    print()
    if errors:
        print(f"❌ {len(errors)} sync errors: {', '.join(errors)}")
        sys.exit(1)
    else:
        tag = "[DRY RUN] " if args.dry_run else ""
        print(f"✅ {tag}Sync complete.")


if __name__ == "__main__":
    main()