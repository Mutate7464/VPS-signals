"""WI-016 — triple-barrier fib-ladder labels + E5 meta-labeling.

Reproducible implementation of accepted design
`docs/workflow/designs/D-016-triple-barrier-fib-labeling.md`:

* `triple_barrier` — first-touch ±k·ATR labels over the curated fib vertical
  ladder {8, 21, 55, 144, 233}, symbol-sequential and point-in-time.
* `probe` (steps 4–5) — legacy-vs-triple-barrier comparison and the mandatory
  probe-first gate.
* `meta_labeler` / `actions` (conditional step 6) — only after a probe target
  clears.

All artifacts written by this package carry the `wi016_` prefix.
"""
