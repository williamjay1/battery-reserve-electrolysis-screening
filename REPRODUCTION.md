# Reproduction guide

## Scope

The scripts reproduce the revision-specific numerical enclosure, discrete decision grid, mechanism illustration, and supporting result ledger. They are designed for the stated piecewise-linear battery model with a 15-minute baseline decision interval. They do not recreate the full provider-data download and quality-control pipeline.

The German reference calculation uses 18,313,200 one-second normalized activation values from January–July 2026. The Great Britain extension uses seven monthly 15-minute-by-900-second activation arrays constructed from public frequency measurements. The smaller saved result files let a reader audit the reported values without re-running the full calculation.

## Software

Use Python 3.12 and install the pinned packages:

```text
python -m venv .venv
.venv\\Scripts\\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The workflow was last checked with Python 3.12.10, NumPy 2.5.1, SciPy 1.18.0, Numba 0.67.0, and Matplotlib 3.11.1 on Windows. It should also work on other platforms with a compatible scientific-Python stack; numerical timings may differ.

## Prepared inputs

The following files are intentionally kept out of Git because of size and provider-data licensing considerations. Version 2 does not distribute the German native input or its source-derived cache. Reconstruct the required inputs from the public providers under their current terms before running the workflow.

```text
prepared_inputs/
  native_evaluation.npy
  reference_quarter_solution.npz
  monthly_energy_results.json
  gb_frequency/
    2026-01.npz
    2026-02.npz
    2026-03.npz
    2026-04.npz
    2026-05.npz
    2026-06.npz
    2026-07.npz
```

The expected file names and roles are documented in [data/PREPARED_INPUTS.md](data/PREPARED_INPUTS.md). Obtain the public provider records under their terms and reconstruct the caches before running the workflow. This repository is portable after that reconstruction, but it is deliberately not a self-contained reproduction bundle.

## Run the revision evidence workflow

From the repository root, with `prepared_inputs/` populated:

```text
python src/revision_evidence.py
```

The script writes:

```text
figures/system_energy_flow.pdf
figures/system_energy_flow.png
figures/mechanism_time_window.pdf
figures/mechanism_time_window.png
figures/parameter_decision_grid.pdf
figures/parameter_decision_grid.png
results/parameter_decision_grid.csv
results/revision_evidence_manifest.json
```

The output manifest records the selected numerical-enclosure cases, endpoint repair residuals, numerical environment, and input locations. The native full-resolution capacity-free value is an evaluated scalar-dual upper value; it must not be described as an exact optimum.

## Audit saved core results

The main-result supporting records are included in `results/`:

- `dual_certificate_2.0_0.1_0.94_17_20348.json` records the finite-capacity LP primal/dual audit for the reference case.
- `hydrogen_matrix.csv` records the full 45-configuration energy matrix.
- `energy_challenge.json` and `cyclic_energy_dual_challenge.json` record selected efficiency/amplitude calculations.
- `native_hydrogen_witness_2.0_0.1.npz` stores the baseline and inventory path for the reference feasible native schedule.
- `hydrogen_Germany_quarters_2.0_0.1.npz` in `results/` stores the released quarter-mean optimization path used by the mechanism illustration; the source-dependent input expected by the workflow is named `prepared_inputs/reference_quarter_solution.npz`.
- `monthly_energy_challenge_results.json` records the separate monthly calculations.
- `hydrogen_optimization_independent_check.json` records small synthetic verification fixtures.

These files are analysis outputs, not raw measurements. They enable numerical traceability for reported values but do not independently validate the public source records or generalize the model beyond its stated assumptions.

## Manuscript build

This archive intentionally excludes manuscript PDFs and journal templates. The manuscript source package is distributed separately for journal handling. The code repository should be cited as a reproduction companion rather than treated as a publisher-formatted article archive.
