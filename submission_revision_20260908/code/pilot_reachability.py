from pathlib import Path
import json,time
import numpy as np
from reachability import reach,reconstruct,audit_schedule
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent/'minute_revision_20260908'
rng=np.random.default_rng(20260908)
checked=0;maxerror=0.
for k in range(300):
    a=rng.uniform(-1,1,120)
    cap=float(rng.uniform(.03,1));R=.75;eta=.94;S=float(rng.uniform(.02,.4));hf=.05
    ans=reach(a,cap,R,eta,S,hf,cap/2,cap/2,10,.025)
    if not ans[0]:continue
    _,n,ls,us,bl,bh=ans
    terminal=(ls[-1]+us[-1])/2
    bs,ss=reconstruct(a,cap,R,eta,ls,us,bl,bh,terminal,10,.025)
    audit=audit_schedule(a,bs,ss[0],cap,R,eta,S,hf,10,.025)
    error=max(audit[-1],abs(ss[0]-cap/2),abs(audit[0]-terminal))
    assert error<1e-7,(k,error)
    maxerror=max(maxerror,error);checked+=1
print('random reconstructed',checked,'error',maxerror,flush=True)
scale=json.loads((BASE/'results/germany_main_config.json').read_text())['scale_mw']
files=sorted((BASE/'datasets/germany_seconds').glob('2026-01-*.npz'))
a=np.concatenate([np.clip(np.load(f)['mw']/scale,-1,1) for f in files])
rows=[]
for cap in [2.,8.]:
    for S in [.025,.05,.1,.2]:
        t=time.perf_counter();ans=reach(a,cap,.75,.94,S,0.,cap/2,cap/2)
        ok,n,ls,us,bl,bh=ans
        cycle=ok and ls[-1]-1e-8<=cap/2<=us[-1]+1e-8
        row=dict(capacity=cap,supply=S,feasible=bool(ok),cyclic_feasible=bool(cycle),quarters=int(n),runtime=time.perf_counter()-t)
        if ok:
            target=cap/2 if cycle else (ls[-1]+us[-1])/2
            bs,ss=reconstruct(a,cap,.75,.94,ls,us,bl,bh,target)
            audit=audit_schedule(a,bs,ss[0],cap,.75,.94,S,0.)
            row['max_violation']=float(max(audit[-1],abs(ss[0]-cap/2),abs(audit[0]-target)))
            assert row['max_violation']<1e-6,row
        rows.append(row);print(row,flush=True)
(ROOT/'results/reachability_pilot.json').write_text(json.dumps(dict(random_reconstructed=checked,max_random_error=maxerror,real_month=rows),indent=2))
