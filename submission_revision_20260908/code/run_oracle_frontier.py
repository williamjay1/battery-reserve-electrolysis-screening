from pathlib import Path
import json,time
import numpy as np
import pandas as pd
from reachability import reach,reconstruct,audit_schedule
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent/'minute_revision_20260908'
(ROOT/'results/oracle_schedules').mkdir(exist_ok=True)
rows=[]
for source,folder,config,step,dt in [
 ('Germany_seconds','germany_seconds','germany_main_config.json',900,1/3600),
 ('Germany_quarters','germany_seconds','germany_main_config.json',1,.25),
 ('Belgium_quarters','belgium_quarters','belgium_validated_config.json',1,.25)]:
    scale=json.loads((BASE/'results'/config).read_text())['scale_mw']
    files=sorted(f for f in (BASE/'datasets'/folder).glob('*.npz') if f.stem>='2026-01-01')
    dates=[pd.Timestamp(f.stem) for f in files]
    assert all((b-a).days==1 for a,b in zip(dates,dates[1:])),source
    arrays=[np.clip(np.load(f)['mw']/scale,-1,1) for f in files]
    if source=='Germany_quarters':arrays=[x.reshape(-1,900).mean(axis=1) for x in arrays]
    a=np.concatenate(arrays);print(source,len(a),'samples',flush=True)
    for cap in [.5,1.,2.,4.,8.]:
        for cyclic in [False,True]:
            start=time.perf_counter();R=.75
            def solve(S):
                result=reach(a,cap,R,.94,S,0.,cap/2,cap/2,step,dt)
                ok=result[0] and (not cyclic or result[3][-1]>=cap/2-1e-9)
                return bool(ok),result
            ok,ans=solve(R)
            row=dict(source=source,capacity_mwh=cap,terminal_at_least_initial=cyclic,days=len(files),hours=len(a)*dt,feasible_in_range=ok)
            if ok:
                lo=0.;hi=R
                for _ in range(16):
                    mid=(lo+hi)/2
                    if solve(mid)[0]:hi=mid
                    else:lo=mid
                row.update(supply_lower_mw=lo,supply_upper_mw=hi,bracket_width_mw=hi-lo)
                # Stay on the certified feasible side of the boundary.
                S=min(R,hi+1e-6);ok,ans=solve(S);assert ok
                _,n,ls,us,bl,bh=ans
                target=max(cap/2,ls[-1]) if cyclic else (ls[-1]+us[-1])/2
                target=min(target,us[-1])
                bs,ss=reconstruct(a,cap,R,.94,ls,us,bl,bh,target,step,dt)
                audit=audit_schedule(a,bs,cap/2,cap,R,.94,S,0.,step,dt)
                error=max(audit[-1],abs(ss[0]-cap/2),abs(audit[0]-target))
                assert error<1e-6,(source,cap,cyclic,error)
                if cyclic:assert audit[0]>=cap/2-1e-6
                row.update(witness_supply_mw=S,witness_hydrogen_input_mwh=float(audit[3]),terminal_mwh=float(audit[0]),maximum_witness_error=float(error))
                np.savez_compressed(ROOT/'results/oracle_schedules'/f'{source}_{cap}_{int(cyclic)}.npz',baseline_mw=bs,quarter_inventory_mwh=ss,supply_mw=S)
            row['seconds']=time.perf_counter()-start;rows.append(row)
            pd.DataFrame(rows).to_csv(ROOT/'results/oracle_frontier.csv',index=False)
            print(row,flush=True)
(ROOT/'results/oracle_frontier_audit.json').write_text(json.dumps(dict(status='PASS',configurations=len(rows),exact_boundary_definition='zero clipping, fixed quarter baseline, initial half capacity; terminal constraint as labeled',bisections=16,maximum_bracket_width_mw=.75/2**16),indent=2))
