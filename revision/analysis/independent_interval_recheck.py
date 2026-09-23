"""Independent saved-certificate and physical-replay audit.

No production analysis module is imported, no large LP is solved, and no raw
input is copied. The small sign-region fixture LPs are independently assembled.
"""
from __future__ import annotations
import os
for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[name] = '1'
from pathlib import Path
import argparse
import hashlib
import itertools
import json
import platform
import sys
from datetime import datetime, timezone
import numpy as np
import scipy
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_INPUT_SHA256 = '0a664312a5bdbb5b7bf3b12dc8e203c932f1b07b7e029abf887e9599efc91163'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4*1024**2), b''):
            h.update(block)
    return h.hexdigest()


def native_certificate(data, directory):
    path = directory/'upper_900s_round3_dual_certificate.npz'
    z = np.load(path)
    fs, cs, knots = z['fs'], z['cs'], z['knots']
    n, k = fs.shape
    step = int(z['step_seconds'])
    assert n*step == len(data) and n == 20348 and k == 20
    eta, reserve, supply = float(z['eta']), float(z['reserve_mw']), float(z['supply_mw'])
    cap = float(z['capacity_mwh'])
    bl, bh = float(z['baseline_lower']), float(z['baseline_upper'])
    y = z['y'].reshape(n, k+2)
    assert np.isfinite(y).all() and y.max() <= 0
    # Direct adjacent-state algebra, independent of sparse LP matrix assembly.
    state_coef = y[:, 0]-y[:, 1]+np.sum(cs*y[:, 2:], axis=1)
    state_aty = state_coef.copy()
    state_aty[:-1] -= state_coef[1:]
    baseline_aty = -np.sum(y[:, 2:], axis=1)
    residual = z['objective']-np.r_[state_aty, baseline_aty]
    rhs_y = (np.sum(y[:, 0]*fs[:, 1]-y[:, 1]*fs[:, 0])
             + np.sum(y[:, 2:]*(cs*fs-knots))+cap/2*state_coef[0])
    lower, upper = z['variable_lower'], z['variable_upper']
    assert np.all(lower[:n-1] == 0) and np.all(upper[:n-1] == cap)
    assert lower[n-1] == upper[n-1] == cap/2
    assert np.all(lower[n:] == bl) and np.all(upper[n:] == bh)
    assert np.all(z['objective'][:n] == 0) and np.all(z['objective'][n:] == step/3600)
    assert np.all(knots[:, 0] == bl) and np.all(knots[:, 1] == bh)
    assert knots.min() >= bl and knots.max() <= bh
    correction = lower@np.maximum(residual, 0)+upper@np.minimum(residual, 0)
    dual = float(rhs_y+correction)
    allocation_upper = supply*len(data)/3600-dual+float(z['numerical_margin_mwh'])
    # Independently derive every native F and inverse slope by sorted prefix sums.
    max_f_error = max_slope_error = 0.
    for start in range(0, n, 256):
        end = min(n, start+256)
        u = np.sort(reserve*np.asarray(data[start*step:end*step]).reshape(-1, step), axis=1)
        prefix = np.c_[np.zeros(end-start), np.cumsum(u, axis=1)]
        for j in range(k):
            b = knots[start:end, j]
            count = np.sum(u <= b[:, None], axis=1)
            part = prefix[np.arange(end-start), count]
            charge = count*b-part
            discharge = prefix[:, -1]-part-(step-count)*b
            f = (eta*charge-discharge/eta)/3600
            inv_slope = 3600/(count*eta+(step-count)/eta)
            max_f_error = max(max_f_error, float(np.max(np.abs(f-fs[start:end, j]))))
            max_slope_error = max(max_slope_error, float(np.max(np.abs(inv_slope-cs[start:end, j]))))
    reported = json.loads((directory/'upper_900s_round3_certificate.json').read_text())
    dual_error = abs(dual-reported['dual_lower_objective'])
    assert dual_error < 1e-9 and max_f_error < 1e-12 and max_slope_error < 1e-10
    return {'status': 'PASS', 'file': path.name, 'sha256': digest(path),
            'inequality_dual_max': float(y.max()), 'rhs_dot_dual_mwh': float(rhs_y),
            'box_correction_mwh': float(correction), 'corrected_dual_mwh': dual,
            'allocation_upper_mwh': allocation_upper, 'reported_dual_difference_mwh': dual_error,
            'support_evaluations_checked': n*k, 'maximum_endpoint_value_error_mwh': max_f_error,
            'maximum_inverse_slope_error': max_slope_error}


