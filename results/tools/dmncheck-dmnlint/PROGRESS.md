# Progress (dmn-check / dmnlint audit)

2026-10-18 19:40 — 55% — Installed both tools; listed validators/rules from installed code (dmn-check 1.4.0 needs Java 21, so ran 1.1.6, the last Java-8 release; dmnlint 2.0.0 has 2 rules); dmn-check done on all 12 pension files + 7 of 24 Car files (DMN 1.3-namespace copies; the DMN 1.4 originals are rejected by its parser) — next: rest of the Car files with dmn-check (~2 min per file), dmnlint on all 39 files (seconds) — ETA ~40 min for Car, then ~10 min write-up; dmn-check on Nursery will probably be skipped (O(n^2) on ~4000+ rules = hours)
2026-10-18 19:43 — 70% — dmnlint 2.0.0 run on all 39 files (originals: parse error on all; DMN1.3 copies: 0 findings), positive controls built and both tools fire on them — next: wait for dmn-check Car run (21/36 files done), then write results.json/SUMMARY.md — ETA ~30 min
2026-10-18 19:47 — 75% — results.json aggregator and run scripts written; dmn-check Car run at 24/36 — next: finish Car run, write SUMMARY.md — ETA ~25 min
2026-10-18 19:56 — 83% — dmn-check Car run in progress (29/36 files done) — next: rest of Car, then SUMMARY.md — ETA ~19 min
2026-10-18 20:04 — 84% — dmn-check Car run in progress (34/36 files done) — next: rest of Car, then SUMMARY.md — ETA ~9 min
2026-10-18 20:06 — 100% — all runs finished (dmn-check pension+Car 36/36, dmnlint 39/39, controls); results.json written; SUMMARY.md blocked for subagent, content handed to lead — next: none — ETA done
