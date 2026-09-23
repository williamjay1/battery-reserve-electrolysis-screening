"""Local cost and complete-population interval audit; no source input is copied.

The sampling and timing protocol was recorded in notes/pipeline_window_protocol.md
before this script was run. Inputs default to ROOT/prepared_inputs. CLI paths or
BATTERY_PAPER_INPUT_ROOT, BATTERY_PAPER_WITNESS and BATTERY_PAPER_COARSE_SOLUTION
may select authorized external inputs. This analysis never solves a new
optimization problem. The exact source used for the manuscript timings is
retained in results/measurement_source_snapshots/pipeline_windows_measured.py;
this portable revision changes input-path handling, not its numerical methods.
"""
from __future__ import annotations
import os
for _key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
             'NUMEXPR_NUM_THREADS', 'NUMBA_NUM_THREADS'):
    os.environ[_key] = '1'
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
os.environ['NUMBA_CACHE_DIR'] = str(ROOT / 'results' / 'numba_cache_pipeline')
import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
import time
import shutil
from datetime import datetime, timezone
import numpy as np
import numba
from numba import njit

RESULTS = ROOT / 'results'
RESULTS.mkdir(exist_ok=True)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(4 * 1024**2), b''):
            digest.update(block)
    return digest.hexdigest()


def screen(u, supply=.1, eta=.94, reserve=.75, interval_hours=.25):
    """Evaluated scalar dual upper bound, matching frozen distribution_screen.py."""
    n, k = u.shape
    if np.any(np.diff(u, axis=1) < -1e-12):
        raise ValueError('Rank summaries must be sorted within every interval.')
    bl, bh = max(-(1-reserve), supply-1), min(1-reserve, supply)
    total = u.sum(axis=1)
    dt = interval_hours / k
    prefix = np.c_[np.zeros(n), np.cumsum(u, axis=1)]

    def value(lam):
        fraction = (1 / eta - 1 / lam) / (1 / eta - eta)
        if fraction <= 0:
            b = np.full(n, bl)
        elif fraction >= 1:
            b = np.full(n, bh)
        else:
            b = np.clip(u[:, min(k-1, max(0, int(np.ceil(fraction*k))-1))], bl, bh)
        count = (u <= b[:, None]).sum(axis=1)
        cp = prefix[np.arange(n), count]
        f = dt * (eta * (count*b-cp) - (total-cp-(k-count)*b)/eta)
        return float(np.sum(b*interval_hours-lam*f)), float(f.sum())

    lo, hi = eta, 1/eta
    best = (-np.inf, 0.)
    for _ in range(55):
        lam = (lo+hi)/2
        d, f = value(lam)
        best = max(best, (d, lam))
        if f < 0:
            lo = lam
        else:
            hi = lam
    for lam in (eta, 1/eta):
        d, _ = value(lam)
        best = max(best, (d, lam))
    return {'upper_mwh': float(supply*n*interval_hours-best[0]+1e-6),
            'multiplier': best[1], 'outward_margin_mwh': 1e-6}


@njit(cache=True)
def replay(a, b, initial, cap=2., reserve=.75, eta=.94, supply=.1):
    """One pass over every second, with battery/electrolyzer/headroom checks."""
    s = initial
    low = s
    high = s
    input_h = 0.
    violation = 0.
    for q in range(len(b)):
        h = supply-b[q]
        input_h += h*.25
        violation = max(violation, abs(b[q])+reserve-1., -h, h-1.)
        for j in range(q*900, (q+1)*900):
            p = reserve*a[j]-b[q]
            s += (-p/eta if p >= 0 else -p*eta)/3600
            low = min(low, s)
            high = max(high, s)
    violation = max(violation, -low, high-cap)
    return s, low, high, input_h, violation


