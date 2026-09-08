"""Exact fixed-baseline interval certificates, including the entry state."""
import numpy as np
from numba import njit

@njit(cache=True)
def certificate(power,dt,eta):
    total=0.;lower=0.;upper=0.;charge=0.;discharge=0.
    for p in power:
        if p>=0:
            discharge+=p*dt;total-=p*dt/eta
        else:
            charge-=p*dt;total-=p*dt*eta
        lower=min(lower,total);upper=max(upper,total)
    return total,lower,upper,charge,discharge

@njit(cache=True)
def native_clip(power,dt,eta,initial,capacity):
    state=initial;shortfall=0.
    for p in power:
        if p>=0:
            served=min(p,state*eta/dt)
            state-=served*dt/eta;shortfall+=(p-served)*dt
        else:
            served=min(-p,(capacity-state)/eta/dt)
            state+=served*dt*eta;shortfall+=(-p-served)*dt
    return state,shortfall

def screen(power,dt,eta,initial,capacity):
    delta,lo,hi,_,_=certificate(power,dt,eta)
    if initial+lo>=0 and initial+hi<=capacity:
        return initial+delta,0.,False
    final,shortfall=native_clip(power,dt,eta,initial,capacity)
    return final,shortfall,True
