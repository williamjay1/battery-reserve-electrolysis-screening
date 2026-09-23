# Reproducibility execution record

## German cache rebuild

The full German rebuild was executed once before the release-path defaults were changed, using explicit local input arguments. No network request or raw-data write occurred.

- 19 of 19 authorized SRL_Soll_*.csv.zip archives passed their byte-size and SHA-256 checks.
- The parser retained 577 complete local Berlin days, including the two 23-hour daylight-saving days.
- The 2025 H1 absolute 99.5th-percentile scale was 1039.8310100000015 MW.
- The normalized January-July 2026 cache contains 18,313,200 seconds, 20,348 15-minute intervals, and 5,087 hours.
- Its SHA-256 is 0a664312a5bdbb5b7bf3b12dc8e203c932f1b07b7e029abf887e9599efc91163, exactly matching the recorded reference.
- The generated cache is intentionally excluded from the public package. The retained distribution-safe evidence is results/rebuild_report.json and results/rebuild_summary.csv.

The report's script checksum identifies the exact script used for that successful run. The subsequently packaged script changes only default input-location discovery: GB cache defaults to PROJECT/prepared_inputs/gb_frequency, German raw input defaults to PROJECT/raw, and top-level src/provenance are preferred with a local staging fallback. The numerical transformation and checks were not rerun solely for that path-default change.

## Great Britain transfer audit

The GB audit was recomputed from the seven permitted derived 2026 cache files with E=2.0 MWh, S=0.1 MW, R=0.75 MW, eta=0.94, and cyclic midpoint endpoints.

- The native capacity-free evaluated dual upper bound was below the no-reserve comparator in all seven months.
- The exact quarter-mean cyclic LP was feasible and below the comparator in January, February, March, May, and July.
- It was infeasible in April and June under the stated quarter-fixed cyclic constraints. The report therefore does not claim a feasible quarter-mean value for those months.
- This is a stress-replay result for transformed GB frequency inputs, not a statement about GB market rules, asset dispatch, or national performance.
## Checksums

- GB audit script used for the recorded audit: 053b7ce3585a39007ae8ddd34a5e3d54c78ecd736d4c4c499e8c141827f3e3b6
- German rebuild script used for the recorded rebuild: e78c9c75752fbdbb66d6fcd37340f61a909805906b34dc1f8387d1c2b46820bd
- Packaged GB script after relative-default adjustment: 64a8b98a2b629c9d2eac49c6afb411bf358eb47af5b327103808142617d43ca0
- Packaged German script after relative-default/summary adjustment: 638244f3bfdac96c66fdc2cd7c3d38892ebc16b62a78e55a0b572f3a1e41daef
