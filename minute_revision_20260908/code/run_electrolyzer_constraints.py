from pathlib import Path
import json,time
import numpy as np,pandas as pd
from electrolyzer_constraints import constrained_day
ROOT=Path(__file__).resolve().parents[1]
configs=[(cap,s,m,dwell) for cap in (2.,4.,8.) for s in (.025,.05,.1,.2) for m,dwell in [(0.,0),(.05,4),(.1,4),(.2,4)]]
(ROOT/'results'/'electrolyzer_constraint_config.json').write_text(json.dumps(dict(capacities=[2,4,8],supply=[.025,.05,.1,.2],minimum_load_dwell_quarters=[[0,0],[.05,4],[.1,4],[.2,4]],reserve=.75,eta=.94,horizon_hours=1,interpretation='engineering sensitivities, not manufacturer-specific plant parameters'),indent=2))
rows=[];t0=time.perf_counter()
for source,folder,configfile in [('Germany_seconds','germany_seconds','germany_main_config.json'),('Belgium','belgium_quarters','belgium_validated_config.json')]:
    files=sorted((ROOT/'datasets'/folder).glob('*.npz'));scale=json.loads((ROOT/'results'/configfile).read_text())['scale_mw']
    states=np.array([[c[0]/2,0.,4.] for c in configs]);previous=None
    for di,f in enumerate(files):
        now=pd.Timestamp(f.stem);reset=previous is None or (now-previous).days!=1;previous=now
        if reset:states=np.array([[c[0]/2,0.,4.] for c in configs])
        a=np.clip(np.load(f)['mw']/scale,-1,1)
        if source=='Belgium':a=np.repeat(a,900)
        for k,(cap,s,m,dwell) in enumerate(configs):
            initial=states[k,0];out=constrained_day(a,cap,.75,.94,s,1.,m,dwell,*states[k]);states[k]=out[:3]
            rows.append((source,f.stem,cap,s,m,dwell,*out,initial,len(a)/3600,reset))
        if di%120==0:print(source,di+1,round(time.perf_counter()-t0,1),flush=True)
cols=['source','day','capacity_mwh','supply_mw','minimum_load_mw','dwell_quarters','actual_state_mwh','last_hydrogen_power_mw','state_age_quarters','deficit_mwh','request_mwh','hydrogen_energy_mwh','startups','on_hours','max_balance_error','constraint_violations','initial_inventory_mwh','hours','episode_restart']
d=pd.DataFrame(rows,columns=cols);d.to_csv(ROOT/'results'/'electrolyzer_constraints_daily.csv.gz',index=False)
assert d.constraint_violations.sum()==0
assert d.max_balance_error.max()<1e-10
(ROOT/'results'/'electrolyzer_constraints_audit.json').write_text(json.dumps(dict(rows=len(d),constraint_violations=int(d.constraint_violations.sum()),max_balance_error=float(d.max_balance_error.max()),status='PASS'),indent=2))
print('COMPLETE',len(d),flush=True)
