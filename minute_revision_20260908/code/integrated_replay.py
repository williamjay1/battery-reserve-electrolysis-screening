"""Quarter-announced baseline; simultaneous model and native physical audit."""
import numpy as np
from numba import njit

@njit(cache=True)
def advance(s,p,dt,eta,cap):
    inc=-p*dt/eta if p>=0 else -p*dt*eta
    nxt=min(cap,max(0.,s+inc))
    actual=-(nxt-s)*eta/dt if nxt<=s else -(nxt-s)/eta/dt
    return nxt,abs(p-actual)*dt

@njit(cache=True)
def replay_day(a,cap,reserve,eta,supply,horizon,seconds,mode,pred,actual,measured_feedback=False):
    # mode 0: ordinary replay at seconds; 1: gross energy; 2: envelope.
    native_loss=0.;pred_loss=0.;charge=0.;hydrogen_energy=0.;request=0.;max_error=0.;fallbacks=0
    for q in range(len(a)//900):
        if measured_feedback:pred=actual
        lower=max(-(1-reserve),supply-1.)
        upper=min(1-reserve,supply)
        desired=(cap*.5-pred)/horizon
        b=min(upper,max(lower,desired))
        hydrogen_energy+=(supply-b)*.25;charge+=b*.25
        start=q*900
        delta=0.;lo=0.;hi=0.
        for j in range(900):
            p=reserve*a[start+j]-b
            actual,loss=advance(actual,p,1/3600,eta,cap)
            native_loss+=loss;request+=abs(reserve*a[start+j])/3600
            inc=-p/3600/eta if p>=0 else -p/3600*eta
            delta+=inc;lo=min(lo,delta);hi=max(hi,delta)
        if mode==2 and pred+lo>=0 and pred+hi<=cap:
            pred+=delta
        elif mode==1:
            # Gross-flow baseline preserves endpoint energy but loses ordering.
            pred=min(cap,max(0.,pred+delta))
        else:
            step=seconds if mode==0 else 1
            if mode==2:fallbacks+=1
            for j in range(0,900,step):
                p=0.
                for k in range(step):p+=reserve*a[start+j+k]-b
                p/=step
                pred,loss=advance(pred,p,step/3600,eta,cap);pred_loss+=loss
        max_error=max(max_error,abs(actual-pred))
    return pred,actual,native_loss,pred_loss,charge,hydrogen_energy,request,max_error,fallbacks
