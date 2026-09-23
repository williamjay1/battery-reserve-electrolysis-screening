# Run the revision-evidence workflow

`src/revision_evidence.py` is the public, portable adaptation of the revision script used to generate the new numerical-enclosure records, the parameter decision grid, and the three figures added in the revision.

## Layout mapping

| Canonical revision layout | This release layout | Purpose |
| --- | --- | --- |
| `analysis/revision_evidence.py` | `src/revision_evidence.py` | Main workflow |
| `analysis/hydrogen_lp_pilot.py` and `analysis/reachability.py` | `src/` | Optimizer and native-path routines imported by the workflow |
| `prepared_inputs/` | `prepared_inputs/` or `$BATTERY_PAPER_INPUT_ROOT` | Reconstructed source-dependent inputs; intentionally not distributed in Version 2 |
| `figures/` | `figures/` | Regenerated vector and PNG figures |
| `revision_results/` | `results/` | Regenerated CSV and JSON ledgers |

## Required prepared-input layout

The workflow requires the following names beneath `prepared_inputs/` (or beneath the directory specified by `BATTERY_PAPER_INPUT_ROOT`):

```text
native_evaluation.npy
reference_quarter_solution.npz
monthly_energy_results.json
gb_frequency/
  2026-01.npz
  ...
  2026-07.npz
```

`native_evaluation.npy` is a reconstructed, normalized German activation cache. It is excluded from the public release because reproduction permission for the source records has not been established. The other inputs are also source-dependent and are not shipped in Version 2. See [provenance/DATA_SOURCES.md](provenance/DATA_SOURCES.md) for source and licence boundaries.

## Execute

Install [requirements.txt](requirements.txt), populate the prepared-input layout from authorized public-source reconstruction, and run from the repository root:

```text
python src/revision_evidence.py
```

For an input directory outside the repository, set an environment variable before running:

```text
set BATTERY_PAPER_INPUT_ROOT=D:\\path\\to\\prepared_inputs
python src/revision_evidence.py
```

On PowerShell:

```text
$env:BATTERY_PAPER_INPUT_ROOT = 'D:\\path\\to\\prepared_inputs'
python src/revision_evidence.py
```

The workflow records archive-relative paths or the environment-root label, input checksums, sample counts, selected numerical-enclosure cases, and root-bracketing checks in `results/revision_evidence_manifest.json`. It must not be described as a self-contained rerun when the German provider records have not been independently obtained and processed.

## Output interpretation

The output manifest distinguishes the endpoint-mixture primal lower side from the group-mean evaluated dual upper side. The evaluated scalar-dual values are valid upper values under the specified model, but they are not exact dual maximizers or native dispatch schedules. The finite-capacity reference upper audit and feasible witness are provided separately under `results/`.
