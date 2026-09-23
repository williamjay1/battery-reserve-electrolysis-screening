# Local screen timing and population window audit

Keep the package layout `revision/analysis`, `revision/plotting`,
`revision/results`, `revision/notes` and `revision/Definitions/figures`.
The scripts determine `revision` from their own location; they do not require
the author's drive layout.

Authorized input files are external, read-only dependencies:

- `prepared_inputs/native_evaluation.npy`: all 18,313,200 normalized German
  one-second observations; source file SHA-256
  `0a664312a5bdbb5b7bf3b12dc8e203c932f1b07b7e029abf887e9599efc91163`.
- `prepared_inputs/reference_quarter_solution.npz`: the saved exact coarse
  baseline and inventory sequence used to audit every original quarter.
- A saved native witness, selected by `--witness`. The original public V2
  witness used in the reported timing is retained at
  `results/archive/retained_original_witness.npz`; it yields 496.725391 MWh.
  Its file SHA-256 is
  `08c55ea68f1975d78caaf492a61ceaf667af5811aeb226f85376935da230d308`.

The native activation array and provider inputs are **not included**. The
retained witness is a previously published derived schedule, not a source
activation cache. The tighter new reference witness is a different schedule.
The measured replay neither computed nor timed optimization of either
schedule; it only loaded and checked the saved original witness.

From the `revision` directory, after obtaining/rebuilding authorized inputs:

```text
python analysis/pipeline_windows.py --witness results/archive/retained_original_witness.npz
python plotting/plot_pipeline_windows.py
```

The default input directory is `revision/prepared_inputs`. To keep data
elsewhere, pass `--input-root AUTHORIZED_DIRECTORY`. The optional
`--quarter-solution PATH` overrides its coarse baseline file. Alternatively
set `BATTERY_PAPER_INPUT_ROOT`, `BATTERY_PAPER_WITNESS` and
`BATTERY_PAPER_COARSE_SOLUTION`. All analysis outputs remain under
`revision/results`; figures and small previews go under `Definitions/figures`
and `qa`. Do not add source caches to a redistributed package.

Rerunning the analysis creates new timings on the current hardware and updates
`results/pipeline_window_audit.json`; preserve the supplied result file first
if comparison with the manuscript run is desired. Cache state and system load
are explicitly recorded; hardware timings are not expected to reproduce
bit-for-bit. The saved formal measurements used one numerical thread, warmed
the input cache through checksum reads, and paused the other known LP job.
Network retrieval, original-source parsing, imports, JIT warm-up and schedule
optimization are excluded.

The source that produced the manuscript measurements is preserved byte for
byte as `results/measurement_source_snapshots/pipeline_windows_measured.py`.
Its hash matches `analysis_script_sha256` in the formal report. That historical
snapshot required explicit CLI input paths and is retained for provenance;
run the portable `analysis/pipeline_windows.py` entry point above.

The analysis keeps the full signed table of quarter increment discrepancies.
Positive quantile examples and the maximum follow the recorded protocol in
`notes/pipeline_window_protocol.md`; they are not described as a random sample
or as preregistered tests. The plotting script uses the external native cache
to draw the original-second curves without copying its activation data.

Exclude `results/numba_cache_pipeline` and Python `__pycache__` folders when
packaging. They are machine-specific caches and are recreated automatically.

## Independent interval-bound audit

The same package includes an independent implementation for auditing the
saved refinement certificate and three decision durations:

```text
python analysis/independent_interval_recheck.py
```

It defaults to `prepared_inputs/native_evaluation.npy`; alternatively pass
`--native-input AUTHORIZED_CACHE_FILE` or set `SCREEN_NATIVE_INPUT`. It reads
saved certificates and schedules in `results/interval_bounds` and writes
`results/independent_interval_recheck.json`. It re-evaluates all 406,960 native
support points, the inequality dual with box residual compensation, every
original second of three native schedules, all intervals of the 1/5/15 minute
coarse schedules, and three explicitly synthetic constraint fixtures. No
production analysis modules are imported and no large LP is rerun. It only
solves the small sign-region enumeration problems. The source cache is never
copied into its outputs. The supplied recorded result is PASS.
