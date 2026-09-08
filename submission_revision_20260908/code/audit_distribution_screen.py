"""Independent epigraph LP and direct Jensen checks; no screen internals used."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import linprog
from distribution_screen import screen,summarize
ROOT=Path(__file__).resolve().parents[1]
rng=np.random.default_rng(60419); records=[]; checked=0
for trial in range(60):
    n,m=4,90; eta=[.8,.9,.94,.98,1.][trial%5]
    u=np.sort(rng.uniform(-.75,.75,(n,m))*(.2 if trial%2 else 1),axis=1)
    for k in [1,3,9,45,90]:
        z=summarize(u,k); dt=.25/k
        # f_q <= every affine branch of its concave exact loss function.
        A=[];B=[]
        for q in range(n):
            for c in range(k+1):
                pref=z[q,:c].sum();total=z[q].sum()
                slope=dt*(eta*c+(k-c)/eta)
                intercept=dt*(-eta*pref-(total-pref)/eta)
                row=np.zeros(2*n);row[q]=-slope;row[n+q]=1
                A.append(row);B.append(intercept)
        row=np.r_[np.zeros(n),-np.ones(n)]; A.append(row);B.append(0.)
        ans=linprog(np.r_[np.full(n,.25),np.zeros(n)],A_ub=A,b_ub=B,
                    bounds=[(-.25,.1)]*n+[(None,None)]*n,method='highs')
        val=screen(z,eta=eta)
        if ans.success:
            exact=.1*n*.25-ans.fun
            err=val['upper_mwh']-exact
            assert -1e-8<=err<=1.1e-6,(trial,k,err)
            checked+=1
        else: assert ans.status==2
        # Direct native vs summary inventory increment at arbitrary baselines.
        for b in [-.25,-.13,0.,.07,.1]:
            direct=lambda v: .25*np.mean(eta*np.maximum(b-v,0)-np.maximum(v-b,0)/eta,axis=1)
            assert np.min(direct(z)-direct(u))>=-1e-12
        records.append(dict(trial=trial,k=k,eta=eta,lp_success=bool(ans.success)))
rows=json.loads((ROOT/'results/distribution_screen/results.json').read_text())
months={r['month']:r for r in json.loads((ROOT/'results/monthly_energy_challenge/results.json').read_text())}
challenges=json.loads((ROOT/'results/energy_challenge.json').read_text())
for r in rows:
    assert r['mean_error_mw']<1e-12
    if r['case'] in months:
        old=months[r['case']]; upper=old['native_upper_mwh'];lower=old['native_lower_mwh']
    else:
        old=next(x for x in challenges if x['eta']==r['eta'] and x['amplitude']==r['amplitude'])
        upper=old['upper_mwh'];lower=old['native_feasible_input_mwh']
    assert r['upper_mwh']>=lower-1e-6
    assert r['upper_mwh']>=upper-2e-6
    if r['k']==900: assert abs(r['upper_mwh']-upper)<2e-6
report=dict(status='PASS',independent_lp_cases=len(records),feasible_lp_comparisons=checked,
            empirical_bounds_checked=len(rows),scope='Capacity-free upper bounds, Jensen contraction, existing feasible lower schedules; not chronological dispatch or external validation.',details=records)
(ROOT/'results/distribution_screen/audit.json').write_text(json.dumps(report,indent=2))
print({k:v for k,v in report.items() if k!='details'},flush=True)
