# Conservative screening of temporal aggregation bias in battery-electrolyzer energy allocation

This repository accompanies the manuscript **“Conservative Screening of Temporal Aggregation Bias in Battery-Electrolyzer Energy Allocation.”** It contains the analysis code, numerical ledgers, selected derived figures, and release instructions used to support the manuscript's revised energy-allocation results.

The study asks a narrow engineering question: can replacing one-second reserve activation with matched 15-minute means reverse the sign of a cyclic electrical-input allocation comparison for a modeled battery-electrolyzer system? It reports an exact quarter-hour result, a feasible native lower value, and conservative native upper values. It does **not** estimate hydrogen mass, profitability, degradation, or realized asset dispatch.

## Repository contents

- `src/` — the portable revision-evidence workflow and the physical/optimization routines it calls.
- `results/` — machine-readable ledgers for the main finite-capacity bound, sensitivity challenge, parameter grid, selected monthly records, and independent small-instance check.
- `figures/` — vector and PNG exports of the three figures produced or used by the revision-evidence workflow.
- `data/` — documentation and a manifest template for the separately released prepared inputs. No raw provider data are stored in Git.
- `provenance/` — source, processing, and licensing boundaries, including the documented German reconstruction chain and raw-file hashes without source records.
- `SUPERSEDED.md` — scope of Version 2 and the earlier envelope outputs that must not be reused.
- `CHANGELOG.md` — Version 2 changes and data-release boundary.
- `MANIFEST.json` and `SHA256SUMS.txt` — file inventory and integrity hashes for this staged Version 2 tree.
- `REPRODUCTION.md` and `RUN_REVISION_EVIDENCE.md` — installation, input placement, canonical-layout mapping, and run instructions.

The source code and original documentation in this repository are released under the [MIT License](LICENSE). Provider data and any provider-derived cache retain the applicable source terms; see [provenance/DATA_SOURCES.md](provenance/DATA_SOURCES.md).

## Main reference result

For the German January–July 2026 reference configuration (`E=2` MWh, `S=0.1` MW, `R=0.75` MW, one-way efficiency `eta=0.94`), the saved ledgers report:

| Quantity | Value (MWh) | Interpretation |
| --- | ---: | --- |
| No-reserve comparator | 508.700 | Fixed supply over the 5,087-hour study period |
| Exact quarter-mean optimum | 512.857 | Interval-constant physical LP |
| Native feasible allocation | 496.725 | Sample-audited cyclic schedule |
| Native finite-capacity upper value | 502.973 | Optimistic convex relaxation with a recorded dual audit |

The comparison is a model-based bound statement. The finite-capacity upper value lies below the no-reserve comparator under the stated assumptions; it is not an implementable schedule or an exact native optimum.

## Citation and archival DOI

Use the citation metadata in [CITATION.cff](CITATION.cff). A DOI is intentionally absent from this staging tree. After a public GitHub Release has been archived by Zenodo, add the newly minted DOI to the repository metadata and the manuscript's data-availability statement only after verifying that the Zenodo record is public and points to this release.

The earlier Zenodo record `10.5281/zenodo.22659529` is explicitly not the DOI for this revision.

## Reproduce

Install the pinned packages and reconstruct the required public-source inputs in `prepared_inputs/` as described in [REPRODUCTION.md](REPRODUCTION.md). Then run:

```text
python src/revision_evidence.py
```

The workflow writes figures and result ledgers under the repository root. It does not download, modify, or redistribute raw provider records.

## Release procedure

Before publishing, follow [release/RELEASE_CHECKLIST.md](release/RELEASE_CHECKLIST.md). Version 2 intentionally excludes German native records and their source-derived cache. Verify the Zenodo archive and DOI after the GitHub Release is published.
