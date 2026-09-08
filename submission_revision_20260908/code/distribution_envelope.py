"""Two-sided bounds on the capacity-free dual optimum, NOT finite dispatch."""
import numpy as np

def weighted_bound(z,w,S=.1,eta=.94,R=.75,Delta=.25):
    z=np.asarray(z); w=np.asarray(w)
    assert z.shape==w.shape and np.all(w>=0) and np.max(abs(w.sum(axis=1)-1))<1e-10
    n,m=z.shape;bl,bh=max(R-1,S-1),min(1-R,S)
    w=w/w.sum(axis=1,keepdims=True)
    cw=np.cumsum(w,axis=1);cw[:,-1]=1.;cu=np.cumsum(w*z,axis=1)
    total=cu[:,-1];cw=np.c_[np.zeros(n),cw];cu=np.c_[np.zeros(n),cu]
    if eta==1:return float(S*n*Delta-total.sum()*Delta)
    def value(lam):
        fraction=(1/eta-1/lam)/(1/eta-eta)
        if fraction<=0:b=np.full(n,bl)
        elif fraction>=1:b=np.full(n,bh)
        else:
            idx=(cw[:,1:]>=fraction).argmax(axis=1)
            b=np.clip(z[np.arange(n),idx],bl,bh)
        count=(z<=b[:,None]).sum(axis=1)
        weight=cw[np.arange(n),count];part=cu[np.arange(n),count]
        f=Delta*(eta*(weight*b-part)-(total-part-(1-weight)*b)/eta)
        return float(np.sum(b*Delta-lam*f)),float(f.sum())
    lo,hi=eta,1/eta;best=-np.inf
    for _ in range(55):
        lam=(lo+hi)/2;d,f=value(lam);best=max(best,d)
        if f<0:lo=lam
        else:hi=lam
    best=max(best,value(eta)[0],value(1/eta)[0])
    return float(S*n*Delta-best)

def envelope(sorted_u,k,S=.1,eta=.94,R=.75):
    n,m=sorted_u.shape;assert m%k==0
    g=sorted_u.reshape(n,k,m//k)
    avg=g.mean(axis=2);lo=g[:,:,0];hi=g[:,:,-1]
    frac=np.divide(hi-avg,hi-lo,out=np.ones_like(avg),where=hi>lo)
    frac=np.clip(frac,0,1)
    endpoints=np.stack([lo,hi],axis=2).reshape(n,2*k)
    weights=np.stack([frac,1-frac],axis=2).reshape(n,2*k)/k
    meanU=weighted_bound(avg,np.full_like(avg,1/k),S,eta,R)
    endpointU=weighted_bound(endpoints,weights,S,eta,R)
    return dict(lower_relaxed_mwh=endpointU-1e-6,upper_relaxed_mwh=meanU+1e-6,
                gap_mwh=meanU-endpointU+2e-6,summary_values=n*k*3)
