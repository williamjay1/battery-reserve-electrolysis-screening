"""January-only mechanism pilot; not the held-out performance experiment."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
paths=sorted((ROOT/'datasets'/'germany_seconds').glob('2025-01-*.npz'))
raw=np.concatenate([np.load(p)['mw'] for p in paths]);scale=float(np.quantile(np.abs(raw),.995))
eta=.94;rows=[]
for file in paths:
    a=np.clip(np.load(file)['mw']/scale,-1,1).reshape(-1,900)
    for baseline in (-.25,0.,.25):
        p=.75*a-baseline
        native=np.where(p>=0,-p/eta,-p*eta)/3600
        path=np.cumsum(native,axis=1)
        lo=np.minimum(0,path.min(axis=1));hi=np.maximum(0,path.max(axis=1))
        delta=path[:,-1]
        # Minimum capacity for SOME starting state; no free resets claimed.
        span=hi-lo
        throughput=np.abs(p).sum(axis=1)/3600
        for seconds in (1,60,300,900):
            coarse=p.reshape(len(p),-1,seconds).mean(axis=2)
            dc=np.where(coarse>=0,-coarse/eta,-coarse*eta)*seconds/3600
            pc=np.cumsum(dc,axis=1)
            sc=np.maximum(0,pc.max(axis=1))-np.minimum(0,pc.min(axis=1))
            coarse_throughput=np.abs(coarse).sum(axis=1)*seconds/3600
            rows.append(dict(day=file.stem,baseline=baseline,seconds=seconds,blocks=len(p),delta_optimism_mwh=float((pc[:,-1]-delta).sum()),span_underestimate_mean_mwh=float((span-sc).mean()),span_underestimate_max_mwh=float((span-sc).max()),native_throughput_mwh=float(throughput.sum()),omitted_throughput_mwh=float((throughput-coarse_throughput).sum())))
df=pd.DataFrame(rows);df.to_csv(ROOT/'results'/'january_mechanism_pilot.csv',index=False)
summary=df.groupby(['baseline','seconds']).agg(delta_optimism_mwh=('delta_optimism_mwh','sum'),mean_span_error_mwh=('span_underestimate_mean_mwh','mean'),max_span_error_mwh=('span_underestimate_max_mwh','max'),omitted_throughput_mwh=('omitted_throughput_mwh','sum'),native_throughput_mwh=('native_throughput_mwh','sum')).reset_index()
summary['omitted_throughput_pct']=100*summary.omitted_throughput_mwh/summary.native_throughput_mwh
summary.to_csv(ROOT/'results'/'january_mechanism_summary.csv',index=False)
(ROOT/'results'/'pilot_config.json').write_text(json.dumps(dict(status='pilot only',days=len(paths),scale_mw=scale,scale_quantile=.995,reserve_mw=.75,eta=eta,baseline_mw=[-.25,0,.25]),indent=2))
print(summary.to_string(index=False),flush=True)
