# Derived result records

This directory stores numerical outputs that support values reported in the manuscript. They are not raw measurements.

| File or directory | Content |
| --- | --- |
| `dual_certificate_2.0_0.1_0.94_17_20348.json` | Finite-capacity reference LP primal/dual audit |
| `hydrogen_matrix.csv` | 45-configuration energy matrix |
| `energy_challenge.json` | Selected efficiency/amplitude calculations |
| `cyclic_energy_dual_challenge.json` | Capacity-free evaluated scalar-dual values used in the challenge |
| `native_hydrogen_witness_2.0_0.1.npz` | Reference feasible native baseline and inventory path |
| `hydrogen_Germany_quarters_2.0_0.1.npz` | Reference quarter-mean baseline and inventory path |
| `monthly_energy_challenge/results.json` | Separate monthly calculation ledger |
| `revision_evidence_manifest.json` | Revised numerical-enclosure cases, input roles, and environment |
| `parameter_decision_grid.csv` | 15-cell discrete parameter decision grid |
| `hydrogen_optimization_independent_check.json` | Small synthetic implementation fixtures |

Run `python src/main_result_audit.py` to verify the central arithmetic and sign relationships among the files. The audit cannot validate an upstream data provider, source-record processing, or claims beyond the model's stated assumptions.
