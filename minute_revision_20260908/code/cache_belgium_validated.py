"""Validated quarter-hour demand; never relabel provisional minute shapes."""
from pathlib import Path
import json
import pandas as pd,numpy as np
ROOT=Path(__file__).resolve().parents[1];RAW=Path('E:/AcademicData/06/raw/minute_revision_20260908')
d=pd.read_csv(RAW/'ods127_2025_2026.csv',sep=';');d['t']=pd.to_datetime(d.datetime,utc=True)
d=d.sort_values('t');assert not d.t.duplicated().any()
d['mw']=d.afrrvolumeup-d.afrrvolumedown;d['day']=d.t.dt.strftime('%Y-%m-%d')
out=ROOT/'datasets'/'belgium_quarters';out.mkdir(exist_ok=True)
audit=[]
for day,g in d.groupby('day',sort=True):
    expected=pd.date_range(day,periods=96,freq='15min',tz='UTC')
    valid=len(g)==96 and pd.DatetimeIndex(g.t).equals(expected) and g.qualitystatus.eq('Validated').all() and np.isfinite(g.mw).all()
    audit.append(dict(day=day,rows=len(g),validated_rows=int(g.qualitystatus.eq('Validated').sum()),complete_validated=bool(valid)))
    if valid:np.savez_compressed(out/(day+'.npz'),mw=g.mw.to_numpy(dtype=float))
pd.DataFrame(audit).to_csv(ROOT/'docs'/'belgium_validated_day_audit.csv',index=False)
validdays=[x['day'] for x in audit if x['complete_validated']]
cal=np.concatenate([np.load(out/(x+'.npz'))['mw'] for x in validdays if x<'2025-07-01'])
report=dict(days=len(audit),complete_validated_days=len(validdays),calibration_quantile=.995,scale_mw=float(np.quantile(np.abs(cal),.995)),source='ODS127 satisfied demand, not domestic activation or asset dispatch',native_resolution_seconds=900,utc_days=True)
(ROOT/'results'/'belgium_validated_config.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
