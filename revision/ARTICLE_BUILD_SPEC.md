# Revision design and evidence ledger

Route: Applied Sciences, applied engineering / numerical-method study. The contribution is a conservative exclusion test for an apparent electrical-input gain under temporal aggregation. Deterministic feasibility and numerical bounds are the relevant validation standards; this is not a predictive ML, causal-identification, or statistical confidence-interval study.

## Decisions fixed before the new calculations

- Compare baseline decision intervals of 60, 300 and 900 seconds on the same 18,313,200 German native observations, E=2 MWh, S=0.1 MW, R=0.75 MW and eta=0.94. Matched coarse models average only within the corresponding decision interval. Report all intervals, including infeasibility or inconclusive results.
- Tighten the native finite-capacity bracket with additional supporting planes and/or an independently replayed feasible schedule. A failed improvement remains recorded. Do not claim an exact optimum without a certified stopping gap.
- Audit all 20,348 quarters under the saved coarse-optimal baseline. Show the full discrepancy distribution and windows nearest the positive-discrepancy P50, P90, P99 and maximum, using deterministic ties. Report zero-discrepancy intervals separately. These are diagnostic selections made after the original finding, not independent validation samples.
- Measure three complete screen runs, including native-array loading, scaling, sorting, summaries, queries and input/numerical checks. Warm compilation separately. Report cache conditions and separately time saved native-witness replay, which excludes optimization and does not belong to the screening algorithm.
- Reclassify the existing complete capacity-by-supply matrix without interpolation; preserve infeasible and inconclusive cases. Do not create unobserved smooth sensitivity regions.

## Article structure

Main text: operational rule first; matched reference result and tightened bracket; shorter baseline intervals; three-mean exclusion and nine-group enclosure; independent GB transfer and its limits. Figures use final-column-size SciencePlots typography and vector exports. Proofs, broad scenario tables, monthly results, Belgium, parameter maps and control diagnostics belong in appendices/supplement.

## Claim-to-evidence map

1. Reference sign reversal: original independently audited coarse LP and new/old native feasible and dual bounds. The upper below H0 settles the sign independently of lower-bound tightness.
2. Conservative screen: Jensen inequality, nonnegative evaluated dual, direct ordering and synthetic epigraph checks. K=3 compression factor refers to summary values, not end-to-end cost or peak memory.
3. Enclosure: endpoint primal lower and mean dual upper, with explicit capacity-free scope and outward margin. Never substitute an incompletely optimized dual as a lower bound.
4. Decision-interval sensitivity: newly executed 60/300/900-second results only. Do not confuse this with existing input-averaging sensitivity at a fixed 900-second baseline.
5. External boundary: GB measured frequency transformed to synthetic activation; recomputed coarse feasibility must be explicit. Monthly German screen inconclusiveness may coexist with a verified gain from a native witness.
6. Reproduction: existing v2 archive supports original calculations. New evidence must be included in a new local reproduction package and, if a new release is made, its DOI may be cited only after formal publication is verified.

## Important corrections

System indicators are not individual-provider dispatch. Droop span does not model omitted deadbands/delays/device dynamics. Optimization brackets are not statistical confidence intervals. Optimistic bounds need not be attainable. AI disclosure must describe the actual coding, analysis and drafting assistance.

## Verification / stop conditions

Check all new numerical claims against executable result ledgers, audit every reported new feasible schedule, rebuild main/supplement/cover PDFs without undefined references or overflow, inspect rendered figures and pages, and rebuild from the delivery ZIP. Preserve the E-drive originals and older D-drive frozen versions. Deliver one authoritative revised set; do not submit to a journal.
