# Integration notes

## Mechanism figure

File: `Definitions/figures/mechanism_window_audit.pdf` (138.6 x 140.97 mm).

Suggested caption:

**Within-quarter discrepancies across the complete reference input.** (a) The
empirical cumulative distribution uses all 20,348 quarters. Discrepancy is the
inventory increment predicted by the coarse model minus the native replay
increment, with the same saved coarse-model baseline in each quarter. Values
within 1e-12 MWh of zero are classified as numerical zeros; signed values are
retained in the data. (b–e) Illustrations are the observed quarters nearest the
50th, 90th and 99th percentiles of the positive-discrepancy distribution and
the maximum, with earliest-index tie breaking. All four curves use original
one-second samples and common axis scales. Their titles report terminal
discrepancy, whereas their curves show cumulative discrepancy within the
quarter. The maximum is the previously illustrated quarter 11272. These
criterion-selected windows are illustrations; panel (a) provides the complete
population context.

Main-text facts: 18,488 positive discrepancies; 1,860 numerical zeros; no
negative values beyond tolerance. Median over all quarters is 0.446315 kWh;
P90=1.506892 kWh; P99=3.196758 kWh; maximum=7.343636 kWh. The selected positive
quantile examples differ from the whole-population quantiles: their terminal
discrepancies are 0.508285, 1.567284, 3.260480 and 7.343636 kWh, respectively.
Do not call the selected first window the population median.

Summing all fixed-baseline discrepancies yields 13.072335 MWh, but this is
not a reoptimized schedule difference and must not be described as the
coarse-versus-native optimal-input gap. The full signed table is
`results/quarter_increment_discrepancies.csv`; it contains derived interval
increments rather than redistributed one-second activation.

## Pipeline figure

File: `Definitions/figures/pipeline_cost.pdf` (138.6 x 108.71 mm).

Suggested caption:

**Measured cost of the complete local screen and a separate saved-schedule
check.** (a) Three individual runs are shown for every phase; the right column
reports phase medians. The screen loads the 18,313,200-element NumPy array,
checks and scales the input, sorts samples within each quarter, constructs
K=3 and K=9 summaries, queries both upper bounds, and performs array-checksum,
mean-preservation and Jensen checks. (b) The total for each complete local
screen. (c) Loading and replaying the already saved feasible native schedule;
this is independent validation, not schedule optimization or an output of
the screen. Timings use one numerical thread on an AMD Ryzen 9 8945HS with
Python 3.12.10, NumPy 2.5.1 and Numba 0.67.0. Provenance/checksum reads warm
the input cache; the OS cache is not flushed and system load is not isolated.
Network acquisition, source parsing, imports, JIT warm-up and prior
optimization are excluded. All timings, input hashes and checks are retained.

Use the final `runs` in `results/pipeline_window_audit.json`; provisional
concurrent timing runs are retained separately and must not be substituted
for the final measurements.

Final measurements after the other known solver was paused: complete local
screen 1.067741, 0.974886 and 1.027303 s (median 1.027303 s). Phase medians,
in order: load 0.028701 s; input checking/scaling 0.051279 s; sort 0.078560 s;
two summaries 0.022488 s; two upper queries 0.062705 s; checksum/mean/Jensen
checks 0.803008 s. Medians of phases need not sum to the median total.
The separate saved-witness load plus replay totals are 0.027413, 0.027221
and 0.028717 s; median 0.027413 s. All three physical replays returned
496.725390798 MWh, zero constraint violation and terminal residual
5.67e-11 MWh. The K=3 and K=9 queries returned 503.780389924 and
503.507199803 MWh in every run. Previous timings remain in
`pipeline_window_audit_preliminary.json`.

## Reproduction

Run `analysis/pipeline_windows.py --input-root AUTHORIZED_INPUT_DIRECTORY
--witness SAVED_WITNESS_NPZ` to generate a new measurement report and the
derived interval table. Then run `plotting/plot_pipeline_windows.py
--input-root AUTHORIZED_INPUT_DIRECTORY` to produce both figures. One-second
source caches are external dependencies and must not enter the submission or
public reproducibility package. Exclude the machine-specific
`results/numba_cache_pipeline` directory from distribution.

The window rule was recorded in `notes/pipeline_window_protocol.md` before
the first new interval computation. This is an analysis audit trail, not a
claim of preregistration.
