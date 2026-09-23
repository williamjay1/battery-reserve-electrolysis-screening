"""Independent physical sign-region enumeration for generic decision duration."""
import itertools, json, time
import numpy as np
from scipy.optimize import linprog
from run_interval_bounds import supports, solve_endpoint, capfree, OUT, R, S, ETA, BL, BH
from hydrogen_lp_pilot import optimize

def physical_exact(a,step,cap):
    n=len(a)//step
    cuts=[]
    for q in range(n):
        u=R*a[q*step:(q+1)*step]
        c=np.unique(np.r_[BL,u[(u>BL)&(u<BH)],BH])
        cuts.append(list(zip(c[:-1],c[1:])))
    best=np.inf;feasible_regions=0
    for bounds in itertools.product(*cuts):
        mid=np.mean(bounds,axis=1)
        coeff=np.zeros(n);constant=0.;rows=[];rhs=[]
        for i,v in enumerate(a):
            q=i//step;scale=1/ETA if R*v-mid[q]>=0 else ETA
            coeff[q]+=scale/3600;constant-=R*v*scale/3600
            rows.extend([coeff.copy(),-coeff.copy()])
            rhs.extend([cap/2-constant,cap/2+constant])
        z=linprog(np.full(n,step/3600),A_ub=rows,b_ub=rhs,
                  A_eq=coeff[None,:],b_eq=[-constant],bounds=bounds,
                  method='highs',options={'threads':1,'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
        if z.success:feasible_regions+=1;best=min(best,z.fun)
    return None if not np.isfinite(best) else S*len(a)/3600-best,feasible_regions

if __name__=='__main__':
    t=time.perf_counter();rng=np.random.default_rng(23092026);records=[]
    for case in range(12):
        step=[2,3,4][case%3];n=3;cap=.0003+(case%4)*.0003
        a=rng.uniform(-.5,.5,n*step);a-=a.mean()+.03
        physical,regions=physical_exact(a,step,cap)
        knots=np.tile(np.r_[BL,BH,np.linspace(BL,BH,9)[1:-1]],(n,1))
        fs,cs=supports(a,knots,step)
        try:upper,_,_=solve_endpoint(fs,cs,knots,E=cap,step=step)
        except AssertionError:
            assert physical is None
            records.append(dict(case=case,step=step,cap=cap,physical='infeasible',relaxation='infeasible'));continue
        cf=capfree(a,step)['capacity_free_upper_mwh']
        if physical is not None:
            assert upper['hydrogen_upper_mwh']+1e-8>=physical,(case,upper,physical)
            assert cf+1e-8>=physical,(case,cf,physical)
        # Independent exact coarse routine uses the actual duration, not .25 h.
        co=optimize(a.reshape(-1,step).mean(axis=1),cap,R,S,ETA,step/3600)
        records.append(dict(case=case,step=step,cap=cap,physical_optimum_mwh=physical,
                            feasible_regions=regions,finite_cap_upper_mwh=upper['hydrogen_upper_mwh'],
                            capacity_free_upper_mwh=cf,coarse_success=co['success']))
    report=dict(status='PASS',cases=len(records),seed=23092026,seconds=time.perf_counter()-t,records=records)
    (OUT/'small_instance_audit.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
