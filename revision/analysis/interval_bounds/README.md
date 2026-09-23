# Native bounds and decision-duration sensitivity

These scripts reproduce the post-review comparison at 60, 300 and 900 s baseline decisions while retaining the same 18,313,200 one-second German activation values and 5,087 h horizon. The original signal is not redistributed here. Reconstruct it using the archive's German-input instructions, verify its manifest checksum, and save it as `prepared_inputs/native_evaluation.npy` under the project root. This module does not download or infer missing observations.

Python versions used: Python 3.12, NumPy 2.5.1, SciPy 1.18.0 and Numba 0.67.0. All solvers use one HiGHS thread. Exact versions are recorded in the final results manifest. Install with `python -m pip install numpy==2.5.1 scipy==1.18.0 numba==0.67.0` in an appropriate isolated environment.

## Portable paths

The default root is two directory levels above this module directory: for `revision/analysis/interval_bounds`, it is `revision`. Default input is `ROOT/prepared_inputs/native_evaluation.npy`; default output is `ROOT/results/interval_bounds`. No absolute workstation path is required. Override using environment variables:

```powershell
$env:SCREEN_NATIVE_INPUT = 'D:/path/to/reconstructed/native_evaluation.npy'
$env:SCREEN_INTERVAL_OUTPUT = 'D:/path/to/new/results/interval_bounds'
# Optional if using a different folder layout:
$env:SCREEN_PROJECT_ROOT = 'D:/path/to/project'
```

`run_interval_bounds.py` also accepts `--input` and `--output`. All scripts honor the environment variables; use them consistently when running the complete pipeline. Original source data should remain read-only. Numba caches are created beside these working scripts, so place the working copy on a writable computation drive.

## Reproduce

From this module directory:

```powershell
python run_interval_bounds.py quick --step 900
python run_interval_bounds.py quick --step 300
python run_interval_bounds.py quick --step 60
python run_interval_bounds.py pilot --step 60
python run_interval_bounds.py upper --step 900 --rounds 3
python run_interval_bounds.py witness --step 900 --rounds 3
python save_final_certificate.py
python coarse_network.py --step 900
python coarse_network.py --step 300
python coarse_network.py --step 60
python run_interval_bounds.py witness --step 300 --guide coarse
python run_interval_bounds.py witness --step 60 --guide coarse
python capacityfree_guidance.py --step 300
python capacityfree_guidance.py --step 60
python audit_small_instances.py
python audit_active_constraints.py
python summarize_results.py
```

The 900 s reference finite-capacity solves each took about one minute on the recorded workstation. Larger sparse LP times depend strongly on hardware and SciPy/HiGHS versions. Each individual LP has a 900 s time limit. A stopped or failed solve raises an error and is never reported as a completed optimum. The original generic coarse inequality form is retained for checking, but `coarse_network.py` is the exact, more efficient form used in the final comparison. The already executed 900 s values agree across both formulations.

## Principal outputs

- `final_manifest.json`: all final numerical values, decisions, software versions, input checksum, reference diagnostics and every retained feasible candidate.
- `decision_interval_table.csv`: three-row manuscript table.
- `upper_900s_round3_dual_certificate.npz`: derived support values/slopes, nonpositive multipliers, finite variable bounds, objective coefficients, primal solution and outward numerical margin. Enables independent dual reconstruction without resolving the LP.
- `upper_900s_round3_certificate.json`: the reference evaluated upper bound and solver residuals; the bound uses the corrected dual objective, not the raw relaxed primal.
- `guided_witness_900s_round3_policy0.npz`: final native reference schedule and inventories. All witnesses contain derived baseline schedules, not the original activation record.
- `interval_{60,300,900}s_coarse_network.json` and `.npz`: exact matched coarse comparisons, physical replay and dual checks.
- `interval_{60,300,900}s_quick.json`: evaluated capacity-free duals, plus initial native reachability witnesses.
- `guided_witness_*`: independently replayed feasible repair candidates. Files named `interval_*_capacityfree_guide` are nominal guides and can violate finite inventory; they are explicitly distinguished from validated witnesses.
- `inherited_refined_witness_{60,300,900}s.json`: full native audits of the refined reference schedule repeated at nested decisions.
- `small_instance_audit.json` and `active_constraint_audit.json`: independent sign-region enumeration checks, including finite-capacity-active and native-prefix-infeasible synthetic fixtures. These are implementation tests, not field evidence.
- `*.log`: incremental execution output, including the abandoned generic 300 s LP and the initially failed roundoff-boundary guidance attempt.

`PLAN.md` records the original requested sensitivity and bounded refinement; `METHODS.md` documents the solver reformulation, feasible repair, numerical safeguards and exploratory implementation adjustments. The study does not claim a globally exact native optimum. Its sign conclusion follows because the valid native upper bound lies below the no-reserve comparator.
