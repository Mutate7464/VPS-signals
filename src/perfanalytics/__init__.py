"""Performance analytics (WI-015) — run/momentum target engineering and
feature-target alignment analysis.

Modules:
  targets/      — continuous run-target labelers (bottom-to-peak amplitude,
                  velocity, momentum duration; point-in-time, trailing-only).
  features/     — fib-spacing and other candidate feature builders.
  correlation/  — feature-target association / alignment diagnostics
                  (which feature aligns best with each target).

All DataFrames cast to float32 immediately after calculation; n_jobs=2.
"""