"""Capacity-free analytic upper bound with cyclic inventory.

For every feasible schedule sum f_q(b_q)=0. Therefore sum b_q dt
>= sum min_b (b dt-lambda f_q(b)) for every lambda>=0.
Minima of these convex piecewise-linear functions occur at an activation
breakpoint or a baseline bound. This is a relaxation, not a dispatch policy.
"""
from pathlib import Path
import json
import numpy as np

ROOT=Path(__file__).resolve().parents[1]

def bound(a,S,eta=.94,R=.75,amplitude=1.):
    u=np.sort(R*np.clip(np.asarray(a).reshape(-1,900)*amplitude,-1,1),axis=1)
    n,m=u.shape
    bl,bh=max(-(1-R),S-1),min(1-R,S)
    prefix=np.c_[np.zeros(n),np.cumsum(u,axis=1)]
    total=prefix[:,-1]
    def evaluate(lam):
        fraction=(1/eta-1/lam)/(1/eta-eta)
        if fraction<=0:b=np.full(n,bl)
        elif fraction>=1:b=np.full(n,bh)
        else:b=np.clip(u[:,max(0,min(m-1,int(np.ceil(fraction*m))-1))],bl,bh)
        count=np.sum(u<=b[:,None],axis=1)
        charge=(count*b-prefix[np.arange(n),count])/3600
        discharge=(total-prefix[np.arange(n),count]-(m-count)*b)/3600
        f=eta*charge-discharge/eta
        dual=float(np.sum(b*.25-lam*f))
        return dual,float(np.sum(f))
    if eta==1:
        h=float(S*n*.25-np.sum(total)/3600)
        return dict(upper_mwh=h,lossless_energy_identity=True)
    lo,hi=eta,1/eta
    best=(-np.inf,None,None)
    for _ in range(55):
        lam=(lo+hi)/2
        dual,f=evaluate(lam)
        if dual>best[0]:best=(dual,lam,f)
        # f increases with lambda; derivative of the concave dual is -sum f.
        if f<0:lo=lam
        else:hi=lam
    margin=1e-6
    return dict(upper_mwh=float(S*n*.25-best[0]+margin),dual_cost=best[0],
                multiplier=best[1],relaxed_inventory_residual=best[2],
                numerical_margin_mwh=margin,lossless_energy_identity=False)

if __name__=='__main__':
    a=np.load(ROOT/'temp/native_evaluation.npy',mmap_mode='r')
    rows=[]
    for eta,amp in [(.94,1.),(.9,1.),(.98,1.),(1.,1.),(.94,.8),(.94,1.2)]:
        r=bound(a,.1,eta=eta,amplitude=amp)
        r.update(eta=eta,amplitude=amp,supply_mw=.1,no_reserve_mwh=len(a)/3600*.1)
        rows.append(r);print(r,flush=True)
        (ROOT/'results/cyclic_energy_dual_challenge.json').write_text(json.dumps(rows,indent=2))
