from pathlib import Path
import numpy as np,pandas as pd,json
from integrated_replay import replay_day
ROOT=Path(__file__).resolve().parents[1]
files=sorted((ROOT/'datasets'/'germany_seconds').glob('2025-01-*.npz'))[:7]
scale=json.loads((ROOT/'results'/'pilot_config.json').read_text())['scale_mw']
rows=[]
for cap in (.25,1.,2.):
    for label,seconds,mode in [('native',1,0),('minute',60,0),('5minute',300,0),('quarter',900,0),('gross',900,1),('envelope',900,2)]:
        pred=actual=cap*.5
        for f in files:
            a=np.clip(np.load(f)['mw']/scale,-1,1)
            out=replay_day(a,cap,.75,.94,.5,1.,seconds,mode,pred,actual)
            pred,actual=out[:2]
            rows.append(dict(day=f.stem,capacity=cap,model=label,pred=pred,actual=actual,native_loss_mwh=out[2],predicted_loss_mwh=out[3],baseline_charge_mwh=out[4],hydrogen_mwh=out[5],reserve_request_mwh=out[6],maximum_state_error_mwh=out[7],fallback_quarters=out[8]))
df=pd.DataFrame(rows);df.to_csv(ROOT/'results'/'integrated_pilot.csv',index=False)
for cap in (.25,1.,2.):
    n=df[(df.capacity==cap)&(df.model=='native')].reset_index(drop=True)
    e=df[(df.capacity==cap)&(df.model=='envelope')].reset_index(drop=True)
    for col in ['actual','native_loss_mwh','baseline_charge_mwh','hydrogen_mwh']:
        assert np.allclose(n[col],e[col],atol=1e-10,rtol=1e-10),(cap,col)
print(df.groupby(['capacity','model'])[['native_loss_mwh','hydrogen_mwh','maximum_state_error_mwh']].sum().to_string())
print('Native and envelope closed-loop equality: PASS')
