from pathlib import Path
import json
import numpy as np,pandas as pd
from reachability import reach,reconstruct,audit_schedule
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent/'minute_revision_20260908'
rows=[]
for source,folder,config,step,dt in [('Germany_seconds','germany_seconds','germany_main_config.json',900,1/3600),('Germany_quarters','germany_seconds','germany_main_config.json',1,.25),('Belgium_quarters','belgium_quarters','belgium_validated_config.json',1,.25)]:
    z=json.loads((BASE/'results'/config).read_text())['scale_mw']
    for month in pd.period_range('2025-01','2026-07',freq='M'):
        files=sorted((BASE/'datasets'/folder).glob(str(month)+'-*.npz'))
        dates=[pd.Timestamp(f.stem) for f in files]
        # Incomplete months cannot be joined across missing days.
        complete=len(files)==month.days_in_month and all((b-a).days==1 for a,b in zip(dates,dates[1:]))
        if not complete:
            rows.append(dict(source=source,month=str(month),status='incomplete_calendar_month',observed_days=len(files)));continue
        chunks=[np.clip(np.load(f)['mw']/z,-1,1) for f in files]
        if source=='Germany_quarters':chunks=[x.reshape(-1,900).mean(axis=1) for x in chunks]
        a=np.concatenate(chunks)
        for E in [2.,4.,8.]:
            def solve(S):
                ans=reach(a,E,.75,.94,S,0.,E/2,E/2,step,dt)
                return bool(ans[0] and ans[2][-1]-1e-9<=E/2<=ans[3][-1]+1e-9),ans
            ok,ans=solve(.75);row=dict(source=source,month=str(month),capacity_mwh=E,status='feasible' if ok else 'infeasible',observed_days=len(files))
            if ok:
                lo=0.;hi=.75
                for _ in range(16):
                    m=(lo+hi)/2
                    if solve(m)[0]:hi=m
                    else:lo=m
                S=min(.75,hi+1e-6);ok,ans=solve(S);assert ok
                b,s=reconstruct(a,E,.75,.94,*ans[2:],E/2,step,dt)
                au=audit_schedule(a,b,E/2,E,.75,.94,S,0.,step,dt)
                error=max(au[-1],abs(s[0]-E/2),abs(au[0]-E/2));assert error<1e-6
                row.update(supply_lower_mw=lo,supply_upper_mw=hi,witness_error=error)
            rows.append(row)
        pd.DataFrame(rows).to_csv(ROOT/'results/monthly_oracle.csv',index=False)
        print(source,str(month),'done',flush=True)
pd.DataFrame(rows).to_csv(ROOT/'results/monthly_oracle.csv',index=False)
(ROOT/'results/monthly_oracle_audit.json').write_text(json.dumps(dict(status='PASS',rows=len(rows),scope='Independent calendar-month cyclic boundaries; incomplete calendar months excluded explicitly; not a prospective test or confidence interval'),indent=2))
