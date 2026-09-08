from pathlib import Path
import json
import numpy as np
from scipy.optimize import linprog
from distribution_envelope import envelope,weighted_bound
ROOT=Path(__file__).resolve().parents[1];rng=np.random.default_rng(70923)
counts=dict(lp_feasible=0,lp_infeasible=0,jensen_checks=0)
for trial in range(40):
    eta=[.8,.9,.94,.98,1.][trial%5];raw=rng.uniform(-.75,.75,(3,90));u=np.sort(raw,axis=1)
    for k in [1,3,9,45,90]:
        g=u.reshape(3,k,90//k);avg=g.mean(axis=2);low=g[:,:,0];high=g[:,:,-1]
        w=np.divide(high-avg,high-low,out=np.ones_like(avg),where=high>low)
        z=np.stack([low,high],axis=2).reshape(3,2*k);weights=np.stack([w,1-w],axis=2).reshape(3,2*k)/k
        for b in [-.25,-.1,0,.1]:
            f=lambda x:eta*np.maximum(b-x,0)-np.maximum(x-b,0)/eta
            native=f(u).mean(axis=1);chord=(f(z)*weights).sum(axis=1);means=f(avg).mean(axis=1)
            assert np.min(native-chord)>-1e-12 and np.min(means-native)>-1e-12
            counts['jensen_checks']+=1
        A=[];B=[]
        for q in range(3):
            for c in range(2*k+1):
                mass=weights[q,:c].sum();part=(weights[q,:c]*z[q,:c]).sum();total=(weights[q]*z[q]).sum()
                row=np.zeros(6);row[q]=-.25*(eta*mass+(1-mass)/eta);row[3+q]=1
                A.append(row);B.append(.25*(-eta*part-(total-part)/eta))
        A.append(np.r_[np.zeros(3),-np.ones(3)]);B.append(0)
        ans=linprog(np.r_[np.full(3,.25),np.zeros(3)],A_ub=A,b_ub=B,bounds=[(-.25,.1)]*3+[(None,None)]*3,method='highs',options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
        if ans.success:
            assert abs(.075-ans.fun-weighted_bound(z,weights,eta=eta))<1e-8,(trial,k,eta,.075-ans.fun,weighted_bound(z,weights,eta=eta))
            counts['lp_feasible']+=1
        else:assert ans.status==2;counts['lp_infeasible']+=1
        e=envelope(u,k,eta=eta);truth=weighted_bound(u,np.full_like(u,1/90),eta=eta)
        assert e['lower_relaxed_mwh']<=truth<=e['upper_relaxed_mwh']
rows=json.loads((ROOT/'results/distribution_envelope.json').read_text());assert len(rows)==78
for r in rows:assert r['lower_relaxed_mwh']<=r['native_relaxed_mwh']<=r['upper_relaxed_mwh']
report=dict(status='PASS',**counts,empirical_intervals=78,scope='Bounds enclose capacity-free dual optimum; lower bound does not certify feasible finite-inventory allocation.')
(ROOT/'results/distribution_envelope_audit.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
