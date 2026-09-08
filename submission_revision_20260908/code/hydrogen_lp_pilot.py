"""Exact convex maximum electrolysis allocation for interval-constant drivers.

Endpoint bounds are sufficient only for interval-constant activation. This is
not asserted exact for native German seconds; that application needs replay.
"""
from pathlib import Path
import json,time
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent/'minute_revision_20260908'

def optimize(a,E,R,S,eta=.94,dt=.25):
    n=len(a);u=R*a;s0=E/2;bl=max(-(1-R),S-1);bh=min(1-R,S)
    def increment(b):
        p=u-b
        return np.where(p>=0,-p/eta,-p*eta)*dt
    wlo=increment(bl);whi=increment(bh)
    # Variables are end-of-quarter inventories s[1:n+1], followed by b[0:n].
    rr=[];cc=[];vv=[];rhs=[]
    for q in range(n):
        prev=s0 if q==0 else 0.
        for coeff,rhs0,bcoef in [(1.,whi[q]+prev,0.),(-1.,-wlo[q]-prev,0.),
                                  (1/(eta*dt),-u[q]+prev/(eta*dt),-1.),
                                  (eta/dt,-u[q]+prev*eta/dt,-1.)]:
            row=len(rhs);rhs.append(rhs0);rr.append(row);cc.append(q);vv.append(coeff)
            if q>0:rr.append(row);cc.append(q-1);vv.append(-coeff)
            if bcoef:rr.append(row);cc.append(n+q);vv.append(bcoef)
    A=coo_matrix((vv,(rr,cc)),shape=(len(rhs),2*n)).tocsr()
    bounds=[(0,E)]*(n-1)+[(s0,s0)]+[(bl,bh)]*n
    c=np.r_[np.zeros(n),np.full(n,dt)]
    solution=linprog(c,A_ub=A,b_ub=rhs,bounds=bounds,method='highs',options={'threads':1})
    if not solution.success:return dict(success=False,status=solution.message)
    states=np.r_[s0,solution.x[:n]];b=solution.x[n:]
    exact=increment(b)
    residual=float(np.max(np.abs(np.diff(states)-exact)))
    assert residual<1e-6,residual
    replay=s0+np.cumsum(exact)
    violation=float(max(0.,-replay.min(),replay.max()-E,abs(replay[-1]-s0)))
    assert violation<1e-5,violation
    return dict(success=True,hydrogen_input_mwh=float(np.sum(S-b)*dt),maximum_equation_residual=residual,maximum_replay_violation=violation,iterations=int(solution.nit),baseline=b,states=states)

if __name__=='__main__':
    scale=json.loads((BASE/'results/belgium_validated_config.json').read_text())['scale_mw']
    files=sorted((BASE/'datasets/belgium_quarters').glob('2026-01-*.npz'))
    a=np.concatenate([np.clip(np.load(f)['mw']/scale,-1,1) for f in files])
    rows=[]
    for E,S in [(4.,.2),(8.,.1),(8.,.2)]:
        t=time.perf_counter();result=optimize(a,E,.75,S)
        if result['success']:
            np.savez_compressed(ROOT/'results'/f'hydrogen_lp_pilot_{E}_{S}.npz',baseline=result.pop('baseline'),states=result.pop('states'))
        result.update(capacity_mwh=E,supply_mw=S,seconds=time.perf_counter()-t);rows.append(result);print(result,flush=True)
    (ROOT/'results/hydrogen_lp_pilot.json').write_text(json.dumps(rows,indent=2))
