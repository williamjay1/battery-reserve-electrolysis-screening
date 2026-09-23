# Screen cost and window audit: analysis protocol

Recorded before computing the new timing and interval summaries on 23 September 2026.

## Timing

Use the unchanged 18,313,200-s German reference input. Set common numerical
thread-count variables to one. Warm the screen and native replay on a tiny
synthetic array before any measured run. Repeat the complete local screen
three times, retaining every run: NumPy file load; activation scaling/reshape;
within-quarter sort; rank summaries for K=3 and K=9; both mean-side upper-bound
queries; SHA256 array-payload check and mean-preservation/Jensen checks.
An individual query does not construct or validate a physical schedule.
Separately time loading the saved native feasible witness and replaying every
second, including the physical and terminal-inventory checks. This is replay
validation of an existing schedule, not optimization.

Do not flush the operating-system page cache. Report cache state as
uncontrolled (successive runs are likely warm); include all three runs rather
than selecting the fastest. Network acquisition, source parsing, software
imports, JIT warm-up, and prior optimization are outside the timed local
pipeline. Report these exclusions explicitly. Record runtime, CPU, input
hashes and numerical checks. Existing benchmark records remain unchanged.

## Window selection

For every one of the 20,348 quarters, replay the fixed baseline from the saved
exact quarter solution on its 900 original samples. Define signed discrepancy
as the quarter-mean inventory increment minus the native inventory increment
(MWh). Retain all positive, zero, and negative values in the population report,
using 1e-12 MWh only to classify floating-point zeros. The plotted empirical
distribution contains all quarters.

For illustrations, take the 50th, 90th and 99th percentiles of the strictly
positive discrepancy population (>1e-12 MWh), using linear quantiles. Select
the quarter closest to each quantile, breaking exact ties by the earliest
zero-based quarter index. Also show the maximum discrepancy, with the same
tie rule, and identify whether it is the previously illustrated quarter 11272.
Plot every original second of cumulative discrepancy for each chosen window,
with the same 0–15 minute time axis and common vertical scale. These are
criterion-selected examples rather than a random or representative sample.

The original source caches remain external and read-only. Share the interval
discrepancy table, distribution summaries and reproducible scripts, not the
one-second source array or complete source-derived activation series.
