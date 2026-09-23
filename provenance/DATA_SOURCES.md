# Data sources, provenance, and licensing boundary

## Repository boundary

This Version 2 repository contains original code, documentation, selected plotting outputs, and derived numerical result records. The repository's original source code and documentation are released under the MIT License. The Zenodo release metadata uses CC BY 4.0 for the archived research object. Neither statement replaces the rights governing third-party records or grants permission to redistribute those records.

## Source summary

| Source | Role in the study | Version 2 release decision | Source terms recorded for the study |
| --- | --- | --- | --- |
| German TSOs via Netztransparenz | Central one-second aFRR reference input | Excluded, including the native cache | The Netztransparenz imprint reserves reproduction rights except where legally permitted; no separate redistribution grant was established |
| Elia Open Data Store (ODS127, ODS128, ODS132) | Interval-level Belgian comparison | Excluded | CC BY 4.0, subject to the provider's current terms |
| NESO system-frequency data | Great Britain frequency-input extension | Excluded | NESO Open Licence; attribution required |

## German aFRR setpoints: excluded

The central calculation uses one-second aFRR setpoints published by German transmission system operators through Netztransparenz, *Data in second resolution*: <https://www.netztransparenz.de/en/Balancing-Capacity/Balancing-Capacity-data/Data-in-second-resolution>.

The original German records, daily processing caches, and the source-derived `native_evaluation.npy` cache are **not included** in Version 2. The source's recorded [imprint](https://www.netztransparenz.de/de-de/Impressum) reserves reproduction rights except where legally permitted, and no separate redistribution grant was established before this release. This is an intentional reproduction-rights boundary, not a claim that the data are unavailable. A user who wants to rerun the native calculation must obtain the records from the provider under the provider's current terms, conduct the stated quality checks, normalize and clip the input as described in the manuscript, and then place the reconstructed cache under `prepared_inputs/`.

The exact Version 1 downloader/parser/cache route and its 19-file SHA-256 inventory are preserved in [GERMAN_RECONSTRUCTION.md](GERMAN_RECONSTRUCTION.md) and [germany_raw_files.json](germany_raw_files.json).

## Elia Belgian aFRR data: not included

The manuscript uses Elia Open Data Store records only for an interval-level comparison:

- ODS127, *Balancing energy volume components per quarter-hour*: <https://opendata.elia.be/explore/dataset/ods127/>;
- ODS128, *Balancing energy volume components per minute*: <https://opendata.elia.be/explore/dataset/ods128/>; and
- ODS132, *Activated Volumes in Belgium*: <https://opendata.elia.be/explore/dataset/ods132/>.

The manuscript records that Elia inputs retain **CC BY 4.0**. They are not included in this repository. Users must verify the current upstream license, record version, and field definitions before reuse.

## NESO Great Britain frequency data: not included

The frequency-input extension starts from one-second Great Britain system-frequency measurements published by the National Energy System Operator: <https://www.neso.energy/data-portal/system-frequency-data>. The manuscript records the **NESO Open Licence** and attribution to National Energy SO Open Data.

The modeled activation `clip((50 - f) / 0.2, -1, 1)` is an engineering transformation. It is not a measured reserve instruction or device-dispatch record. The seven transformed monthly arrays are not included in Version 2; users should obtain the source records, retain the required attribution, and recreate the arrays before running the extension.

## Derived result records

Files under `results/` and `figures/` are derived outputs of the stated processing and optimization workflow. They provide traceability for the manuscript's reported bounds and sensitivity calculations. They are not raw measurements and do not establish any right to distribute an underlying source-derived cache.

## Citation and attribution

Citation metadata for this research object are in [CITATION.cff](../CITATION.cff). Cite the associated manuscript for scientific claims. Cite or attribute public data providers according to their current terms and their official documentation; this repository is not a substitute for the original provider documentation.
