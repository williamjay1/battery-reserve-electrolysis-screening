# Conservative screening of temporal aggregation bias

This is version 3.0.2 of the code and derived-results archive for **Conservative Screening of Temporal Aggregation Bias in Battery–Electrolyzer Energy Allocation** by Junjie Zhang.

The authoritative new analyses are under [`revision/`](revision/README.md). The top-level `src/`, `results/` and older figures preserve the preceding v2 analysis; their reference native lower/upper values are superseded by the refined v3 bracket, although their correctly directed compression bounds remain valid. See `SUPERSEDED.md`.

| German reference quantity | MWh |
|---|---:|
| No-reserve comparator | 508.700000 |
| Exact 15-minute coarse optimum | 512.856678 |
| Improved native feasible lower | 502.790566 |
| Refined finite-capacity native upper | 502.811466 |

The remaining native gap is 0.020900 MWh (0.004157% of the upper). The native global optimum is not claimed exact. Matched sign reversals are also found at one- and five-minute baseline decisions; all native seconds are retained. The one-minute native upper is only 0.091626 MWh below the comparator, so its conditional margin must not be exaggerated.

## Access and licences

Raw provider records and native source-derived caches are excluded. Rebuilding the empirical German values requires authorized provider inputs and hash checks. The package supplies an independent synthetic demo for users without those inputs. Original software and associated source documentation are MIT licensed (`LICENSE`); the archival metadata and original derived figures/results use CC BY 4.0. External data retain provider terms. See `provenance/DATA_SOURCES.md`.

Version 2 is archived at https://doi.org/10.5281/zenodo.22910726. A version 3 DOI may be cited only after the public GitHub Release has been archived and its version link verified; it is intentionally not guessed here.
