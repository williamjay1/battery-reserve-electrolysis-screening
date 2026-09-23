# Prepared-input release asset

`prepared_inputs/` is excluded from the Git tree. The revision workflow needs a compact set of reconstructed or derived inputs whose role is listed below. Version 2 deliberately does not distribute these inputs, including the German native cache.

| Relative path | Role | Expected source boundary |
| --- | --- | --- |
| `native_evaluation.npy` | 18,313,200 normalized German activation values used by the reference native calculations | Derived cache; do not release raw provider records with it |
| `reference_quarter_solution.npz` | Quarter-mean baseline and inventory path used for the mechanism illustration | Derived optimization output |
| `monthly_energy_results.json` | Month endpoints used to select the seven German enclosure cases | Derived result ledger |
| `gb_frequency/2026-01.npz` through `gb_frequency/2026-07.npz` | Seven complete transformed Great Britain frequency-input arrays | Derived cache from NESO system-frequency measurements |

If a future release considers a prepared-input bundle:

1. Recheck the upstream provider terms and any redistribution restrictions.
2. Include a machine-readable SHA-256 manifest for each bundled file.
3. Keep raw German setpoints out of the bundle unless their provider explicitly permits redistribution.
4. State that the Great Britain arrays are a model transformation, not observed reserve dispatch.
5. Test that the extracted bundle reproduces `results/revision_evidence_manifest.json` with the pinned environment.

Until that review is complete, reconstruct the inputs from the original public sources. The appropriate file name, version tag, and DOI must be assigned only at the actual release stage.
