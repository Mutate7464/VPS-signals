"""Deterministic acceptance checks for the 2026-11-06 fib overnight chain.

Usage: uv run python docs/workflow/briefs/2026-11-06-fib-overnight/checks.py <WI-0XX> <out_dir>
Exit 0 = accept, 1 = reject (chain stops). Appends a section to <out_dir>/OVERNIGHT_REPORT.md.
Research verdicts (PASS/FAIL/BLOCKED_PRECONDITION) are RESULTS, not check failures.
Ops tooling for the orchestrator (not application source).
"""
import json
import os
import re
import sys

import pandas as pd

WI, OUT = sys.argv[1], sys.argv[2]
RD = dict(keep_default_na=False, na_values=[''])
lines, ok = [], True


def check(cond, msg):
    global ok
    lines.append(f"- [{'x' if cond else ' '}] {msg}")
    ok = ok and bool(cond)


def near(a, b, tol=0.0015):
    return a is not None and abs(float(a) - b) <= tol


def verdict(md):
    p = os.path.join(OUT, md)
    if not os.path.exists(p):
        return None
    m = re.findall(r'^VERDICT: (.+)$', open(p).read(), re.M)
    return m[-1].strip() if m else None


def wf_row(wf, period, side):
    r = wf[(wf.period == period) * (wf.side == side)]
    return r.iloc[0] if len(r) else None


