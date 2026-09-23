# Minimal public reproduction package plan

**Purpose.** Give a reader without access to the German provider data a small,
deterministic executable check of the model and screening inequalities, while
stating exactly what is needed for a full authorized German rebuild.

## Current evidence already available

The staged Version 2 source tree at
`D:\MLWork\06\Applied_Sciences_energy_revision_20260923\public_repository`
already has:

1. **Portable analysis modules.**  `src/revision_evidence.py`,
   `reachability.py`, `hydrogen_lp_pilot.py`, `native_hydrogen_bound.py`,
   `cyclic_energy_dual.py`, `verify_hydrogen_optimization.py`, and
   `main_result_audit.py`.
2. **Independent small-instance checks.**
   `src/verify_hydrogen_optimization.py` enumerates 30 fixed-seed synthetic
   sign-region fixtures and checks the interval LP and upper bounds.  It is a
   useful development test, but it writes result files and invokes modules
   that write certificates, so it is not the cleanest user-facing smoke demo.
3. **Result traceability.**  `results/` contains the finite-capacity
   certificate, energy challenge, matrix, native witness, monthly results,
   manifest, and `main_result_audit.py`; `MANIFEST.json` and
   `SHA256SUMS.txt` inventory the staged tree.
4. **German route and integrity evidence.**
   `provenance/GERMAN_RECONSTRUCTION.md` identifies Version 1 Zenodo DOI
   `10.5281/zenodo.22659529`, commit
   `36aeb2a08dd7682e4f210c7718b188bb4c67cac3`, and the historical scripts:

   ```text
   minute_revision_20260908/code/download_germany.py
   minute_revision_20260908/code/cache_germany.py
   submission_revision_20260908/code/prepare_evaluation_cache.py
   ```

   `provenance/germany_raw_files.json` supplies the 19 input hashes; the
   documented normalized cache is also identified by SHA-256.
5. **Licensing boundary.**  `LICENSE` applies MIT to original code and
   documentation.  `provenance/DATA_SOURCES.md` correctly retains provider
   terms for German, Belgian, and GB materials and excludes source-dependent
   caches from Version 2.

## Missing for an end-to-end German rerun

- Version 2 does not contain the three historical German downloader/parser/
  cache scripts; it names their paths in Version 1.  It therefore cannot fetch
  and rebuild German inputs by itself.
- It intentionally contains neither the raw German records nor
  `native_evaluation.npy`; `revision_evidence.py` requires an authorized local
  `prepared_inputs/` tree.
- It also excludes the GB transformed arrays, reference quarter path, and
  monthly derived input expected by the revision script.

These omissions should be described as an intentional source-rights boundary,
not as fully self-contained empirical reproducibility.  Do not add provider
records unless the provider terms have been independently verified.

## New no-source demonstration supplied with this revision

The following files now belong to this manuscript-revision tree:

```text
analysis/repro_demo.py
results/repro_demo_report.json
results/repro_demo_summary.csv
```

Run:

```text
python -B analysis/repro_demo.py --write-results
```

It depends only on NumPy and SciPy, generates a fixed-seed 3-by-6 synthetic
activation fixture, and writes only the two `results/repro_demo_*` artifacts.
It does not read German, Belgian, GB, or manuscript-result inputs.

The report demonstrates all of the following on the small fixture:

1. Exact finite-capacity native optimum by exhaustive sign-region LP
   enumeration.
2. Independently enumerated capacity-free native optimum.
3. Valid evaluated scalar-dual upper bounds at full native resolution and
   after three rank-group means.
4. A cyclic endpoint-mixture primal lower construction and an independently
   shifted native capacity-free witness.
5. Ordering checks: finite exact $\leq$ capacity-free exact $\leq$ native
   dual upper $\leq$ rank-mean screen upper, and endpoint lower $\leq$ native
   endpoint witness $\leq$ capacity-free exact.
6. The cyclic signed-energy/throughput identity and the loss relation
   $D=\eta^2C$.

Every output labels itself as a **synthetic software-verification fixture
only**.  It must never be cited as German-data validation, a numerical
reproduction of the paper, or empirical evidence.

## Recommended public-facing package additions

1. Add the three synthetic-demo files above to the source/reproducibility
   package and mention the command in its README.
2. Keep the GPL/MIT provenance accurate: this new demo reimplements the small
   piecewise-linear model independently and contains a header identifying the
   public MIT source-model lineage.  No external source file was copied.
3. Keep `verify_hydrogen_optimization.py` as a developer regression test, but
   direct ordinary readers first to `analysis/repro_demo.py` because it has no
   provider-data dependency and no hidden output mutation.
4. If a future release needs a full German rebuild, first retrieve or vendor
   the Version 1 scripts only after confirming their licence and exact commit;
   then replace historical absolute paths with documented relative paths or an
   explicit input-root environment variable.  Require raw-file hash matching,
   quality checks, and a newly generated cache hash before calling the result
   reproduced.
5. The local staging README still says that Version 2 has no DOI.  If that
   staging tree is refreshed for publication, update this wording only after
   confirming the exact public version DOI and tag.  The existing public
   record checked in the prior release audit is `10.5281/zenodo.22910726` for
   version 2.0.0; do not merge it with the older Version 1 DOI.
