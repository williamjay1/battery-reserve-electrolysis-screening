"""Frozen full-factor integrated replay; calibration scaling uses 2025 H1 only."""
from pathlib import Path
import time,json
import numpy as np
import pandas as pd
from integrated_replay import replay_day
ROOT=Path(__file__).resolve().parents[1]
files=sorted((ROOT/'datasets'/'germany_seconds').glob('*.npz'))
expected=pd.date_range('2025-01-01','2026-07-31',freq='D').strftime('%Y-%m-%d').tolist()
assert [f.stem for f in files]==expected,'Complete nineteen-month native cache required'
cal=np.concatenate([np.load(f)['mw'] for f in files if f.stem<'2025-07-01'])
scale=float(np.quantile(np.abs(cal),.995));del cal
models=[('native',1,0),('minute',60,0),('5minute',300,0),('quarter',900,0),('gross',900,1),('envelope',900,2)]
configs=[(cap,r,supply,label,step,mode) for cap in (.25,.5,1.,2.,4.) for r in (.25,.5,.75) for supply in (.25,.5,.75) for label,step,mode in models]
config=dict(stage='measured-state feedback sensitivity',coverage=[expected[0],expected[-1]],normalization='2025 H1 absolute 99.5 percentile; clipped signed setpoint',scale_mw=scale,eta=.94,horizon_hours=1.,capacity_mwh=[.25,.5,1.,2.,4.],reserve_mw=[.25,.5,.75],scheduled_supply_mw=[.25,.5,.75],inverter_mw=1.,electrolyzer_mw=1.,models=models,reliability_thresholds=[.001,.005,.01],primary_threshold=.005,uncertainty='paired calendar 7-day block bootstrap; 3/14-day sensitivity',interpretation='system signal stress replay, not participant activation or qualification')
(ROOT/'results'/'germany_measured_config.json').write_text(json.dumps(config,indent=2))
state=np.array([[c[0]/2,c[0]/2] for c in configs]);rows=[];t0=time.perf_counter()
for di,f in enumerate(files):
    raw=np.load(f)['mw'];a=np.clip(raw/scale,-1,1)
    for k,(cap,r,supply,label,step,mode) in enumerate(configs):
        initial_actual=state[k,1]
        out=replay_day(a,cap,r,.94,supply,1.,step,mode,state[k,0],state[k,1],True);state[k]=out[:2]
        rows.append((f.stem,cap,r,supply,label,*out,initial_actual,len(a)/3600,int((np.abs(raw)>scale).sum())))
    if di%30==0:print('days',di+1,'elapsed',round(time.perf_counter()-t0,1),flush=True)
columns=['day','capacity_mwh','reserve_mw','supply_mw','model','predicted_state_mwh','actual_state_mwh','native_deficit_mwh','predicted_deficit_mwh','baseline_charge_mwh','hydrogen_energy_mwh','requested_reserve_mwh','maximum_state_error_mwh','fallback_quarters','initial_actual_state_mwh','hours','clipped_signal_seconds']
df=pd.DataFrame(rows,columns=columns);df.to_csv(ROOT/'results'/'germany_measured_daily.csv.gz',index=False)
# Equality is a required invariant over every configuration and day, not a selected example.
keys=['day','capacity_mwh','reserve_mw','supply_mw']
n=df[df.model=='native'].set_index(keys).sort_index();e=df[df.model=='envelope'].set_index(keys).sort_index()
errors={c:float(np.max(np.abs(n[c]-e[c]))) for c in ['actual_state_mwh','native_deficit_mwh','baseline_charge_mwh','hydrogen_energy_mwh']}
assert max(errors.values())<1e-7,errors
(ROOT/'results'/'germany_measured_audit.json').write_text(json.dumps(dict(days=len(files),configurations=len(configs),rows=len(df),elapsed_seconds=time.perf_counter()-t0,native_envelope_max_errors=errors,status='PASS'),indent=2))
print('COMPLETE',len(df),errors,flush=True)

