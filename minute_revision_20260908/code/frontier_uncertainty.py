from pathlib import Path
import pandas as pd,numpy as np
ROOT=Path(__file__).resolve().parents[1]
a=pd.read_csv(ROOT/'results'/'recovery_scarcity_daily.csv.gz');a['source']='Germany_seconds'
b=pd.read_csv(ROOT/'results'/'cross_source_daily.csv.gz')
d=pd.concat([a,b],ignore_index=True);d=d[(d.day>='2026-01-01')&(d.reserve_mw==.75)]
rng=np.random.default_rng(20260908);rows=[]
for source,x in d.groupby('source'):
    for label,left,right in [('supply_005_to_01',(2.,.05),(2.,.1)),('capacity_05_to_8_at_0025',(.5,.025),(8.,.025))]:
        l=x[(x.capacity_mwh==left[0])&(x.supply_mw==left[1])].set_index('day').sort_index()
        r=x[(x.capacity_mwh==right[0])&(x.supply_mw==right[1])].set_index('day').loc[l.index]
        delta=(l.native_deficit_mwh-r.native_deficit_mwh).to_numpy();den=l.requested_reserve_mwh.to_numpy();n=len(delta)
        for block in (3,7,14):
            start=rng.integers(0,n,(2000,int(np.ceil(n/block))))
            ix=((start[:,:,None]+np.arange(block))%n).reshape(2000,-1)[:,:n]
            stat=100*delta[ix].sum(axis=1)/den[ix].sum(axis=1)
            rows.append(dict(source=source,contrast=label,days=n,block_days=block,deficit_reduction_pp=100*delta.sum()/den.sum(),ci_low=np.quantile(stat,.025),ci_high=np.quantile(stat,.975)))
out=pd.DataFrame(rows);out.to_csv(ROOT/'results'/'frontier_uncertainty.csv',index=False)
print(out[out.block_days==7].to_string(index=False))