def native_witness(data, path, step):
    with np.load(path) as z:
        b, states = z['baseline'], z['states']
    assert len(b)*step == len(data) and len(states) == len(b)+1
    assert np.isfinite(b).all() and np.isfinite(states).all()
    current = low = high = 1.
    actual_power_max = stored_error = charge = discharge = 0.
    for start in range(0, len(b), 512):
        end = min(len(b), start+512)
        a = np.asarray(data[start*step:end*step]).reshape(-1, step)
        assert np.isfinite(a).all() and np.max(np.abs(a)) <= 1.+1e-12
        power = .75*a-b[start:end, None]
        charge += float(np.maximum(-power, 0).sum()/3600)
        discharge += float(np.maximum(power, 0).sum()/3600)
        trajectory = current+np.cumsum(np.where(power >= 0, -power/.94, -power*.94).ravel()/3600)
        low, high = min(low, float(trajectory.min())), max(high, float(trajectory.max()))
        actual_power_max = max(actual_power_max, float(np.max(np.abs(power))))
        stored_error = max(stored_error, float(np.max(np.abs(trajectory.reshape(-1, step)[:, -1]
                                                            -states[start+1:end+1]))))
        current = float(trajectory[-1])
    electrical = float(np.sum(.1-b)*step/3600)
    signed = float(.75*np.asarray(data).sum()/3600)
    kappa = (1-.94**2)/(1+.94**2)
    identity_error = (electrical-.1*len(data)/3600)-(-signed-kappa*(charge+discharge))
    headroom = float(np.max(np.abs(b))+.75)
    load_min, load_max = float(np.min(.1-b)), float(np.max(.1-b))
    assert low >= -1e-8 and high <= 2+1e-8 and abs(current-1) < 1e-8
    assert actual_power_max <= 1+1e-10 and headroom <= 1+1e-10
    assert load_min >= -1e-10 and load_max <= 1+1e-10
    assert stored_error < 1e-8 and abs(identity_error) < 1e-8 and abs(states[0]-1) < 1e-8
    return {'status': 'PASS', 'file': path.name, 'sha256': digest(path),
            'step_seconds': step, 'native_samples_checked': len(data), 'intervals': len(b),
            'electrical_input_mwh': electrical, 'minimum_inventory_mwh': low,
            'maximum_inventory_mwh': high, 'terminal_residual_mwh': current-1,
            'maximum_actual_power_mw': actual_power_max, 'maximum_headroom_mw': headroom,
            'electrolyzer_input_range_mw': [load_min, load_max],
            'maximum_saved_state_error_mwh': stored_error,
            'throughput_identity_residual_mwh': identity_error}


def coarse_replay(data, directory, step):
    path = directory/f'interval_{step}s_coarse_network.npz'
    with np.load(path) as z:
        b, states = z['baseline'], z['states']
    assert len(b)*step == len(data)
    u = .75*np.asarray(data).reshape(-1, step).mean(axis=1)
    power = u-b
    increment = np.where(power >= 0, -power/.94, -power*.94)*step/3600
    replay = np.r_[1., 1.+np.cumsum(increment)]
    electrical = float((.1-b).sum()*step/3600)
    cost = float(u.sum()*step/3600+(1/.94-.94)*np.maximum(increment, 0).sum())
    eq_error = float(np.max(np.abs(np.diff(states)-increment)))
    cost_error = float(.1*len(data)/3600-electrical-cost)
    assert len(states) == len(b)+1 and abs(states[0]-1) < 1e-8
    assert eq_error < 1e-8 and abs(replay[-1]-1) < 1e-8
    assert replay.min() >= -1e-8 and replay.max() <= 2+1e-8
    assert b.min() >= -.25-1e-10 and b.max() <= .1+1e-10 and abs(cost_error) < 1e-8
    report = json.loads(path.with_suffix('.json').read_text())
    assert abs(electrical-report['exact_coarse_mwh']) < 1e-8
    return {'status': 'PASS', 'file': path.name, 'sha256': digest(path),
            'step_seconds': step, 'intervals': len(b), 'electrical_input_mwh': electrical,
            'maximum_equation_error_mwh': eq_error, 'terminal_residual_mwh': float(replay[-1]-1),
            'inventory_range_mwh': [float(replay.min()), float(replay.max())],
            'baseline_range_mw': [float(b.min()), float(b.max())],
            'network_cost_identity_residual_mwh': cost_error}


