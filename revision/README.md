# Reproduce the v3 revision

All new code and results are stored here. The paper reports retrospective engineering calculations, not statistical confidence intervals. Provider measurements are separate from explicitly labeled synthetic software fixtures.

## No-provider-data demonstration

From this directory install the pinned top-level requirements plus pandas, and run:

```text
python analysis/repro_demo.py --write-results
```

This independently enumerates tiny native optima and checks the screen/enclosure/energy identity. It does not reproduce German empirical MWh.

## Authorized German reconstruction

Use `python analysis/rebuild_german.py --help`. Supply a read-only raw directory and a separate derived-output directory. The original 19 archives are identified in `../provenance/germany_raw_files.json`. Raw files are never overwritten, and network downloading is off by default. The expected evaluation-cache SHA-256 is `0a664312a5bdbb5b7bf3b12dc8e203c932f1b07b7e029abf887e9599efc91163`. Inspect `results/rebuild_report.json` for the executed reconstruction status.

Place the authorized cache at `prepared_inputs/native_evaluation.npy`, or set `SCREEN_NATIVE_INPUT` to its location. Detailed bound, sparse coarse LP, witness repair and audit commands are in `analysis/interval_bounds/README.md`; numerical formulations are in `METHODS.md` alongside it. `results/interval_bounds/final_manifest.json` is the authoritative new bound ledger. Independent verification is implemented in `analysis/independent_interval_recheck.py`.

## Other analyses

- `analysis/gb_transfer_audit.py --help`: explicit GB-cache and original-source-code locations; results distinguish infeasibility from a loss objective. The original portable modules are in `../src`.
- `analysis/README_pipeline_windows.md`: complete timed-screen and window-audit commands, input requirements and exclusions. The archived timing source snapshot records the exact source used to measure the quoted runs. A rerun measures new hardware/cache conditions and is not expected to reproduce wall times exactly.
- `plotting/plot_revision.py`: new framework, comparison, screen and capacity map from saved ledgers. `plotting/plot_pipeline_windows.py` makes the window/cost figures. Remaining plot scripts and cached aggregate plotting tables retain the supplementary scenarios.

New diagrams use the community SciencePlots 2.2.2 `science`, `nature`, and `no-latex` styles (https://github.com/garrettj403/SciencePlots; MIT). This is typography/style reuse, not Nature endorsement. Vector PDF/SVG and native 900-dpi PNG exports are under `Definitions/figures`.

## Meaning of the bounds

The main paper's three-duration table uses the same **capacity-free** native upper at every duration. The results manifest additionally supplies the tighter **finite-capacity** 15-minute upper. Do not confuse them. Compression enclosures are capacity-free; feasible finite-battery witnesses require native replay. A non-excluding screen is inconclusive, while a feasible witness above the comparator verifies a positive sign.

`notes/` records the independent mathematical and manuscript audits. Numerical ledgers retain all attempted policies and infeasible cases. Absolute source paths in historical run logs identify provenance only; executable entry points accept portable paths. Raw arrays, reconstructed caches, Numba caches and trained models are absent.
