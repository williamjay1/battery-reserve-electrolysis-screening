"""Mean-preserving rank summaries for a conservative cyclic-energy screen.

No chronological feasibility claim is made. Input u is sorted activation MW,
with one row per fixed-duration dispatch interval and equally weighted columns.
"""
import numpy as np

def summarize(sorted_u, k):
    n,m=sorted_u.shape
    if m%k: raise ValueError('k must divide interval sample count')
    return sorted_u.reshape(n,k,m//k).mean(axis=2)

def screen(u, S=.1, eta=.94, R=.75, interval_hours=.25):
    u=np.asarray(u,dtype=float)
    n,k=u.shape
    if not 0<eta<=1: raise ValueError('efficiency')
    if np.any(np.diff(u,axis=1)<-1e-12): raise ValueError('sorted rows required')
    bl,bh=max(-(1-R),S-1),min(1-R,S)
    if bl>bh: raise ValueError('empty baseline range')
    total=u.sum(axis=1); dt=interval_hours/k
    if eta==1:
        return dict(upper_mwh=float(S*n*interval_hours-total.sum()*dt),multiplier=1.,margin_mwh=0.)
    prefix=np.c_[np.zeros(n),np.cumsum(u,axis=1)]
    def value(lam):
        fraction=(1/eta-1/lam)/(1/eta-eta)
        if fraction<=0: b=np.full(n,bl)
        elif fraction>=1: b=np.full(n,bh)
        else: b=np.clip(u[:,min(k-1,max(0,int(np.ceil(fraction*k))-1))],bl,bh)
        count=(u<=b[:,None]).sum(axis=1)
        cp=prefix[np.arange(n),count]
        f=dt*(eta*(count*b-cp)-(total-cp-(k-count)*b)/eta)
        return float(np.sum(b*interval_hours-lam*f)),float(f.sum())
    lo,hi=eta,1/eta; best=(-np.inf,0.)
    for _ in range(55):
        lam=(lo+hi)/2; d,f=value(lam)
        if d>best[0]: best=(d,lam)
        if f<0: lo=lam
        else: hi=lam
    # Endpoints matter for degenerate distributions and baseline limits.
    for lam in (eta,1/eta):
        d,_=value(lam)
        if d>best[0]:best=(d,lam)
    return dict(upper_mwh=float(S*n*interval_hours-best[0]+1e-6),multiplier=best[1],margin_mwh=1e-6)