def verify_summaries(a, u, sorted_u, means, expected_payload_sha256):
    payload = hashlib.sha256(memoryview(a)).hexdigest()
    if payload != expected_payload_sha256:
        raise AssertionError('Native array payload checksum changed.')
    max_mean_error = float(np.max(np.abs(u.mean(axis=1)-sorted_u.mean(axis=1))))
    minimum_jensen_slack = {}
    for k, z in means.items():
        max_mean_error = max(max_mean_error, float(np.max(np.abs(u.mean(axis=1)-z.mean(axis=1)))))
        # Check concavity at three fixed, admissible baselines, covering both limits.
        min_slack = np.inf
        for start in range(0, len(u), 512):
            x = u[start:start+512]
            m = z[start:start+512]
            for baseline in (-.25, 0., .1):
                xn = baseline-x
                xm = baseline-m
                native_increment = .25*np.mean(np.where(xn >= 0, .94*xn, xn/.94), axis=1)
                summary_increment = .25*np.mean(np.where(xm >= 0, .94*xm, xm/.94), axis=1)
                min_slack = min(min_slack, float(np.min(summary_increment-native_increment)))
        minimum_jensen_slack[str(k)] = min_slack
    if max_mean_error > 1e-12 or min(minimum_jensen_slack.values()) < -1e-12:
        raise AssertionError('Mean preservation or Jensen check failed.')
    return {'array_payload_sha256': payload, 'maximum_mean_preservation_error_mw': max_mean_error,
            'minimum_Jensen_slack_mwh': minimum_jensen_slack,
            'Jensen_baselines_mw': [-.25, 0., .1], 'status': 'PASS'}