def enumerate_fixture(fixture):
    """Independent cumulative-inventory LP for each piecewise sign region."""
    a = np.array(fixture['activation'])
    step, cap = fixture['step'], fixture['capacity_mwh']
    n, u = len(a)//step, .75*a
    regions = []
    for q in range(n):
        values = u[q*step:(q+1)*step]
        cuts = np.unique(np.r_[-.25, values[(values > -.25)&(values < .1)], .1])
        regions.append(list(zip(cuts[:-1], cuts[1:])))
    best, feasible_count = np.inf, 0
    for bounds in itertools.product(*regions):
        mid = np.mean(bounds, axis=1)
        slope = np.where(np.repeat(mid, step) >= u, .94, 1/.94)
        components = np.zeros((len(a), n))
        components[np.arange(len(a)), np.arange(len(a))//step] = slope/3600
        accum = np.cumsum(components, axis=0)
        offset = np.cumsum(-slope*u/3600)
        solution = linprog(np.full(n, step/3600), A_ub=np.r_[accum, -accum],
                           b_ub=np.r_[cap/2-offset, cap/2+offset], A_eq=accum[-1:, :],
                           b_eq=[-offset[-1]], bounds=bounds, method='highs',
                           options={'threads': 1, 'primal_feasibility_tolerance': 1e-9,
                                    'dual_feasibility_tolerance': 1e-9})
        if solution.success:
            feasible_count += 1
            best = min(best, solution.fun)
    result = None if not np.isfinite(best) else .1*len(a)/3600-best
    expected = fixture['physical_optimum_mwh']
    assert (result is None) if expected is None else (result is not None and abs(result-expected) < 1e-10)
    if result is not None:
        assert fixture['finite_cap_upper_mwh'] >= result-1e-10
        assert fixture['capacity_free_upper_mwh'] >= fixture['finite_cap_upper_mwh']-1e-10
    return {'status': 'PASS', 'case': fixture['case'], 'feasible_sign_regions': feasible_count,
            'independent_physical_optimum_mwh': result, 'reported_physical_optimum_mwh': expected}


def main():
    parser = argparse.ArgumentParser()
    default_input = Path(os.environ.get('SCREEN_NATIVE_INPUT',
                        Path(os.environ.get('BATTERY_PAPER_INPUT_ROOT', ROOT/'prepared_inputs'))/'native_evaluation.npy'))
    parser.add_argument('--native-input', type=Path, default=default_input)
    parser.add_argument('--results-root', type=Path, default=ROOT/'results'/'interval_bounds')
    parser.add_argument('--output', type=Path, default=ROOT/'results'/'independent_interval_recheck.json')
    args = parser.parse_args()
    input_sha = digest(args.native_input)
    assert input_sha == EXPECTED_INPUT_SHA256, 'This audit targets the frozen German reference input.'
    data = np.load(args.native_input, mmap_mode='r')
    assert data.shape == (18_313_200,)
    native_files = [(900, 'guided_witness_900s_round3_policy0.npz'),
                    (300, 'guided_witness_300s_capacityfree_guide_policy0.npz'),
                    (60, 'guided_witness_60s_capacityfree_guide_policy0.npz')]
    fixtures = json.loads((args.results_root/'active_constraint_audit.json').read_text())
    result = {'status': 'PASS', 'created_utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'Independent saved dual/support audit, original-second native replay, coarse replay and small synthetic enumeration; no production code imported or large LP rerun.',
              'native_input_sha256': input_sha, 'script_sha256': digest(__file__),
              'environment': {'python': sys.version, 'numpy': np.__version__, 'scipy': scipy.__version__,
                              'platform': platform.platform(), 'numerical_threads': 1},
              'native_certificate': native_certificate(data, args.results_root),
              'native_witnesses': [native_witness(data, args.results_root/name, step) for step, name in native_files],
              'complete_coarse_replays': [coarse_replay(data, args.results_root, step) for step in (60, 300, 900)],
              'synthetic_active_constraint_fixtures': [enumerate_fixture(f) for f in
                      [fixtures['prefix_fixture']]+fixtures['capacity_active_fixtures']]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'status': result['status'], 'output': str(args.output),
                     'support_evaluations': result['native_certificate']['support_evaluations_checked'],
                     'native_replays': len(result['native_witnesses']),
                     'complete_coarse_replays': len(result['complete_coarse_replays']),
                     'targeted_synthetic_fixtures': len(result['synthetic_active_constraint_fixtures'])}, indent=2))


if __name__ == '__main__':
    main()
