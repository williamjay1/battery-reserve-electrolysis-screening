"""Independent checks for exact scalar storage reachability (no manuscript edits).

Run: python reachability_property_check.py
Only prints a JSON report; no raw data, cache, or results are written.
The reachability recurrence is checked against exhaustive sign-cell LPs, which
enforce the physical charging/discharging branch rather than relaxing it.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path
import hashlib

import numpy as np
from scipy.optimize import linprog


TOL = 2e-9


def summaries(u, b, eta, dt):
    x = b - np.asarray(u, dtype=float)
    f = np.r_[0., np.cumsum(np.where(x >= 0., eta*x, x/eta)*dt)]
    m, M = f.min(), f.max()
    up = np.max(f - np.minimum.accumulate(f))
    down = np.max(np.maximum.accumulate(f) - f)
    return f[-1], m, M, up, down


def out_bounds(u, b, eta, dt, E, L, U):
    F, m, M, _, _ = summaries(u, b, eta, dt)
    return max(L, -m) + F, min(U, E-M) + F


def transition(u, eta, dt, E, L, U, bl, bh):
    """Floating point realization of the exact interval theorem."""
    if bl > bh or L > U:
        return None

    def low_ok(b):
        _, m, _, _, down = summaries(u, b, eta, dt)
        return min(m+U, E-down)

    def high_ok(b):
        _, _, M, up, _ = summaries(u, b, eta, dt)
        return min(E-L-M, E-up)

    if low_ok(bh) < -1e-12 or high_ok(bl) < -1e-12:
        return None
    if low_ok(bl) >= 0.:
        a = bl
    else:
        left, right = bl, bh
        for _ in range(64):
            mid = (left+right)/2
            if low_ok(mid) >= 0.:
                right = mid
            else:
                left = mid
        a = right
    if high_ok(bh) >= 0.:
        z = bh
    else:
        left, right = bl, bh
        for _ in range(64):
            mid = (left+right)/2
            if high_ok(mid) >= 0.:
                left = mid
            else:
                right = mid
        z = left
    if a > z:
        if a-z > 1e-12:
            return None
        a = z = (a+z)/2
    lo = out_bounds(u, a, eta, dt, E, L, U)[0]
    hi = out_bounds(u, z, eta, dt, E, L, U)[1]
    assert lo <= hi+TOL
    return lo, hi, a, z


def cells(u, bl, bh):
    if bl == bh:
        return [(bl, bh)]
    cuts = np.unique(np.r_[bl, np.asarray(u)[(np.asarray(u)>bl) & (np.asarray(u)<bh)], bh])
    return list(zip(cuts[:-1], cuts[1:]))


def affine(u, cell, eta, dt):
    mid = sum(cell)/2
    w = np.where(mid >= np.asarray(u), eta, 1/eta)*dt
    return np.r_[0., np.cumsum(w)], np.r_[0., np.cumsum(-w*np.asarray(u))]


def quarter_lp(u, eta, dt, E, L, U, bl, bh):
    """Exhaust all physical sign cells and optimize four linear objectives."""
    outputs, base = [], []
    for cell in cells(u, bl, bh):
        a, c = affine(u, cell, eta, dt)
        A = np.r_[np.c_[np.ones(len(a)), a], -np.c_[np.ones(len(a)), a]]
        rhs = np.r_[E-c, c]
        bounds = [(L, U), cell]
        sols = [linprog(obj, A_ub=A, b_ub=rhs, bounds=bounds, method='highs')
                for obj in ([1., a[-1]], [-1., -a[-1]], [0., 1.], [0., -1.])]
        assert len(set(s.success for s in sols)) == 1
        if sols[0].success:
            outputs.append((sols[0].fun+c[-1], -sols[1].fun+c[-1]))
            base.append((sols[2].fun, -sols[3].fun))
    if not outputs:
        return None
    outputs.sort()
    right = outputs[0][1]
    for left, newright in outputs[1:]:
        assert left <= right+TOL, ('Disconnected output', outputs)
        right = max(right, newright)
    return min(x[0] for x in outputs), max(x[1] for x in outputs), min(x[0] for x in base), max(x[1] for x in base)


def horizon_lp(us, eta, dt, E, s0, bl, bh, terminal=None):
    """Exhaust joint sign cells. Variables are b[0:Q], s[0:Q+1]."""
    Q = len(us)
    endpoints = []
    for cc in itertools.product(*(cells(u, bl, bh) for u in us)):
        aub, bub, aeq, beq = [], [], [], []
        for q, (u, cell) in enumerate(zip(us, cc)):
            a, c = affine(u, cell, eta, dt)
            for aa, v in zip(a, c):
                row = np.zeros(2*Q+1)
                row[q], row[Q+q] = aa, 1.
                aub.extend([row, -row])
                bub.extend([E-v, v])
            row = np.zeros(2*Q+1)
            row[q], row[Q+q], row[Q+q+1] = -a[-1], -1., 1.
            aeq.append(row)
            beq.append(c[-1])
        bounds = list(cc)+[(s0, s0)]+[(0., E)]*Q
        if terminal is not None:
            bounds[-1] = (terminal, terminal)
        obj = np.zeros(2*Q+1)
        obj[-1] = 1.
        rlo = linprog(obj, A_ub=aub, b_ub=bub, A_eq=aeq, b_eq=beq, bounds=bounds, method='highs')
        if not rlo.success:
            continue
        if terminal is not None:
            return True
        rhi = linprog(-obj, A_ub=aub, b_ub=bub, A_eq=aeq, b_eq=beq, bounds=bounds, method='highs')
        assert rhi.success
        endpoints.append((rlo.fun, -rhi.fun))
    if terminal is not None:
        return False
    if not endpoints:
        return None
    return min(x[0] for x in endpoints), max(x[1] for x in endpoints)


def forward(us, eta, dt, E, s0, bl, bh):
    history = [(s0, s0)]
    ranges = []
    for u in us:
        t = transition(u, eta, dt, E, *history[-1], bl, bh)
        if t is None:
            return None
        history.append(t[:2])
        ranges.append(t[2:])
    return history, ranges


def recover(us, eta, dt, E, fw, terminal):
    history, ranges = fw
    Q = len(us)
    states = np.empty(Q+1)
    baselines = np.empty(Q)
    states[-1] = terminal
    for q in reversed(range(Q)):
        L, U = history[q]
        a, z = ranges[q]
        y = states[q+1]
        if out_bounds(us[q], a, eta, dt, E, L, U)[1] >= y:
            b = a
        else:
            for _ in range(64):
                mid = (a+z)/2
                if out_bounds(us[q], mid, eta, dt, E, L, U)[1] >= y:
                    z = mid
                else:
                    a = mid
            b = z
        F, m, M, _, _ = summaries(us[q], b, eta, dt)
        s = y-F
        assert L-TOL <= s <= U+TOL
        assert s+m >= -TOL and s+M <= E+TOL
        baselines[q], states[q] = b, s
    assert abs(states[0]-history[0][0]) <= TOL
    return baselines, states


def main():
    rng = np.random.default_rng(20260908)
    report = {'seed': 20260908, 'tolerance': TOL}
    errors = []
    one_cases = 120
    for _ in range(one_cases):
        n = int(rng.integers(1, 7))
        u = rng.uniform(-1, 1, n)
        eta = rng.uniform(.55, 1)
        dt = rng.uniform(.04, .3)
        E = rng.uniform(.03, .7)
        L, U = np.sort(rng.uniform(0, E, 2))
        bl, bh = np.sort(rng.uniform(-1, 1, 2))
        t = transition(u, eta, dt, E, L, U, bl, bh)
        ref = quarter_lp(u, eta, dt, E, L, U, bl, bh)
        assert (t is None) == (ref is None)
        if t is not None:
            errors.append(float(np.max(np.abs(np.asarray(t)-ref))))
            assert errors[-1] <= TOL, (t, ref)
        seq = np.asarray([summaries(u, b, eta, dt) for b in np.linspace(bl, bh, 71)])
        ends = np.asarray([out_bounds(u, b, eta, dt, E, L, U) for b in np.linspace(bl, bh, 71)])
        assert np.min(np.diff(seq[:, 3])) >= -TOL
        assert np.max(np.diff(seq[:, 4])) <= TOL
        assert np.min(np.diff(ends, axis=0)) >= -TOL
        assert np.max(np.abs(seq[:, 2]-seq[:, 1]-np.maximum(seq[:, 3], seq[:, 4]))) <= TOL
    report['single_quarter_cases'] = one_cases
    report['single_quarter_max_endpoint_error_vs_exhaustive_physical_lp'] = max(errors)
    multi_errors = []
    trajectories = 0
    for _ in range(24):
        us = rng.uniform(-.7, .7, (3, 2))
        eta, dt, E = rng.uniform(.65, 1), .2, rng.uniform(.04, .4)
        s0, bl, bh = rng.uniform(0, E), -.35, .35
        fw = forward(us, eta, dt, E, s0, bl, bh)
        ref = horizon_lp(us, eta, dt, E, s0, bl, bh)
        assert (fw is None) == (ref is None)
        if fw is not None:
            lo, hi = fw[0][-1]
            err = float(np.max(np.abs(np.array([lo, hi])-ref)))
            assert err <= TOL
            multi_errors.append(err)
            for y in (lo, (lo+hi)/2, hi):
                recover(us, eta, dt, E, fw, y)
                assert horizon_lp(us, eta, dt, E, s0, bl, bh, y)
                trajectories += 1
    report['multi_quarter_cases'] = 24
    report['multi_quarter_max_endpoint_error_vs_exhaustive_physical_lp'] = max(multi_errors)
    report['small_case_recovered_trajectories'] = trajectories
    # Degenerate equality, fixed baseline, capacity zero, and eta=1.
    for u, eta, E, s0, bl, bh in [
        ([.1], .8, 0., 0., -1., 1.),
        ([0., 0.], 1., .3, .1, 0., 0.),
        ([.2, -.2], 1., .4, .2, -.1, .1),
    ]:
        fw = forward([u], eta, .25, E, s0, bl, bh)
        assert fw is not None
        recover([u], eta, .25, E, fw, np.mean(fw[0][-1]))
    report['degenerate_cases'] = 3
    # Real native block length, without relying on any external raw data.
    us = rng.uniform(-.3, .3, (8, 900))
    fw = forward(us, .91, 1/3600, .025, .0125, -.2, .2)
    assert fw is not None
    for y in (*fw[0][-1], .0125):
        recover(us, .91, 1/3600, .025, fw, y)
    report['native_shape'] = [8, 900]
    report['native_recovered_trajectories'] = 3
    # Explicit relaxation gap: net charge x=.1, battery initially full.
    eta, x = .8, .1
    k = eta*x/(1/eta-eta)
    charge, discharge = x+k, k
    physical_delta = eta*x
    relaxed_delta = eta*charge-discharge/eta
    assert physical_delta > 0 and abs(relaxed_delta) < 1e-15
    assert charge+discharge < 1
    report['simultaneous_lp_counterexample'] = {
        'eta': eta, 'dt': 1., 'E': 1., 's0': 1., 'terminal': 1.,
        'b_minus_u': x, 'physical_end': 1+physical_delta,
        'lp_charge': charge, 'lp_discharge': discharge,
        'lp_end': 1+relaxed_delta,
    }
    # Read the production implementation without creating a JIT or import cache.
    source_path = Path(__file__).with_name('reachability.py')
    if source_path.exists():
        source = source_path.read_text(encoding='utf-8-sig')
        production = {'__name__': 'reachability_readonly_review'}
        nojit = source.replace('from numba import njit',
                               'def njit(*args, **kwargs):\n    return lambda f: f')
        exec(compile(nojit, str(source_path), 'exec'), production)
        p_errors, p_feasible = [], 0
        for _ in range(100):
            u = rng.uniform(-1, 1, int(rng.integers(1, 7)))
            eta, dt, E = rng.uniform(.6, 1), .2, rng.uniform(.03, .7)
            L, U = np.sort(rng.uniform(0, E, 2))
            bl, bh = np.sort(rng.uniform(-1, 1, 2))
            ref = transition(u, eta, dt, E, L, U, bl, bh)
            got = production['interval_step'](u, 0, len(u), bl, bh, E, L, U, 1., eta, dt)
            assert bool(got[0]) == (ref is not None)
            if ref is not None:
                p_feasible += 1
                p_errors.append(float(np.max(np.abs(np.array(got[1:])-ref))))
                assert p_errors[-1] <= TOL
        zero = production['interval_step'](np.array([.1]), 0, 1, -1., 1., 0., 0., 0., 1., .8, .25)
        negative = production['interval_step'](np.array([0.]), 0, 1, -5e-11, -5e-11,
                                               1., 0., 0., 0., 1., 1.)
        try:
            trailing = production['reach'](np.array([0., 1.]), .1, 1., 1., 0., 0., .05, .05,
                                            step=3, dt=1.)
            trailing_result = {'accepted': bool(trailing[0]), 'processed_quarters': int(trailing[1])}
        except ValueError as exc:
            trailing_result = {'accepted': False, 'raised': str(exc)}
        terminal_outside = None
        fw = production['reach'](np.array([0.]), 1., 0., 1., 0., 0., .5, .5, step=1, dt=1.)
        if fw[0]:
            try:
                b, s = production['reconstruct'](np.array([0.]), 1., 0., 1., fw[2], fw[3],
                                                fw[4], fw[5], 2., step=1, dt=1.)
                terminal_outside = {'accepted': True, 'states': s.tolist(), 'baselines': b.tolist()}
            except ValueError as exc:
                terminal_outside = {'accepted': False, 'raised': str(exc)}
        recovered_errors = []
        for _ in range(40):
            a = rng.uniform(-1, 1, 60)
            E, R, eta, S = rng.uniform(.05, .3), .75, .94, rng.uniform(.05, .4)
            fw = production['reach'](a, E, R, eta, S, .05, E/2, E/2, step=10, dt=.025)
            if not fw[0]:
                continue
            for target in (fw[2][-1], (fw[2][-1]+fw[3][-1])/2, fw[3][-1]):
                b, s = production['reconstruct'](a, E, R, eta, fw[2], fw[3], fw[4], fw[5],
                                                target, step=10, dt=.025)
                audit = production['audit_schedule'](a, b, E/2, E, R, eta, S, .05, step=10, dt=.025)
                err = max(audit[-1], abs(s[0]-E/2), abs(audit[0]-target))
                assert err <= TOL
                recovered_errors.append(float(err))
        report['production_readonly_check'] = {
            'sha256': hashlib.sha256(source.encode('utf-8')).hexdigest(),
            'random_cases': 100, 'random_feasible': p_feasible,
            'max_boundary_error': max(p_errors),
            'zero_capacity_result': list(zero),
            'tiny_infeasible_fixed_baseline_result': list(negative),
            'trailing_samples_result': trailing_result,
            'terminal_outside_result': terminal_outside,
            'recovered_trajectories': len(recovered_errors),
            'max_recovered_violation_from_prescribed_initial_state': max(recovered_errors),
        }
    report['status'] = 'MATH_CHECKS_PASSED_PRODUCTION_BOUNDARIES_RECORDED'
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
