from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
d=pd.read_csv(ROOT/'datasets'/'elia_quarter_audit.csv');d['day']=pd.to_datetime(d.q,utc=True).dt.strftime('%Y-%m-%d')
base=d.n.eq(15)&d.n_unique.eq(15)&~d.bad_up&~d.bad_down&d.qualitystatus.eq('Validated')
rows=[]
for tolerance in (1.,2.,5.,10.):
    valid=base&d.error_up.abs().le(tolerance)&d.error_down.abs().le(tolerance)
    for flags in ('retain_reported_flags','exclude_DataIssue'):
        v=valid if flags=='retain_reported_flags' else valid&~d.quality_issue
        days=pd.DataFrame({'day':d.day,'valid':v}).groupby('day').valid.agg(['sum','count'])
        rows.append(dict(endpoint_tolerance_mw=tolerance,quality_policy=flags,quarters=int(v.sum()),fraction=float(v.mean()),complete_96quarter_days=int(((days['sum']==96)&(days['count']==96)).sum()),days_at_least_90pct=int((days['sum']/96>=.9).sum())))
pd.DataFrame(rows).to_csv(ROOT/'results'/'belgium_eligibility_sensitivity.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))
