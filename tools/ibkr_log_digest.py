#!/usr/bin/env python
"""IBKR API log digester — stream-parse -> template-mine -> flag issues.

Input: one or more IBKR exported API log files (api.<clientId>.* logs).
Format handled (line-based, never full-load):
    HH:MM:SS:mmm (sync HH:MM:SS:mmm) -> [field;field;...]
Direction markers: `->` (TWS->client), `<-` (client->TWS).
First payload field is the IBKR message ID (numeric); known error IDs get
flagged. Output: template table (counts + 1 sample, redacted) as CSV,
plus a JSON summary of flagged/unusual lines.

Usage:
    uv run python tools/ibkr_log_digest.py LOGFILE... [--csv out.csv] [--json out.json]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

GATEWAY_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s+(TRACE|DEBUG|INFO|WARN|ERROR|FATAL)\s+\[([^\]]+)\]\s+-\s?(.*)$"
)
LINE_RE = re.compile(
    r"^(\d{2}:\d{2}:\d{2}:\d{3})\s+[\((]?sync\s+[\d:]+[\))]?\s+(-[<>]|[<>]-)\s*\[?(.*)\]?\s*$"
)
# IBKR API error message IDs: 4 (error code in 3rd field), 5 (not-valid warnings)
ERROR_ID = {"4"}
# Error codes that are noise vs. real issues (IBKR error-code conventions)
NOISE_CODES = {"2100", "2103", "2104", "2106", "2107", "2108",
               "2109", "2119", "2158", "2101"}  # farm/fallback status chatter
VAR_RE = [
    re.compile(r"\d+(?:\.\d+)?"),          # numbers
    re.compile(r"\"[^\"]*\"|'[^']*'"),     # quoted strings
    re.compile(r"\b[0-9a-fA-F]{8,}\b"),    # hex/uuid-ish tokens
    re.compile(r"[/\w.-]+/[\w.-]+"),       # paths
]
REDACT_RE = re.compile(
    r"(?i)\b(token|session|password|account|secret|key)(['\"]?\s*[:=]?\s*)(?!(?:token|session|password|account|secret|key)\b)(\S+)"
)

def redact(text: str) -> str:
    """REDACT keyword-adjacent values; a value that is itself a keyword is skipped
    (lookahead), so 'session token abc123' -> 'session token <REDACT>'."""
    return REDACT_RE.sub(r"\1\2<REDACT>", text)


KEYWORDS = {"token", "session", "password", "account", "secret", "key"}

MSG_NAMES = {
    "1": "tickPrice", "2": "tickSize", "3": "orderStatus", "4": "ERR",
    "5": "openOrder", "6": "updateAccountValue", "8": "execDetails",
    "9": "nextValidId", "12": "contractDetails", "15": "hello",
    "53": "position", "54": "positionEnd", "81": "reqIds",
    "87": "commissionReport", "96": "reqMktData?", "100": "reqScanner",
}


def mask(text: str) -> str:
    for r in VAR_RE:
        text = r.sub("<V>", text)
    return redact(text)


def template_id(msg_id: str, body: str) -> str:
    t = hashlib.blake2b(mask(body).encode(), digest_size=6).hexdigest()
    return f"{msg_id}:{t}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="+", type=Path)
    ap.add_argument("--csv", type=Path, default=Path("reports/ibkr_log/templates.csv"))
    ap.add_argument("--json", type=Path, default=Path("reports/ibkr_log/summary.json"))
    args = ap.parse_args(argv)

    templates: Counter[str] = Counter()
    samples: dict[str, tuple[str, str, str]] = {}  # tid -> (ts, dir, redacted sample)
    per_file: defaultdict[str, int] = defaultdict(int)
    errors, noise = [], []
    unparsed = 0

    def ingest_gw(ts: str, level: str, body: str, path) -> None:
        tid = template_id(f"L{level}", body)
        templates[tid] += 1
        per_file[str(path)] += 1
        if tid not in samples:
            samples[tid] = (ts, "-", redact(body)[:200])
        if level in ("WARN", "ERROR", "FATAL"):
            errors.append({"ts": ts, "code": level,
                           "msg": redact(body)[:300]})

    api_cur = None  # (ts, direction, payload) of pending API message

    def ingest_api(ts: str, direction: str, payload: str, path) -> None:
        all_fields = payload.split(";")
        msg_id = all_fields[0].strip().lstrip("[").strip() if all_fields else "?"
        # API msg id 4 = error: [4;code-ignored;reqId;ERRORCODE;text...]
        error_code = all_fields[3].strip() if len(all_fields) > 3 else None
        body = payload
        tid = template_id(msg_id, body)
        templates[tid] += 1
        per_file[str(path)] += 1
        if tid not in samples:
            samples[tid] = (ts, direction, redact(body)[:200])
        # error classification: id 4 carries the IB error code in field 4
        if msg_id in ERROR_ID and error_code is not None:
            (noise if error_code in NOISE_CODES else errors).append(
                {"ts": ts, "code": error_code, "msg": redact(body)[:300]}
            )

    for path in args.logs:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            cur = None  # (ts, level, body) of message being continued
            for line in fh:
                line = line.rstrip("\r\n")
                if not line or line.startswith("=="):
                    continue
                m = GATEWAY_RE.match(line)
                if m:  # gateway diagnostic log format
                    if cur is not None:
                        ingest_gw(cur[0], cur[1], cur[2], path)
                    ts, level, thread, body = m.groups()
                    cur = (ts, level, body)
                    continue
                if cur is not None:
                    cur = (cur[0], cur[1], (cur[2] + " " + line)[:2000])
                    continue
                m = LINE_RE.match(line)
                if not m:
                    if cur is None and api_cur is not None:
                        # continuation of a multi-line API message (contract dumps)
                        api_cur = (api_cur[0], api_cur[1],
                                   (api_cur[2] + " " + line)[:2000])
                    else:
                        unparsed += 1
                    continue
                if api_cur is not None:
                    ingest_api(api_cur[0], api_cur[1], api_cur[2], path)
                ts, direction, payload = m.groups()
                api_cur = (ts, direction, payload)
                continue
            if cur is not None:
                ingest_gw(cur[0], cur[1], cur[2], path)
                cur = None
            if api_cur is not None:
                ingest_api(api_cur[0], api_cur[1], api_cur[2], path)
                api_cur = None

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["template_id", "msg_id", "msg_name", "count", "pct",
                    "direction", "first_ts", "sample_redacted", "flags"])
        total = sum(templates.values()) or 1
        for tid, n in templates.most_common():
            ts, d, smp = samples[tid]
            msg_id = tid.split(":", 1)[0]
            flags = []
            if msg_id in ERROR_ID:
                code = smp.split(";")[1].strip() if ";" in smp else "?"
                flags.append("NOISE" if code in NOISE_CODES else "ERROR")
            if n <= 3:
                flags.append("RARE")
            w.writerow([tid, msg_id, MSG_NAMES.get(msg_id, "?"), n,
                         round(100 * n / total, 2), d, ts, smp, "|".join(flags)])

    summary = {
        "files": {k: v for k, v in per_file.items()},
        "lines_parsed": sum(templates.values()),
        "lines_unparsed": unparsed,
        "distinct_templates": len(templates),
        "errors_flagged": len(errors),
        "noise_flagged": len(noise),
        "error_codes": dict(Counter(e["code"] for e in errors)),
        "errors_tail": errors[-50:],
        "rare_templates": [
            {"template_id": tid, "count": n, "sample": samples[tid][2]}
            for tid, n in templates.most_common() if n <= 3
        ][:50],
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(summary, indent=2))

    print(f"parsed={sum(templates.values())} unparsed={unparsed} "
          f"templates={len(templates)} errors={len(errors)} noise={len(noise)}")
    print(f"csv: {args.csv}\njson: {args.json}")
    for tid, n in templates.most_common(10):
        print(f"  top: {tid} n={n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())