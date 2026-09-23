"""Exact sparse flow form of the interval-constant coarse energy LP.

For cyclic inventory and u=R*a, cost sum(b*dt) = sum(u*dt)
 + (1/eta-eta)*sum(positive inventory increments). Continuous charge and
discharge flow variables never simultaneously carry at an optimum, because
their simultaneous reduction leaves inventory unchanged and reduces cost.
"""
import argparse,time
import numpy as np
from scipy.sparse import coo_matrix
from scipy.optimize import linprog
from run_interval_bounds import INPUT, OUT, E, R, S, ETA, BL, BH, save

def coarse_network(a,step):
    started=time.perf_counter();dt=step/3600
    u=R*np.asarray(a).reshape(-1,step).mean(axis=1);n=len(u);s0=E/2
    def increment(b):
        p=u-b;return np.where(p>=0,-p/ETA,-p*ETA)*dt
    low=increment(BL);high=increment(BH)
    lower=np.r_[np.zeros(n-1),s0,np.maximum(low,0),np.maximum(-high,0)]
    upper=np.r_[np.full(n-1,E),s0,np.maximum(high,0),np.maximum(-low,0)]
    q=np.arange(n)
    rows=np.r_[q,q[1:],q,q];cols=np.r_[q,q[1:]-1,n+q,2*n+q]
    values=np.r_[np.ones(n),-np.ones(n-1),-np.ones(n),np.ones(n)]
    A=coo_matrix((values,(rows,cols)),shape=(n,3*n)).tocsr()
    rhs=np.zeros(n);rhs[0]=s0
    # Scale objective to integer coefficients for conditioning.
    c=np.r_[np.zeros(n),np.ones(n),np.zeros(n)]
    out=linprog(c,A_eq=A,b_eq=rhs,bounds=np.c_[lower,upper],method='highs-ipm',
        options={'threads':1,'time_limit':900.,'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8})
    assert out.success,out.message
    y=out.eqlin.marginals;residual=c-A.T@y
    dual=float(rhs@y+lower@np.maximum(residual,0)+upper@np.minimum(residual,0))
    states=np.r_[s0,out.x[:n]];delta=np.diff(states)
    b=u+np.where(delta>=0,delta/(ETA*dt),delta*ETA/dt)
    physical=increment(b);replay=s0+np.cumsum(physical)
    simultaneous=float(np.max(np.minimum(out.x[n:2*n],out.x[2*n:])))
    violation=float(max(0.,-replay.min(),replay.max()-E,abs(replay[-1]-s0),np.max(BL-b),np.max(b-BH)))
    assert simultaneous<1e-7 and violation<1e-6,(simultaneous,violation)
    signed=float(np.sum(u)*dt);beta=1/ETA-ETA
    cost=signed+beta*float(out.fun);dual_cost=signed+beta*dual
    objective=float(np.sum(S-b)*dt)
    assert abs(objective-(S*n*dt-cost))<1e-6
    report=dict(step_seconds=step,capacity_mwh=E,supply_mw=S,intervals=n,method='exact network LP, highs-ipm',
        exact_coarse_mwh=objective,hydrogen_upper_mwh=S*n*dt-dual_cost+1e-6,
        primal_objective=cost,dual_lower_objective=dual_cost,duality_gap=cost-dual_cost,
        maximum_equation_residual=float(np.max(np.abs(delta-physical))),
        maximum_replay_violation=violation,max_simultaneous_inventory_flow=simultaneous,
        max_equality_residual=float(np.max(np.abs(A@out.x-rhs))),
        max_full_stationarity_residual=float(np.max(np.abs(residual-out.lower.marginals-out.upper.marginals))),
        roundoff_margin_mwh=1e-6,iterations=int(out.nit),total_seconds=time.perf_counter()-started)
    np.savez_compressed(OUT/f'interval_{step}s_coarse_network.npz',baseline=b,states=states)
    save(f'interval_{step}s_coarse_network.json',report)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--step',type=int,default=900);args=p.parse_args()
    a=np.load(INPUT,mmap_mode='r');coarse_network(a,args.step)
