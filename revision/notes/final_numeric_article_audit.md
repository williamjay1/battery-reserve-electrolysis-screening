# Final numeric manuscript audit

**Decision: PASS for the assigned native-bound and decision-interval scope.**

Audited on 2026-09-23 after the current `assemble_revision.py` output. This was a read-only comparison of the manuscript and supplementary LaTeX against the already completed result manifests and independent audits. No optimization, empirical analysis, or manuscript editing was performed.

## Files checked

- `Applied_Sciences_MDPI_Manuscript.tex`
- `Applied_Sciences_MDPI_Supplementary.tex`
- `results/interval_bounds/final_manifest.json`
- `results/interval_bounds/decision_interval_table.csv`
- `results/interval_bounds/upper_900s_round3_certificate.json`
- Previously completed independent certificate, support and physical-replay checks.

## Reference native bracket

The completed reference has a native feasible lower of **502.79056572048813 MWh** and a finite-capacity evaluated upper of **502.81146570412585 MWh**. The interval width is **0.020899983637718833 MWh**, or **20.8999836377 kWh**, equal to **0.004156624314135511% of the upper**.

The abstract, main Results, Conclusions and Supplementary computation section use the correct rounded endpoints **502.791–502.811 MWh**, and the gap is stated as **0.020900 MWh / 0.0042%**. No current-gap assertion retains the former approximately 1.24%. The two rounded endpoints alone display a 0.020 MWh difference, but the Results also give six-decimal endpoints, so the separately stated 0.020900 MWh width is clearly based on the unrounded values.

The main Results correctly identify **502.972585 MWh** and **496.725391 MWh** as the earlier upper and witness, respectively, and explain their improvement. They are not represented as the current endpoints. The finite-capacity upper lies **5.888534295874 MWh** below the comparator, correctly rounded to **5.889 MWh** in the manuscript.

## Decision-duration comparison

Main Table 2 intentionally uses the **same capacity-free upper-bound relaxation for all three durations**. Its 15-minute upper of **503.369 MWh is correct and is not stale**. The tighter finite-capacity upper, **502.811 MWh**, is reported separately for the reference.

| Duration | Exact coarse, manuscript | Native feasible lower, manuscript | Capacity-free upper, manuscript | Upper minus comparator, manuscript | Check |
|---|---:|---:|---:|---:|---|
| 1 minute | 508.930 | 506.662 | 508.608 | −0.092 | PASS |
| 5 minutes | 510.200 | 504.884 | 507.008 | −1.692 | PASS |
| 15 minutes | 512.857 | 502.791 | 503.369 | −5.331 | PASS |

The exact 1-minute exclusion margin is **0.091626006505 MWh**. The abstract and Results correctly round it to **0.092 MWh**, identify it as narrow, and retain the operating assumptions. The main text correctly says all three matched coarse optima exceed **508.700 MWh**, whereas their native upper bounds fall below it. The shared comparator and original one-second input are maintained. The distinction between changing baseline duration and merely averaging the input with 15-minute decisions is explicit.

The figure caption for the reference/sensitivity comparison correctly separates the finite-capacity bracket in panel (a) from capacity-free upper bounds in panel (b). The main-table footnote makes the same distinction. Actual PDF rendering and embedded graphical labels remain within the main agent's visual audit rather than this source-text review.

## Derived physical quantities and numerical checks

- Signed activation energy **−14.285 MWh**, the **231.162 MWh** throughput threshold and the refined native minimum throughput **326.451 MWh** agree with the completed audit. The old **323.844 MWh** inference is not retained for the refined reference.
- The main Results correctly retain **18,313,200** replayed native seconds and round the **1.09 × 10⁻¹¹ MWh** terminal residual to **1.1 × 10⁻¹¹ MWh** where appropriate.
- The reference support refinement is correctly described as **17 initial supports plus three rounds, ending at 20 supports per interval**.
- Appendix values **5.888535297411 MWh primal cost**, **5.888535295874 MWh corrected dual cost**, **1.54 × 10⁻⁹ MWh difference**, and **8.73 × 10⁻⁸ primal inequality residual** match the saved certificate. The text explicitly derives the reported upper from the corrected dual, rather than treating the slightly infeasible relaxed primal as a certificate.
- The **10⁻⁶ MWh outward upper margin**, **10⁻⁷ MWh inward witness inventory margin**, **406,960 independently checked supports**, and independent dual agreement within **3.2 × 10⁻¹³ MWh** are correctly distinguished.
- The native interval is not described as an exact native optimum or a confidence interval. The exactness statement is confined to the constant-input coarse LP.

## Supplementary preservation of earlier candidates

Supplementary Table S1 updates the German reference finite-capacity bracket to **502.791–502.811 MWh**. Supplementary Table S2 and its sensitivity figure retain the earlier **496.725 MWh** reference witness alongside the capacity-free **503.369 MWh** upper. The text explicitly identifies that witness as feasible but no longer the best current lower bound, explains why the original scenario construction is retained, and distinguishes the unchanged capacity-free relaxation. This is transparent retention of a valid earlier candidate, not contradictory reporting.

The **503.242–503.507 MWh** nine-group enclosure and **0.052 kW** equivalent-power width remain explicitly attached to the **capacity-free** model. They are not confused with the much narrower finite-capacity optimization bracket.

## Outcome

No blocking numerical mismatch, incorrect upper-bound substitution, stale current-reference gap, or claim of exact native optimality was found in the assigned source-text scope. No correction to the checked numerical passages is required.
