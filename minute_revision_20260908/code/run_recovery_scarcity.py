"""Native measured-state challenge of recovery supply vs storage capacity."""
from pathlib import Path
import json,time
import numpy as np,pandas as pd
from integrated_replay import replay_day
ROOT=Path(__file__).resolve().parents[1]
files=sorted((ROOT/'datasets'/'germany_seconds').glob('*.npz'));assert len(files)==577
scale=json.loads((ROOT/'results'/'germany_main_config.json').read_text())['scale_mw']
configs=[(cap,r,s) for cap in (.5,1.,2.,4.,8.) for r in (.25,.5,.75) for s in (0.,.025,.05,.1,.2,.4)]
(ROOT/'results'/'recovery_scarcity_config.json').write_text(json.dumps(dict(capacity_mwh=[.5,1,2,4,8],reserve_mw=[.25,.5,.75],supply_mw=[0,.025,.05,.1,.2,.4],eta=.94,horizon_hours=1,feedback='measured',normalization_mw=scale),indent=2))
states=np.array([[c[0]/2,c[0]/2] for c in configs]);rows=[];t0=time.perf_counter()
for di,f in enumerate(files):
    a=np.clip(np.load(f)['mw']/scale,-1,1)
    for k,(cap,r,s) in enumerate(configs):
        initial=states[k,1];out=replay_day(a,cap,r,.94,s,1.,1,0,*states[k],True);states[k]=out[:2]
        rows.append((f.stem,cap,r,s,*out,initial,len(a)/3600))
    if di%60==0:print('scarcity days',di+1,'seconds',round(time.perf_counter()-t0,1),flush=True)
cols=['day','capacity_mwh','reserve_mw','supply_mw','predicted_state_mwh','actual_state_mwh','native_deficit_mwh','predicted_deficit_mwh','baseline_charge_mwh','hydrogen_energy_mwh','requested_reserve_mwh','maximum_state_error_mwh','fallback_quarters','initial_actual_state_mwh','hours']
d=pd.DataFrame(rows,columns=cols);d.to_csv(ROOT/'results'/'recovery_scarcity_daily.csv.gz',index=False)
assert d.maximum_state_error_mwh.max()<1e-8
print('COMPLETE',len(d),flush=True)
