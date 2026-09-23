"""Upper bound on native maximum electrolysis allocation, not a dispatch model.

Convex inverse endpoint-energy supports relax native quarter dynamics; native
prefix constraints are omitted. Every exact feasible schedule satisfies the LP.
An independently reconstructed, sample-audited path supplies the lower bound.
"""
import argparse
from pathlib import Path
import json
import numpy as np
from numba import njit
from scipy.sparse import coo_matrix
from scipy.optimize import linprog
from reachability import reach,reconstruct,audit_schedule
ROOT=Path(__file__).resolve().parents[1]

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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compute the finite-capacity native upper bound for a reconstructed activation cache.')
    parser.add_argument('--input', type=Path, default=ROOT / 'prepared_inputs' / 'native_evaluation.npy')
    parser.add_argument('--capacity-mwh', type=float, default=2.0)
    parser.add_argument('--supply-mw', type=float, default=0.1)
    parser.add_argument('--reserve-mw', type=float, default=0.75)
    parser.add_argument('--eta', type=float, default=0.94)
    parser.add_argument('--knots', type=int, default=17)
    args = parser.parse_args()
    if not args.input.exists():
        raise SystemExit(f'Reconstructed input is required but was not found: {args.input}')
    activation = np.load(args.input, mmap_mode='r')
    bound_value, iterations = upper_bound(
        activation, args.capacity_mwh, args.reserve_mw, args.supply_mw, args.eta, args.knots
    )
    print(json.dumps({'hydrogen_upper_mwh': bound_value, 'lp_iterations': iterations}, indent=2))
