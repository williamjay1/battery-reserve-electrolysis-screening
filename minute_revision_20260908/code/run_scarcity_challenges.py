"""Binding-supply feedback-speed and signal-scale challenges."""
from pathlib import Path
import json,time
import numpy as np,pandas as pd
from electrolyzer_constraints import constrained_day
ROOT=Path(__file__).resolve().parents[1]
variants=[('reference',1.,1.),('fast_feedback',.25,1.),('slow_feedback',4.,1.),('low_signal',1.,.8),('high_signal',1.,1.2)]
configs=[(cap,s,label,horizon,mult) for cap in (2.,4.,8.) for s in (.025,.05,.1,.2) for label,horizon,mult in variants]
(ROOT/'results'/'scarcity_challenges_config.json').write_text(json.dumps(dict(variants=variants,capacity_mwh=[2,4,8],supply_mw=[.025,.05,.1,.2],signal_policy='multiply raw signal before calibration-scale clipping; scenario sensitivity, not refitted normalization'),indent=2))
rows=[];t0=time.perf_counter()
for source,folder,cfg in [('Germany_seconds','germany_seconds','germany_main_config.json'),('Belgium','belgium_quarters','belgium_validated_config.json')]:
    files=sorted((ROOT/'datasets'/folder).glob('*.npz'));scale=json.loads((ROOT/'results'/cfg).read_text())['scale_mw'];states=np.array([[c[0]/2,0.,4.] for c in configs]);previous=None
    for di,f in enumerate(files):
        now=pd.Timestamp(f.stem);reset=previous is None or (now-previous).days!=1;previous=now
        if reset:states=np.array([[c[0]/2,0.,4.] for c in configs])
        raw=np.load(f)['mw'];signals={mult:np.clip(raw*mult/scale,-1,1) for mult in (.8,1.,1.2)}
        if source=='Belgium':signals={k:np.repeat(v,900) for k,v in signals.items()}
        for k,(cap,s,label,horizon,mult) in enumerate(configs):
            initial=states[k,0];out=constrained_day(signals[mult],cap,.75,.94,s,horizon,0.,0,*states[k]);states[k]=out[:3]
            rows.append((source,f.stem,cap,s,label,*out,initial,reset))
        if di%180==0:print(source,di+1,round(time.perf_counter()-t0,1),flush=True)
cols=['source','day','capacity_mwh','supply_mw','variant','actual_state_mwh','last_hydrogen_power_mw','state_age_quarters','deficit_mwh','request_mwh','hydrogen_energy_mwh','startups','on_hours','max_balance_error','constraint_violations','initial_inventory_mwh','episode_restart']
d=pd.DataFrame(rows,columns=cols);d.to_csv(ROOT/'results'/'scarcity_challenges_daily.csv.gz',index=False);assert d.constraint_violations.sum()==0
g=d[d.day>='2026-01-01'].groupby(['source','capacity_mwh','supply_mw','variant']).agg(deficit_mwh=('deficit_mwh','sum'),request_mwh=('request_mwh','sum'),hydrogen_energy_mwh=('hydrogen_energy_mwh','sum')).reset_index();g['deficit_pct']=100*g.deficit_mwh/g.request_mwh;g.to_csv(ROOT/'results'/'scarcity_challenges_summary.csv',index=False)
print('COMPLETE',len(d),flush=True)
