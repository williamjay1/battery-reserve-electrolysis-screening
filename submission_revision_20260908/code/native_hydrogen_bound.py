"""Upper bound on native maximum electrolysis allocation, not a dispatch model.

Convex inverse endpoint-energy supports relax native quarter dynamics; native
prefix constraints are omitted. Every exact feasible schedule satisfies the LP.
An independently reconstructed, sample-audited path supplies the lower bound.
"""
from pathlib import Path
import json,time
import numpy as np
from numba import njit
from scipy.sparse import coo_matrix
from scipy.optimize import linprog
from reachability import reach,reconstruct,audit_schedule
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent/'minute_revision_20260908'

@njit(cache=True)
def supports(a,knots,R,eta,step=900,dt=1/3600):
    n=len(a)//step;k=len(knots);fs=np.empty((n,k));cs=np.empty((n,k))
    for q in range(n):
        for j in range(k):
            b=knots[j];f=0.;deriv=0.
            for i in range(q*step,(q+1)*step):
                p=R*a[i]-b
                f+=(-p/eta if p>=0 else -p*eta)*dt
                deriv+=(eta if p<=0 else 1/eta)*dt
            fs[q,j]=f;cs[q,j]=1/deriv
    return fs,cs

def upper_bound(a,E,R,S,eta=.94,K=17,method='highs-ipm'):
    bl=max(-(1-R),S-1);bh=min(1-R,S);knots=np.linspace(bl,bh,K)
    fs,cs=supports(a,knots,R,eta);n=len(fs);s0=E/2
    # Two endpoint increment bounds plus K convex inverse supporting planes.
    coeff=np.c_[np.ones(n),-np.ones(n),cs]
    rhs=np.c_[fs[:,-1],-fs[:,0],cs*fs-knots[None,:]]
    rhs[0,:]+=coeff[0,:]*s0
    m=K+2;rr=np.arange(n*m).reshape(n,m);q=np.repeat(np.arange(n)[:,None],m,axis=1)
    rows=[rr.ravel(),rr[1:].ravel(),rr[:,2:].ravel()]
    cols=[q.ravel(),(q[1:]-1).ravel(),(q[:,2:]+n).ravel()]
    vals=[coeff.ravel(),-coeff[1:].ravel(),-np.ones(n*K)]
    A=coo_matrix((np.concatenate(vals),(np.concatenate(rows),np.concatenate(cols))),shape=(n*m,2*n)).tocsr()
    out=linprog(np.r_[np.zeros(n),np.full(n,.25)],A_ub=A,b_ub=rhs.ravel(),bounds=[(0,E)]*(n-1)+[(s0,s0)]+[(bl,bh)]*n,method=method,options={'threads':1})
    if not out.success and method=='highs-ipm':
        method='highs-ds'
        out=linprog(np.r_[np.zeros(n),np.full(n,.25)],A_ub=A,b_ub=rhs.ravel(),bounds=[(0,E)]*(n-1)+[(s0,s0)]+[(bl,bh)]*n,method=method,options={'threads':1})
    assert out.success,out.message
    # A valid lower bound on the minimization objective, even if returned dual
    # stationarity has small numerical residuals. All primal variables bounded.
    y=np.minimum(out.ineqlin.marginals,0.)
    residual=np.r_[np.zeros(n),np.full(n,.25)]-A.T@y
    lower=np.r_[np.zeros(n-1),s0,np.full(n,bl)]
    upper=np.r_[np.full(n-1,E),s0,np.full(n,bh)]
    dual=float(rhs.ravel()@y+lower@np.maximum(residual,0)+upper@np.minimum(residual,0))
    assert dual<=out.fun+1e-5,(dual,out.fun)
    report=dict(capacity_mwh=E,supply_mw=S,quarters=n,knots=K,eta=eta,method=method,primal_objective=float(out.fun),dual_lower_objective=dual,duality_gap=float(out.fun-dual),roundoff_margin_mwh=1e-6,hydrogen_upper_mwh=float(S*n*.25-dual+1e-6))
    (ROOT/'results'/f'dual_certificate_{E}_{S}_{eta}_{K}_{n}.json').write_text(json.dumps(report,indent=2))
    return float(S*n*.25-dual+1e-6),int(out.nit)

if __name__=='__main__':
    scale=json.loads((BASE/'results/germany_main_config.json').read_text())['scale_mw']
    files=sorted(f for f in (BASE/'datasets/germany_seconds').glob('*.npz') if f.stem>='2026-01-01')
    a=np.concatenate([np.clip(np.load(f)['mw']/scale,-1,1) for f in files]);rows=[]
    for E,S in [(2.,.1),(8.,.05)]:
        t=time.perf_counter();ans=reach(a,E,.75,.94,S,0.,E/2,E/2)
        assert ans[0] and ans[2][-1]<=E/2<=ans[3][-1]
        bs,ss=reconstruct(a,E,.75,.94,*ans[2:],E/2)
        audit=audit_schedule(a,bs,E/2,E,.75,.94,S,0.)
        assert max(audit[-1],abs(ss[0]-E/2),abs(audit[0]-E/2))<1e-6
        lower=audit[3]
        upper,its=upper_bound(a,E,.75,S,K=17)
        assert lower<=upper+1e-6
        row=dict(capacity_mwh=E,supply_mw=S,hydrogen_feasible_lower_mwh=lower,hydrogen_relaxed_upper_mwh=upper,gap_pct=100*(upper-lower)/upper,native_schedule_error=float(max(audit[-1],abs(audit[0]-E/2))),support_knots=17,lp_iterations=its,seconds=time.perf_counter()-t)
        rows.append(row);print(row,flush=True)
        np.savez_compressed(ROOT/'results'/f'native_hydrogen_witness_{E}_{S}.npz',baseline_mw=bs,inventory_mwh=ss)
        (ROOT/'results/native_hydrogen_bounds.json').write_text(json.dumps(rows,indent=2))
