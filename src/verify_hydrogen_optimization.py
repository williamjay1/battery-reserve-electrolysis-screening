"""Independent exhaustive physical sign-region check of hydrogen optimizers.

Enumerate battery power signs instead of using inverse-function epigraphs.
Each region is an exact linear physical model with every sample state bound.
Small synthetic instances are verification fixtures, not empirical evidence.
"""
from pathlib import Path
from itertools import product
import json
import numpy as np
from scipy.optimize import linprog
from hydrogen_lp_pilot import optimize
from native_hydrogen_bound import upper_bound
from cyclic_energy_dual import bound as cyclic_bound

ROOT = Path(__file__).resolve().parents[1]

def exhaustive(a, E, R, S, eta):
    nq, ns = a.shape
    dt = .25 / ns
    bl, bh = max(-(1-R), S-1), min(1-R, S)
    regions = []
    for row in R*a:
        cuts = sorted(set([bl, bh]+[float(u) for u in row if bl < u < bh]))
        regions.append(list(zip(cuts[:-1], cuts[1:])))
    best = None
    for bounds in product(*regions):
        mid = np.array([(l+h)/2 for l,h in bounds])
        A, rhs = [], []
        slope = np.zeros(nq)
        offset = E/2
        for q in range(nq):
            for x in a[q]:
                u = R*x
                k = eta if mid[q] >= u else 1/eta
                slope[q] += k*dt
                offset -= k*u*dt
                A.extend([slope.copy(), -slope.copy()])
                rhs.extend([E-offset, offset])
        sol = linprog(np.full(nq,.25), A_ub=A, b_ub=rhs,
                      A_eq=[slope], b_eq=[E/2-offset], bounds=bounds,
                      method='highs',options={'threads':1})
        if sol.success and (best is None or sol.fun < best):
            best = float(sol.fun)
    return None if best is None else S*nq*.25-best

def main():
    rng = np.random.default_rng(63107)
    rows = []
    for i in range(30):
        a = rng.uniform(-1,1,(3,2))
        E = float(rng.choice([.08,.2,.5]))
        S = float(rng.choice([.1,.3,.6]))
        eta = float(rng.choice([.85,.94,1.]))
        exact = exhaustive(a,E,.75,S,eta)
        native = np.repeat(a,450,axis=1).ravel()
        if exact is not None:
            bound,_ = upper_bound(native,E,.75,S,eta=eta,K=7)
            assert bound >= exact-1e-8, (i,bound,exact)
            relaxed = cyclic_bound(native,S,eta=eta)['upper_mwh']
            assert relaxed >= exact-1e-8, (i,relaxed,exact)
        else:
            bound = None
        means = a.mean(axis=1)
        coarse_exact = exhaustive(means[:,None],E,.75,S,eta)
        coarse = optimize(means,E,.75,S,eta)
        assert coarse['success'] == (coarse_exact is not None), i
        err = None
        if coarse_exact is not None:
            err = abs(coarse['hydrogen_input_mwh']-coarse_exact)
            assert err < 1e-8, (i,err)
        rows.append(dict(case=i,capacity=E,supply=S,eta=eta,
                         native_exact=exact,native_upper=bound,coarse_error=err))
    report = dict(status='PASS',seed=63107,cases=rows,
                  native_feasible=sum(r['native_exact'] is not None for r in rows),
                  maximum_coarse_error=max(r['coarse_error'] or 0 for r in rows))
    (ROOT/'results/hydrogen_optimization_independent_check.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='cases'}),flush=True)

if __name__ == '__main__':
    main()
