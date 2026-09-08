"""Matched 15-minute source challenge, including explicit gap restarts."""
from pathlib import Path
import json,time
import numpy as np,pandas as pd
from integrated_replay import replay_day
ROOT=Path(__file__).resolve().parents[1]
configs=[(cap,r,s) for cap in (.5,1.,2.,4.,8.) for r in (.25,.5,.75) for s in (0.,.025,.05,.1,.2,.4)]
rows=[];t0=time.perf_counter()
for source,folder,configfile in [('Belgium','belgium_quarters','belgium_validated_config.json'),('Germany_15min','germany_seconds','germany_main_config.json')]:
    files=sorted((ROOT/'datasets'/folder).glob('*.npz'));scale=json.loads((ROOT/'results'/configfile).read_text())['scale_mw']
    states=np.array([[c[0]/2,c[0]/2] for c in configs]);previous=None
    for di,f in enumerate(files):
        now=pd.Timestamp(f.stem);reset=previous is None or (now-previous).days!=1;previous=now
        if reset:states=np.array([[c[0]/2,c[0]/2] for c in configs])
        raw=np.load(f)['mw']
        if source=='Belgium':a=np.repeat(np.clip(raw/scale,-1,1),900)
        else:
            # Average already-normalized native stress, preserving its quarter energy.
            a=np.repeat(np.clip(raw/scale,-1,1).reshape(-1,900).mean(axis=1),900)
        for k,(cap,r,s) in enumerate(configs):
            initial=states[k,1];out=replay_day(a,cap,r,.94,s,1.,1,0,*states[k],True);states[k]=out[:2]
            rows.append((source,f.stem,cap,r,s,*out,initial,len(a)/3600,reset))
        if di%120==0:print(source,di+1,round(time.perf_counter()-t0,1),flush=True)
cols=['source','day','capacity_mwh','reserve_mw','supply_mw','predicted_state_mwh','actual_state_mwh','native_deficit_mwh','predicted_deficit_mwh','baseline_charge_mwh','hydrogen_energy_mwh','requested_reserve_mwh','maximum_state_error_mwh','fallback_quarters','initial_actual_state_mwh','hours','episode_restart']
d=pd.DataFrame(rows,columns=cols);d.to_csv(ROOT/'results'/'cross_source_daily.csv.gz',index=False)
assert d.maximum_state_error_mwh.max()<1e-8
d['period']=np.where(d.day<'2025-07-01','calibration',np.where(d.day<'2026-01-01','development','evaluation'))
g=d.groupby(['source','period','capacity_mwh','reserve_mw','supply_mw']).agg(deficit_mwh=('native_deficit_mwh','sum'),request_mwh=('requested_reserve_mwh','sum'),hydrogen_energy_mwh=('hydrogen_energy_mwh','sum'),hours=('hours','sum'),restarts=('episode_restart','sum')).reset_index()
g['deficit_pct']=100*g.deficit_mwh/g.request_mwh;g.to_csv(ROOT/'results'/'cross_source_summary.csv',index=False)
print('COMPLETE',len(d),flush=True)