try:
    if WI == 'WI-021':
        wf = pd.read_csv(os.path.join(OUT, 'walkforward_validation.csv'), **RD)
        e = wf_row(wf, 'EVAL >=2022-07-01', 'bottom')
        check(e is not None and int(e.n_events) == 20990, f"EVAL bottom n_events == 20990 (got {None if e is None else e.n_events})")
        check(e is not None and int(e.n_screened) == 1056, f"EVAL bottom n_screened == 1056 (got {None if e is None else e.n_screened})")
        check(e is not None and near(e.screen_rate_medplus, 0.2959), f"EVAL bottom screen_rate ≈ 0.2959 (got {None if e is None else round(e.screen_rate_medplus, 4)})")
        check(e is not None and near(e.base_rate_medplus, 0.2619), f"EVAL bottom base_rate ≈ 0.2619 (got {None if e is None else round(e.base_rate_medplus, 4)})")
        y = wf_row(wf, '2026', 'bottom')
        check(y is not None and near(y.screen_rate_medplus, 0.2436), f"2026 bottom screen_rate ≈ 0.2436 (got {None if y is None else round(y.screen_rate_medplus, 4)})")
        t = wf_row(wf, 'EVAL >=2022-07-01', 'top')
        check(t is not None and near(t.screen_rate_medplus, 0.1034) and near(t.base_rate_medplus, 0.1147), "EVAL top drop-outcome rates ≈ 0.1034 / 0.1147")
        ev = pd.read_csv(os.path.join(OUT, 'trailing_events_w39.csv'), **RD,
                         usecols=lambda c: c in {'type', 'fwd_mfe_pct', 'grade', 'screen_bottom', 'screen_top', 'market'})
        check({'screen_bottom', 'screen_top', 'market'} <= set(ev.columns), "events file has screen_bottom, screen_top, market")
        check(len(ev) == 186729, f"events rows == 186729 (got {len(ev)})")
        b = ev[ev.type == 'bottom']
        check(int(b[b.fwd_mfe_pct.isna()].grade.notna().sum()) == 0, "unresolved bottoms have empty grade")
        pr = pd.read_csv(os.path.join(OUT, 'rally_grade_priors.csv'), **RD)
        check(len(pr) == 903 and pr.symbol.nunique() == 903, f"priors 903 unique symbols (got {pr.symbol.nunique()})")
        lines.append(f"- result: EVAL bottom edge = {round((e.screen_rate_medplus - e.base_rate_medplus) * 100, 2)}pp; 2026 screen {round(y.screen_rate_medplus, 4)} vs base {round(y.base_rate_medplus, 4)}")

    elif WI == 'WI-023':
        g = pd.read_csv(os.path.join(OUT, 'exit_policy_grid.csv'), **RD)
        check(g.policy.nunique() == 32, f"32 policies (got {g.policy.nunique()})")
        def cell(pol, s):
            r = g[(g.policy == pol) * (g.period == 'EVAL') * (g.market == 'ALL') * (g.set == s)]
            return r.iloc[0] if len(r) else None
        s = cell('t10_s8_d39_close', 'screened'); a = cell('t10_s8_d39_close', 'all')
        check(s is not None and int(s.n) == 1007, f"t10_s8_d39_close EVAL screened n == 1007 (got {None if s is None else s.n})")
        check(s is not None and 0.403 <= s.hit_rate <= 0.712, f"screened hit_rate in [0.403, 0.712] (got {None if s is None else round(s.hit_rate, 4)})")
        check(a is not None and 0.378 <= a.hit_rate <= 0.705, f"all-bottoms hit_rate in [0.378, 0.705] (got {None if a is None else round(a.hit_rate, 4)})")
        ch = json.load(open(os.path.join(OUT, 'exit_policy_choice.json')))
        check('policy' in ch, "exit_policy_choice.json has 'policy'")
        lines.append(f"- result: chosen policy = {ch.get('policy')} ({ch.get('reason')}), CALIB mean ret {ch.get('calib_mean_ret')}")
        if ch.get('policy'):
            c = cell(ch['policy'], 'screened')
            if c is not None:
                lines.append(f"- result: chosen policy EVAL screened: n {int(c.n)}, hit {round(c.hit_rate, 3)}, mean ret {round(c.mean_ret, 4)}, p10 {round(c.p10_ret, 4)}, max consec losses {int(c.max_consec_losses)}")
            for m in ('CAD', 'USD'):
                r = g[(g.policy == ch['policy']) * (g.period == 'EVAL') * (g.market == m) * (g.set == 'screened')]
                if len(r):
                    lines.append(f"- result: {m} EVAL screened mean ret {round(r.iloc[0].mean_ret, 4)} (n {int(r.iloc[0].n)})")
        tl = pd.read_parquet(os.path.join(OUT, 'trade_labels_w39.parquet'), columns=['policy'])
        check(len(tl) == 76049 * 32, f"trade_labels rows == 76049*32 (got {len(tl)})")

    elif WI == 'WI-022':
        rd = pd.read_csv(os.path.join(OUT, 'regime_daily.csv'), **RD)
        check(set(rd.market.unique()) >= {'CAD', 'USD', 'ALL'}, "regime_daily has CAD/USD/ALL")
        check(rd.r2.dropna().between(0, 1).all() and rd.date.nunique() > 4500, "r2 within [0,1]; > 4500 dates")
        rs = pd.read_csv(os.path.join(OUT, 'regime_overlay_results.csv'), **RD)
        u = rs[(rs.rule == 'UNGATED') * (rs.market == 'ALL') * rs.period.astype(str).str.startswith('EVAL')]
        check(len(u) == 1 and near(u.iloc[0].screen_rate, 0.2959), f"UNGATED EVAL ALL screen_rate ≈ 0.2959 (got {u.screen_rate.tolist()})")
        v = verdict('REGIME_OVERLAY.md')
        check(v is not None, f"REGIME_OVERLAY.md has a VERDICT line (got {v})")
        lines.append(f"- result: VERDICT {v}")
        for _, r in rs[(rs.market == 'ALL') * rs.period.astype(str).str.startswith('EVAL')].iterrows():
            lines.append(f"- result: {r.rule}: gated_rate {round(r.gated_rate, 4) if r.gated_rate == r.gated_rate else 'NA'}, keep {round(r.keep_rate, 3) if r.keep_rate == r.keep_rate else 'NA'}, base {round(r.base_rate, 4)}")

    elif WI == 'WI-024':
        f = pd.read_parquet(os.path.join(OUT, 'event_features.parquet'))
        check(len(f) == 76049, f"event_features rows == 76049 (got {len(f)})")
        need = ['rsi_f63', 'spread15_39', 'bbw_ratio', 'rsi24_39', 'rsi15_slope5', 'dd63', 'dd63_days',
                'days_since_prev_bottom', 'mom_12_1', 'vol21', 'atrp63', 'r1_s5', 'r2', 'prior_p_medplus', 'is_usd', 'screen_bottom']
        miss = [c for c in need if c not in f.columns]
        check(not miss, f"all 16 features present (missing {miss})")
        if not miss:
            nan = f[need].isna().mean()
            check((nan < 0.25).all(), f"each feature NaN share < 25% (max {nan.idxmax()} {round(nan.max(), 3)})")
        v = verdict('META_MODEL.md')
        check(v is not None, f"META_MODEL.md has a VERDICT line (got {v})")
        lines.append(f"- result: VERDICT {v}")
        p = os.path.join(OUT, 'meta_model_results.csv')
        if os.path.exists(p):
            lines.append("- results table: `meta_model_results.csv` (first rows below)")
            lines.append("```\n" + pd.read_csv(p, **RD).head(12).to_string(index=False) + "\n```")

    elif WI == 'WI-025':
        q = pd.read_csv(os.path.join(OUT, 'quantile_results.csv'), **RD)
        check(len(q) > 0, f"quantile_results rows > 0 (got {len(q)})")
        v = verdict('QUANTILE_MODEL.md')
        check(v is not None, f"QUANTILE_MODEL.md has a VERDICT line (got {v})")
        lines.append(f"- result: VERDICT {v}")
        lines.append("```\n" + q.head(12).to_string(index=False) + "\n```")
    else:
        check(False, f"unknown WI {WI}")
except Exception as exc:  # any missing file / column = reject
    check(False, f"check crashed: {type(exc).__name__}: {exc}")

with open(os.path.join(OUT, 'OVERNIGHT_REPORT.md'), 'a') as fh:
    fh.write(f"\n## {WI} — acceptance {'ACCEPT' if ok else 'REJECT'}\n" + "\n".join(lines) + "\n")
print(f"{WI} {'ACCEPT' if ok else 'REJECT'}")
sys.exit(0 if ok else 1)
