# Reproduction

Use Python 3.12 and the pinned requirements in submission_revision_20260908/requirements.txt. Work on a copy because numerical scripts write results. On the author's Windows storage layout, use D for working files and E only for immutable raw downloads.

## Offline checks using bundled inputs/results

From the repository root:

```
python verify_manifest.py
python submission_revision_20260908/code/run_local.py submission_revision_20260908/code/verify_hydrogen_optimization.py
python submission_revision_20260908/code/run_local.py submission_revision_20260908/code/audit_distribution_envelope.py
```

The second and third commands test independent small optimization fixtures and concavity/enclosure properties. They do not rerun all empirical results. The GB transfer experiment is independently runnable from the seven bundled derived caches:

```
python submission_revision_20260908/code/run_local.py submission_revision_20260908/code/run_gb_transfer.py
```

Existing results can be reused by resume logic. For a genuinely fresh transfer test, copy the repository and remove only the new copy's `submission_revision_20260908/results/gb_transfer` directory before running. Do not delete the frozen original results.

## German source reconstruction

German native inputs are not bundled for redistribution. Obtain the 19 monthly `SRL_Soll_*.csv.zip` files from the source page in DATA_SOURCES.md. The downloader `minute_revision_20260908/code/download_germany.py` implements the provider's public form and inventory as observed at acquisition; it can be affected by future provider website changes. Its optional `RESERVE_RAW_DIR` environment variable identifies the immutable raw directory (default `E:/AcademicData/06/raw/minute_revision_20260908`). It creates missing raw files exclusively and does not overwrite existing files.

Run the downloader through run_local.py if source files are not already present. Compare source files to provenance/germany_raw_files.json. Then run `minute_revision_20260908/code/cache_germany.py` through run_local.py using the same RESERVE_RAW_DIR. Run `submission_revision_20260908/code/prepare_evaluation_cache.py` to build the 18,313,200-sample evaluation array on the work drive. This array cannot be rebuilt from the public result tables alone.

## Current analysis sequence

After German cache reconstruction, the current code-directory stages are:

```
reachability_property_check.py
prepare_evaluation_cache.py
control_classification.py
run_oracle_frontier.py
run_monthly_oracle.py
run_hydrogen_matrix.py
certify_native_bounds.py
cyclic_energy_dual.py
run_energy_challenge.py
verify_hydrogen_optimization.py
audit_energy_identity.py
run_resolution_challenge.py
run_monthly_energy_challenge.py
audit_resolution_extension.py
run_distribution_screen.py
audit_distribution_screen.py
run_distribution_envelope.py
audit_distribution_envelope.py
run_gb_transfer.py
```

Use `python submission_revision_20260908/code/run_local.py submission_revision_20260908/code/STAGE.py`. A full rerun can be computationally expensive. Use a fresh working tree and retain delivered result/configuration files as the comparison record; inspect resume behavior before treating a run as independent. Acquisition scripts that target raw files are optional and distinct from the numerical stages. Raw-to-cache audit_gb_transfer.py needs raw provider files and is not an offline-only test.

The archive contains optimizer bounds, feasible schedules, all recorded parameter conditions and failed/infeasible outcomes. Bounds are not statistical confidence intervals. Full-period inventory and monthly reset cases answer different questions. Published system signals are not private asset instructions. No new empirical calculations were performed solely to mint this release.

AI assistance in the research process included implementation, verification and manuscript work as disclosed in the separate manuscript. Archiving does not modify that history or resolve journal-specific AI rules.
