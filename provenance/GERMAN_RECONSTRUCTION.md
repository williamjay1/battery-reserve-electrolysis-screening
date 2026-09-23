# German input reconstruction chain

Version 2 intentionally excludes the German one-second aFRR files, daily caches, and the normalized `native_evaluation.npy` cache. The exclusion follows the reproduction-rights boundary in [DATA_SOURCES.md](DATA_SOURCES.md); it is not a claim that the source files cannot be obtained from Netztransparenz.

## Verified Version 1 chain

The immutable Version 1 archive is available at [Zenodo DOI 10.5281/zenodo.22659529](https://doi.org/10.5281/zenodo.22659529). Its matching repository snapshot is commit [`36aeb2a08dd7682e4f210c7718b188bb4c67cac3`](https://github.com/williamjay1/battery-reserve-electrolysis-screening/tree/36aeb2a08dd7682e4f210c7718b188bb4c67cac3).

The Version 1 source paths are:

```text
minute_revision_20260908/code/download_germany.py
minute_revision_20260908/code/cache_germany.py
submission_revision_20260908/code/prepare_evaluation_cache.py
```

`download_germany.py` records the provider inventory and fetches missing monthly `SRL_Soll_*.csv.zip` files to a caller-controlled raw-data directory. `cache_germany.py` reads the official local-clock CSV export, handles Europe/Berlin daylight-saving transitions, rejects incomplete, duplicated, unordered, or non-finite daily paths, and writes only derived daily caches. `prepare_evaluation_cache.py` builds the 2026 evaluation cache from retained daily caches.

The checked 19-file inventory (January 2025 through July 2026), byte sizes, and SHA-256 values are included in [germany_raw_files.json](germany_raw_files.json). This JSON file is an inventory only: it contains no source observations.

## Conditions for the Version 2 reference cache

The Version 2 workflow expects a local file at `prepared_inputs/native_evaluation.npy` with all of the following properties:

- one-second German aFRR setpoints obtained from the provider under its current terms;
- the published power is normalized by the 99.5th percentile of absolute values in January–June 2025, then clipped to `[-1, 1]` before aggregation;
- the reference evaluation period is January–July 2026, retaining 212 complete German local days, 18,313,200 seconds, 20,348 complete 15-minute intervals, and 5,087 hours;
- local paths contain no interpolation, and daylight-saving days retain their actual length; and
- the reconstructed cache has SHA-256 `0a664312a5bdbb5b7bf3b12dc8e203c932f1b07b7e029abf887e9599efc91163` for the validated Version 2 calculation.

The Version 2 script checks the sample count and records this SHA-256 in `results/revision_evidence_manifest.json`. A different provider release, a changed source record, or a modified normalization pipeline can yield a different hash and should be treated as a new input version, not silently substituted for the recorded reference calculation.

## Completing the local prepared-input layout

After reconstructing `native_evaluation.npy`, create the local layout described in [RUN_REVISION_EVIDENCE.md](../RUN_REVISION_EVIDENCE.md). The two smaller German derived records can be copied locally from this repository's frozen result ledgers:

```text
results/hydrogen_Germany_quarters_2.0_0.1.npz
  -> prepared_inputs/reference_quarter_solution.npz
results/monthly_energy_challenge/results.json
  -> prepared_inputs/monthly_energy_results.json
```

For the independent Great Britain extension, Version 1 contains the seven permitted derived caches at:

```text
submission_revision_20260908/datasets/gb_frequency/2026-01.npz
...
submission_revision_20260908/datasets/gb_frequency/2026-07.npz
```

Copy them into `prepared_inputs/gb_frequency/` while preserving the NESO attribution and licence terms in [DATA_SOURCES.md](DATA_SOURCES.md). These files are an engineering input transformation, not observed reserve dispatch.

## What this chain does and does not establish

It provides a documented route from the original provider source through a checked local cache to the Version 2 numerical workflow. It does not grant redistribution rights to German source records, assert that the provider interface will remain unchanged, or turn the model's electrical-input allocation results into measurements of hydrogen output, profitability, or asset dispatch.
