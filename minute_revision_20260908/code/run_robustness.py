"""Efficiency and feedback-speed challenges, retaining every result."""
from pathlib import Path
import json,time
import numpy as np,pandas as pd
from integrated_replay import replay_day
ROOT=Path(__file__).resolve().parents[1]
files=sorted((ROOT/'datasets'/'germany_seconds').glob('*.npz'))
assert len(files)==577
scale=json.loads((ROOT/'results'/'germany_main_config.json').read_text())['scale_mw']
models=[('native',1,0),('minute',60,0),('5minute',300,0),('quarter',900,0),('gross',900,1),('envelope',900,2)]
factors=[(.9,1.),(.98,1.),(1.,1.),(.94,.25),(.94,4.)]
configs=[(cap,eta,horizon,measured,label,step,mode) for cap in (.5,1.,2.) for eta,horizon in factors for measured in (False,True) for label,step,mode in models]
(ROOT/'results'/'robustness_config.json').write_text(json.dumps(dict(scale_mw=scale,capacities_mwh=[.5,1.,2.],eta_horizon_factors=factors,feedback=['modeled','measured'],reserve_mw=.75,supply_mw=.5,models=models),indent=2))
states=np.array([[c[0]/2,c[0]/2] for c in configs]);rows=[];t0=time.perf_counter()
for di,f in enumerate(files):
    a=np.clip(np.load(f)['mw']/scale,-1,1)
    for k,(cap,eta,horizon,measured,label,step,mode) in enumerate(configs):
        initial=states[k,1]
        out=replay_day(a,cap,.75,eta,.5,horizon,step,mode,*states[k],measured);states[k]=out[:2]
        rows.append((f.stem,cap,eta,horizon,measured,label,*out,initial))
    if di%60==0:print('robustness days',di+1,'seconds',round(time.perf_counter()-t0,1),flush=True)
columns=['day','capacity_mwh','eta','horizon_hours','measured_feedback','model','predicted_state_mwh','actual_state_mwh','native_deficit_mwh','predicted_deficit_mwh','baseline_charge_mwh','hydrogen_energy_mwh','requested_reserve_mwh','maximum_state_error_mwh','fallback_quarters','initial_actual_state_mwh']
d=pd.DataFrame(rows,columns=columns);d.to_csv(ROOT/'results'/'robustness_daily.csv.gz',index=False)
keys=['day','capacity_mwh','eta','horizon_hours','measured_feedback']
n=d[d.model.eq('native')].set_index(keys).sort_index();e=d[d.model.eq('envelope')].set_index(keys).sort_index()
error=float(np.max(np.abs(n.actual_state_mwh-e.actual_state_mwh)));assert error<1e-7
(ROOT/'results'/'robustness_audit.json').write_text(json.dumps(dict(rows=len(d),configurations=len(configs),max_native_envelope_state_error=error,status='PASS'),indent=2))
print('COMPLETE',len(d),flush=True)
