"""Native sample zero-deficit reachability with quarter-constant baseline.

An offline feasibility comparator. No clipping or simultaneous charge/discharge.
The monotone constraint and connected-image proof is documented separately.
"""
import numpy as np
from numba import njit

@njit(cache=True)
def features(a,start,stop,b,reserve,eta,dt):
    total=0.;lo=0.;hi=0.;rise=0.;draw=0.
    for i in range(start,stop):
        p=reserve*a[i]-b
        total+=(-p/eta if p>=0 else -p*eta)*dt
        rise=max(rise,total-lo);draw=max(draw,hi-total)
        lo=min(lo,total);hi=max(hi,total)
    return total,lo,hi,rise,draw

@njit(cache=True)
def interval_step(a,start,stop,bl,bh,cap,L,U,reserve,eta,dt,tol=1e-10):
    if L>U or L<0 or U>cap or bl>bh:raise ValueError('Invalid initial interval or baseline bounds')
    f0=features(a,start,stop,bl,reserve,eta,dt)
    f1=features(a,start,stop,bh,reserve,eta,dt)
    # Increasing b reduces the initial inventory needed and any forward drawdown.
    if f1[1]<-U-tol or f1[4]>cap+tol:return False,0.,0.,0.,0.
    # Increasing b increases the maximum excursion and any forward rise.
    if f0[2]>cap-L+tol or f0[3]>cap+tol:return False,0.,0.,0.,0.
    low=bl
    if f0[1]<-U or f0[4]>cap:
        l=bl;r=bh
        for _ in range(38):
            m=(l+r)*.5;f=features(a,start,stop,m,reserve,eta,dt)
            if f[1]<-U or f[4]>cap:l=m
            else:r=m
        low=r
    high=bh
    if f1[2]>cap-L or f1[3]>cap:
        l=bl;r=bh
        for _ in range(38):
            m=(l+r)*.5;f=features(a,start,stop,m,reserve,eta,dt)
            if f[2]>cap-L or f[3]>cap:r=m
            else:l=m
        high=l
    if low>high+tol:return False,0.,0.,0.,0.
    if low>high:low=high=(low+high)*.5
    fl=features(a,start,stop,low,reserve,eta,dt)
    fh=features(a,start,stop,high,reserve,eta,dt)
    nextL=max(L,-fl[1])+fl[0]
    nextU=min(U,cap-fh[2])+fh[0]
    nextL=max(0.,nextL);nextU=min(cap,nextU)
    if nextL>nextU:
        if nextL-nextU>tol:return False,0.,0.,0.,0.
        nextL=nextU=min(cap,max(0.,(nextL+nextU)*.5))
    return True,nextL,nextU,low,high

@njit(cache=True)
def reach(a,cap,reserve,eta,supply,hfloor,initial_low,initial_high,step=900,dt=1/3600):
    if step<=0 or len(a)%step!=0:raise ValueError('Incomplete decision interval')
    if not (cap>0 and 0<eta<=1 and 0<=reserve<=1 and 0<=hfloor<=1):raise ValueError('Invalid physical parameters')
    if initial_low>initial_high or initial_low<0 or initial_high>cap:raise ValueError('Invalid initial inventory')
    n=len(a)//step
    ls=np.empty(n+1);us=np.empty(n+1);bslo=np.empty(n);bshi=np.empty(n)
    ls[0]=initial_low;us[0]=initial_high
    bl=max(-(1-reserve),supply-1);bh=min(1-reserve,supply-hfloor)
    if bl>bh:return False,0,ls[:1],us[:1],bslo[:0],bshi[:0]
    for q in range(n):
        ok,l,u,blo,bhi=interval_step(a,q*step,(q+1)*step,bl,bh,cap,ls[q],us[q],reserve,eta,dt)
        if not ok:return False,q,ls[:q+1],us[:q+1],bslo[:q],bshi[:q]
        ls[q+1]=l;us[q+1]=u;bslo[q]=blo;bshi[q]=bhi
    return True,n,ls,us,bslo,bshi

@njit(cache=True)
def reconstruct(a,cap,reserve,eta,ls,us,bslo,bshi,terminal,step=900,dt=1/3600):
    if terminal<ls[-1]-1e-9 or terminal>us[-1]+1e-9:raise ValueError('Unreachable terminal inventory')
    n=len(bslo);bseq=np.empty(n);sseq=np.empty(n+1);sseq[n]=terminal
    for q in range(n-1,-1,-1):
        target=sseq[q+1];l=bslo[q];r=bshi[q]
        # Smallest feasible baseline whose upper endpoint reaches target.
        for _ in range(40):
            m=(l+r)*.5;f=features(a,q*step,(q+1)*step,m,reserve,eta,dt)
            upper=min(us[q],cap-f[2])+f[0]
            if upper<target:l=m
            else:r=m
        bseq[q]=r
        f=features(a,q*step,(q+1)*step,bseq[q],reserve,eta,dt)
        sseq[q]=target-f[0]
    return bseq,sseq

@njit(cache=True)
def audit_schedule(a,bseq,s0,cap,reserve,eta,supply,hfloor,step=900,dt=1/3600):
    s=s0;smin=s;smax=s;gross_h=0.;max_headroom=0.;min_h=1.;max_h=0.
    for q in range(len(bseq)):
        b=bseq[q];h=supply-b;gross_h+=h*step*dt;min_h=min(min_h,h);max_h=max(max_h,h)
        max_headroom=max(max_headroom,abs(b)+reserve)
        for j in range(q*step,(q+1)*step):
            p=reserve*a[j]-b
            s+=(-p/eta if p>=0 else -p*eta)*dt
            smin=min(smin,s);smax=max(smax,s)
    violation=max(0.,-smin,smax-cap,max_headroom-1,hfloor-min_h,max_h-1)
    return s,smin,smax,gross_h,violation
