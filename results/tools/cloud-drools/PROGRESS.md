# Cloud Drools/KIE re-run progress

2026-10-18 23:16 UTC — 2% — machine recorded (4 vCPU Xeon 2.1 GHz, 15 GiB RAM, no swap, OpenJDK 21.0.12, Maven 3.9.11) — next: regenerate inputs, build KIE 10.2.0 and Drools 7.74.1 drivers — ETA ~23:40 UTC setup done, ~03:30 UTC all done (if Nursery V1 uses full 2 h caps)
2026-10-18 23:19 UTC — 15% — inputs regenerated (39 DMN, manifest identical); KIE 10.2.0 (59 jars) and Drools 7.74.1 (39 jars) built; both run on OpenJDK 21.0.12; KIE 10.2.0 pension 12/12 done, all identical to laptop — next: KIE 10.2.0 Car 24 files (running), then Drools 7.74.1 pension+Car — ETA ~23:45 UTC timing pairs done
2026-10-18 23:29 UTC — 30% — KIE 10.2.0 Car 24/24 done (8-17 s per file vs 12-81 s on laptop), all identical to laptop — next: Drools 7.74.1 pension 12 + Car 24 on OpenJDK 21 — ETA ~23:50 UTC
2026-10-18 23:31 UTC — 40% — Drools 7.74.1 on OpenJDK 21: pension 12/12 + Car 5/24 done, all identical to laptop so far — next: remaining Drools 7.74.1 Car, then Nursery V1 on KIE 10.2.0 (2 h cap) — ETA ~23:37 UTC Car done, Nursery V1 ends by ~01:40 UTC
2026-10-18 23:34 UTC — 45% — Drools 7.74.1 Car 24/24 done; all 36 Drools 7.74.1 and 36 KIE 10.2.0 pension/Car runs identical to laptop; KIE 10.2.0 Nursery V1 started (-Xmx12g, 2 h cap) — next: poll Nursery V1 (auto-progress every ~9 min) — ETA Nursery V1 finished or killed by 01:34 UTC