def benchmark(input_path, witness_path):
    # Deliberately warm JIT only on tiny artificial data; exclude setup from timings.
    tiny = np.array([-.2, .3] * 450, dtype=float)
    screen(np.sort((.75*tiny).reshape(1, 900), axis=1).reshape(1, 3, 300).mean(axis=2))
    replay(tiny, np.zeros(1), 1.)
    with np.load(witness_path) as witness:
        witness_initial = float(witness['inventory_mwh'][0])
    # Expected checksum is established before measured runs, not inside a timed query.
    check_array = np.load(input_path, mmap_mode='r')
    expected_payload = hashlib.sha256(memoryview(check_array)).hexdigest()
    del check_array
    rows = []
    for repeat in range(1, 4):
        t = time.perf_counter()
        a = np.load(input_path, allow_pickle=False)
        t1 = time.perf_counter()
        if a.shape != (18_313_200,):
            raise AssertionError(a.shape)
        if not np.isfinite(a).all() or np.max(np.abs(a)) > 1.+1e-12:
            raise AssertionError('Native activation is nonfinite or outside [-1, 1].')
        u = (.75*a).reshape(-1, 900)
        t2 = time.perf_counter()
        sorted_u = np.sort(u, axis=1)
        t3 = time.perf_counter()
        means = {k: sorted_u.reshape(-1, k, 900//k).mean(axis=2) for k in (3, 9)}
        t4 = time.perf_counter()
        queried = {str(k): screen(means[k]) for k in (3, 9)}
        t5 = time.perf_counter()
        checks = verify_summaries(a, u, sorted_u, means, expected_payload)
        t6 = time.perf_counter()
        with np.load(witness_path) as stored:
            b = stored['baseline_mw'].copy()
            initial = float(stored['inventory_mwh'][0])
        t7 = time.perf_counter()
        physical = replay(a, b, initial)
        residual = abs(physical[0]-initial)
        if physical[4] > 1e-8 or residual > 1e-8:
            raise AssertionError(f'Witness validation failed: {physical}, residual {residual}')
        t8 = time.perf_counter()
        rows.append({
            'run': repeat,
            'seconds': {'file_load': t1-t, 'activation_prepare': t2-t1,
                        'rank_sort': t3-t2, 'summary_K3_and_K9': t4-t3,
                        'two_upper_queries': t5-t4, 'checksum_and_Jensen_checks': t6-t5},
            'total_local_screen_seconds': t6-t,
            'queries': queried, 'verification': checks,
            'saved_witness_load_seconds': t7-t6,
            'native_witness_replay_validation_seconds': t8-t7,
            'physical_validation': {'terminal_mwh': physical[0], 'minimum_mwh': physical[1],
                                    'maximum_mwh': physical[2], 'electrolyzer_input_mwh': physical[3],
                                    'maximum_violation': physical[4], 'terminal_residual_mwh': residual,
                                    'initial_mwh': witness_initial, 'status': 'PASS'},
        })
        print(f'Cost run {repeat}: screen {t6-t:.6f}s; replay {t8-t7:.6f}s', flush=True)
        del a, u, sorted_u, means
    return rows


def windows(input_path, quarter_path):
    raw = np.load(input_path, mmap_mode='r')
    with np.load(quarter_path) as stored:
        baselines = stored['baseline_mw'].copy()
    n = len(raw)//900
    coarse = np.empty(n)
    native = np.empty(n)
    for start in range(0, n, 512):
        stop = min(n, start+512)
        a = np.asarray(raw[start*900:stop*900]).reshape(-1, 900)
        power = .75*a-baselines[start:stop, None]
        native[start:stop] = np.sum(np.where(power >= 0, -power/.94, -power*.94), axis=1)/3600
        p = .75*a.mean(axis=1)-baselines[start:stop]
        coarse[start:stop] = .25*np.where(p >= 0, -p/.94, -p*.94)
    discrepancy = coarse-native
    tol = 1e-12
    positive_ids = np.flatnonzero(discrepancy > tol)
    selected = []
    for quantile in (.5, .9, .99):
        target = float(np.quantile(discrepancy[positive_ids], quantile, method='linear'))
        index = int(positive_ids[np.argmin(np.abs(discrepancy[positive_ids]-target))])
        selected.append({'criterion': f'Positive P{100*quantile:g}', 'quantile': quantile,
                         'target_mwh': target, 'quarter_index_zero_based': index})
    selected.append({'criterion': 'Maximum', 'quantile': 1., 'target_mwh': float(discrepancy.max()),
                     'quarter_index_zero_based': int(np.argmax(discrepancy))})
    for item in selected:
        i = item['quarter_index_zero_based']
        item.update(discrepancy_mwh=float(discrepancy[i]), native_increment_mwh=float(native[i]),
                    coarse_increment_mwh=float(coarse[i]), baseline_mw=float(baselines[i]),
                    formerly_selected=(i == 11272))
    # No activation samples are written: the interval results are derived scalars.
    with (RESULTS/'quarter_increment_discrepancies.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['quarter_index_zero_based', 'coarse_increment_mwh', 'native_increment_mwh',
                         'signed_discrepancy_mwh'])
        writer.writerows(zip(range(n), coarse, native, discrepancy))
    distribution = {
        'n_quarters': n, 'zero_tolerance_mwh': tol,
        'positive_count': int(np.sum(discrepancy > tol)),
        'zero_within_tolerance_count': int(np.sum(np.abs(discrepancy) <= tol)),
        'negative_count': int(np.sum(discrepancy < -tol)),
        'raw_negative_float_count': int(np.sum(discrepancy < 0)),
        'minimum_signed_mwh': float(discrepancy.min()), 'maximum_signed_mwh': float(discrepancy.max()),
        'mean_signed_mwh': float(discrepancy.mean()), 'sum_signed_mwh': float(discrepancy.sum()),
        'quantiles_all_mwh': {str(q): float(np.quantile(discrepancy, q)) for q in (0, .25, .5, .75, .9, .95, .99, 1)},
        'quantiles_positive_mwh': {str(q): float(np.quantile(discrepancy[positive_ids], q)) for q in (.5, .9, .99)},
        'definition': 'quarter-mean increment minus native increment under each fixed quarter baseline',
        'all_signed_values_retained': True,
    }
    return {'distribution': distribution, 'selected_windows': selected,
            'selection_rule': 'Protocol recorded before computation; linear positive quantiles, nearest observed discrepancy, earliest exact tie.',
            'previously_selected_quarter': 11272,
            'previously_selected_signed_discrepancy_mwh': float(discrepancy[11272]),
            'source_activation_redistributed': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-root', type=Path,
                        default=Path(os.environ.get('BATTERY_PAPER_INPUT_ROOT', ROOT/'prepared_inputs')),
                        help='Authorized native cache directory; default ROOT/prepared_inputs or BATTERY_PAPER_INPUT_ROOT.')
    parser.add_argument('--witness', type=Path,
                        default=Path(os.environ.get('BATTERY_PAPER_WITNESS',
                                                   ROOT/'prepared_inputs'/'native_hydrogen_witness_2.0_0.1.npz')),
                        help='Saved native feasible witness to replay, not optimize.')
    parser.add_argument('--quarter-solution', type=Path,
                        default=Path(os.environ['BATTERY_PAPER_COARSE_SOLUTION'])
                        if 'BATTERY_PAPER_COARSE_SOLUTION' in os.environ else None,
                        help='Saved coarse baseline; default reference_quarter_solution.npz under the input directory.')
    parser.add_argument('--timing-only', action='store_true',
                        help='Replace provisional timings after preserving the complete earlier report; retain interval audit.')
    args = parser.parse_args()
    input_path = args.input_root/'native_evaluation.npy'
    quarter_path = args.quarter_solution or args.input_root/'reference_quarter_solution.npz'
    try:
        cpu = subprocess.check_output(['powershell', '-NoProfile', '-Command',
               '(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)'], text=True).strip()
    except Exception:
        cpu = platform.processor()
    existing = None
    if args.timing_only:
        current = RESULTS/'pipeline_window_audit.json'
        existing = json.loads(current.read_text(encoding='utf-8'))
        archived = RESULTS/'pipeline_window_audit_preliminary.json'
        if archived.exists():
            raise FileExistsError('Preliminary report already preserved; do not silently overwrite measurements.')
        shutil.copyfile(current, archived)
    result = {'created_utc': datetime.now(timezone.utc).isoformat(),
              'environment': {'python': sys.version, 'numpy': np.__version__, 'numba': numba.__version__,
                              'platform': platform.platform(), 'cpu': cpu,
                              'numerical_threads': 1,
                              'page_cache_state': 'Warmed by provenance and array-checksum reads; no operating-system cache flush',
                              'system_load_isolated': False,
                              'other_known_solver_runs_during_measurements': not args.timing_only,
                              'timer': 'time.perf_counter wall-clock seconds'},
              'input_files': {p.name: {'sha256': sha256(p), 'bytes': p.stat().st_size}
                              for p in (input_path, quarter_path, args.witness)},
              'frozen_algorithm_source': 'distribution_screen.py; native replay equations independently restated',
              'frozen_distribution_screen_sha256': 'd2451f6edc18a5a148f5966ec3f0ff39fdce6f587a99e0ca134b39adb742b87c',
              'excluded_from_timing': ['network acquisition', 'source-provider parsing', 'software import',
                                      'JIT warm-up', 'prior schedule optimization', 'plotting'],
              'screen_outputs_schedule': False,
              'runs': benchmark(input_path, args.witness),
              'window_audit': existing['window_audit'] if existing else windows(input_path, quarter_path)}
    if existing:
        result['preliminary_timing_report'] = 'pipeline_window_audit_preliminary.json'
        result['timing_revision_reason'] = 'Repeat after other known optimization jobs stopped; preliminary concurrent timings retained.'
    result['analysis_script_sha256'] = sha256(__file__)
    result['protocol_sha256'] = sha256(ROOT/'notes'/'pipeline_window_protocol.md')
    (RESULTS/'pipeline_window_audit.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result['window_audit'], indent=2), flush=True)


if __name__ == '__main__':
    main()
