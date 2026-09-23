"""Targeted capacity and native-prefix tests; synthetic fixtures only."""
import json
import numpy as np
from audit_small_instances import physical_exact
from run_interval_bounds import BL,BH,OUT,supports,solve_endpoint,capfree

def evaluate(a,step,cap,case):
    exact,regions=physical_exact(a,step,cap)
    n=len(a)//step;knots=np.tile(np.r_[BL,BH,np.linspace(BL,BH,33)[1:-1]],(n,1))
    fs,cs=supports(a,knots,step)
    try:up,_,_=solve_endpoint(fs,cs,knots,E=cap,step=step)
    except AssertionError:
        assert exact is None
        return None
    cf=capfree(a,step)['capacity_free_upper_mwh']
    if exact is not None:
        assert exact<=up['hydrogen_upper_mwh']+1e-8
        assert exact<=cf+1e-8
    return dict(case=case,activation=a.tolist(),step=step,capacity_mwh=cap,
                physical_optimum_mwh=exact,feasible_regions=regions,
                finite_cap_upper_mwh=up['hydrogen_upper_mwh'],capacity_free_upper_mwh=cf,
                upper_bound_improvement_mwh=cf-up['hydrogen_upper_mwh'])

if __name__=='__main__':
    prefix=evaluate(np.array([.8,-.8,.8,-.8]),4,.00005,'prefix makes endpoint-feasible case physically infeasible')
    assert prefix is not None and prefix['physical_optimum_mwh'] is None
    rng=np.random.default_rng(3902309);active=[];attempted=0
    for attempted in range(1,81):
        a=rng.uniform(-.55,.55,12);a-=a.mean()+.02
        rec=evaluate(a,3,.00012+(attempted%3)*.00003,f'capacity fixture seed3902309 draw{attempted}')
        if rec and rec['physical_optimum_mwh'] is not None and rec['upper_bound_improvement_mwh']>1e-7:
            active.append(rec)
            if len(active)==2:break
    assert len(active)==2,(attempted,len(active))
    report=dict(status='PASS',test_purpose='adversarial synthetic checks of constraints, not empirical evidence',
                seed=3902309,search_draws=attempted,prefix_fixture=prefix,capacity_active_fixtures=active)
    (OUT/'active_constraint_audit.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
