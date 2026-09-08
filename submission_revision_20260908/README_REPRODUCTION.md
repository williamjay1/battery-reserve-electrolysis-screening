# Reproduction and manuscript review

This is a local review package. No journal submission or public data upload has taken place. The manuscript is not yet certified against a final journal's instructions. The author reports no funding and no competing interests. Final author approval is pending.

The archive preserves two sibling folders. `submission_revision_20260908` is the current analysis and manuscript. `minute_revision_20260908` contains the daily German and Belgian input caches, source-processing code and prior audit results needed to trace their construction. Keep the sibling layout. All analysis work belongs on D; original downloaded records on E remain read-only. No training is performed.

## Quick numerical check

From the current `code` directory, run:

```text
python -X utf8 run_local.py audit_current_evidence.py
python -X utf8 run_local.py verify_hydrogen_optimization.py
```

The first checks result/certificate consistency and reported sign conditions, not all scientific validity. The second independently enumerates physical sign regions on small synthetic instances; those cases are software fixtures rather than empirical observations.

The resolution/horizon extension is reproduced with run_resolution_challenge.py, run_monthly_energy_challenge.py and audit_resolution_extension.py, in that order through run_local.py after prepare_evaluation_cache.py. build_resolution_figure.py generates the additional figure. These stages are also included in the full fresh-analysis runner. compare_resolution_reproduction.py takes the regenerated current project directory as its argument and compares both new tables and all saved schedules. The recorded separate run passed 410 checks; its scope is distinct from the earlier 198-check comparison.

## Full fresh analysis

Install the versions in requirements.txt into a work environment. Use a new D-drive target, with adequate free disk space and memory:

```text
python -X utf8 run_local.py reproduce_in_fresh_directory.py D:\MLWork\reserve_fresh_reproduction
```

The command copies included inputs into a new tree and starts with an empty current results directory. It refuses an existing target. It reruns full native/quarter comparisons, monthly boundaries, parameter challenges, conservative certificates, plots and manuscript assembly. The full optimization can take considerably longer than the quick checks. It uses HiGHS with one thread and an alternative solver on reported failure; unsuccessful solves stop the run. It neither downloads new data nor alters E. The source archive's result tables remain a comparison record.

The normalization cache contains18,313,200 native evaluation samples. It is reconstructed from212daily caches by prepare_evaluation_cache.py. The caches retain the audited source values; they are not new measured observations. Original public endpoints and quality decisions appear in the source bibliography and processing scripts. No redistribution license is implied by inclusion in a private review package; check provider terms before public deposition.

## Manuscript build

In the current paper directory, run pdflatex on manuscript.tex, bibtex on manuscript, then pdflatex twice. Run an additional pass only if references remain unsettled. MiKTeX/TeX Live and Poppler are required separately from Python. Vector figures and900dpiPNG exports are included. Captions are also supplied separately. PDF output must be visually inspected after changes.

## Evidence boundaries

The native optimum is bounded by a feasible witness and optimistic upper bounds; no exact native optimum is claimed. The main energy comparison fixes initial and final inventory at half capacity. Controller classification leaves terminal inventory free for both comparators. Monthly resets differ from full-period inventory transfer. Public aggregate system traces are normalized engineering drivers, not individual asset dispatch. Belgian validated quarter data are not a high-frequency replication. Efficiency conditions without sign reversal are retained.

The manifest records archive-relative filenames, sizes and SHA256digests. Integrity checks establish that files were packaged faithfully, not that every scientific claim is correct. See docs/issue_register.md for the remaining publication checks.

Declaration update: the user response to the explicit funding/COI question is recorded in AUTHOR_DECLARATION_RECORD.md. The PDF now states no funding and no competing interests. Final author review is separate and remains pending.


Distribution redesign: run run_distribution_screen.py, audit_distribution_screen.py and build_distribution_figure.py after the monthly energy challenge, before assemble_manuscript.py. These are included in reproduce_in_fresh_directory.py. results/distribution_screen/reproduction.json records624 deterministic comparisons from a separate directory. Wall times vary and are excluded. The current manuscript has20pages,5figures,2tables and40references.


## Error-envelope and GB transfer extension
The latest scientific assessment is docs/ENVELOPE_TRANSFER_REVIEW.md. Run run_distribution_envelope.py and audit_distribution_envelope.py after the core native cache preparation. Run run_gb_transfer.py using the seven included datasets/gb_frequency/*.npz files, then build_error_transfer_figure.py. The fresh-directory driver now copies these caches and includes both analyses; no raw-data network retrieval is necessary to reproduce the new numerical tables. Existing result-file resume checks require matching cache SHA256.

Raw GB frequency files are listed with official URLs, local immutable E-drive paths and SHA256 in results/gb_frequency_downloads.json. prepare_gb_frequency.py is the optional raw-to-feature regeneration step, not required when using the included derived caches. The failed partial May file is excluded; only complete manifest-listed downloads are inputs. audit_gb_transfer.py independently checks every transformed activation plus quarter-start timestamps, then reruns all 42 conditions in a new D-drive tree. Its fixed fresh target must not already exist; use a new D-drive destination for a repeat audit. The existing successful audit is results/gb_transfer_audit.json.

NESO source: https://www.neso.energy/data-portal/system-frequency-data . Licence: https://www.neso.energy/data-portal/neso-open-licence . Supported by National Energy SO Open Data. Frequency is observed; activation=clip((50-f)/0.2,-1,1) is a model transformation and is not a measured asset instruction. No deadband or device response is claimed. No submission/upload has occurred.
