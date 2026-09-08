"""Quarter-boundary load projection with minimum on/off residence times."""
import numpy as np
from numba import njit
from integrated_replay import advance

@njit(cache=True)
def constrained_day(a,cap,reserve,eta,supply,horizon,minload,dwell,s,previous_h,age):
    loss=0.;request=0.;hydrogen=0.;starts=0;onquarters=0;max_balance=0.;violations=0
    for q in range(len(a)//900):
        desired_b=(cap*.5-s)/horizon
        h_low=max(0.,supply-(1-reserve));h_high=min(1.,supply+1-reserve)
        desired_h=supply-desired_b
        if minload==0:
            h=min(h_high,max(h_low,desired_h))
        else:
            onlow=max(h_low,minload);onhigh=h_high
            onallowed=onlow<=onhigh
            offallowed=h_low<=1e-12
            wason=previous_h>1e-12
            if age<dwell:
                if wason:offallowed=False
                else:onallowed=False
            if onallowed:
                candidate=min(onhigh,max(onlow,desired_h))
            else:candidate=0.
            if offallowed and (not onallowed or abs(desired_h)<=abs(candidate-desired_h)):
                h=0.
            elif onallowed:h=candidate
            else:
                violations+=1;h=min(h_high,max(h_low,desired_h))
        ison=h>1e-12;wason=previous_h>1e-12
        if ison!=wason:
            if minload>0 and age<dwell:violations+=1
            age=1
            if ison:starts+=1
        else:age+=1
        previous_h=h;onquarters+=int(ison)
        b=supply-h;hydrogen+=h*.25
        if abs(b)+reserve>1+1e-10:violations+=1
        if minload>0 and h>1e-12 and h<minload-1e-10:violations+=1
        for j in range(900):
            p=reserve*a[q*900+j]-b
            max_balance=max(max_balance,abs(supply+p-h-reserve*a[q*900+j]))
            s,e=advance(s,p,1/3600,eta,cap);loss+=e;request+=abs(reserve*a[q*900+j])/3600
    return s,previous_h,age,loss,request,hydrogen,starts,onquarters*.25,max_balance,violations
