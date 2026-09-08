"""All seven evaluation months, separate cyclic inventories; no cherry-picking."""
from pathlib import Path
import json,time,calendar
import numpy as np
from reachability import reach,reconstruct,audit_schedule
from cyclic_energy_dual import bound
from hydrogen_lp_pilot import optimize

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent/'minute_revision_20260908'
OUT=ROOT/'results/monthly_energy_challenge';OUT.mkdir(exist_ok=True)
scale=json.loads((BASE/'results/germany_main_config.json').read_text())['scale_mw']
E,S,R,eta=2.,.1,.75,.94
rows=[]
for month in range(1,8):
    started=time.perf_counter();key=f'2026-{month:02}'
    files=sorted((BASE/'datasets/germany_seconds').glob(key+'-*.npz'))
    assert [f.stem for f in files]==[f'{key}-{d:02}' for d in range(1,calendar.monthrange(2026,month)[1]+1)]
    a=np.concatenate([np.clip(np.load(f)['mw']/scale,-1,1) for f in files])
    H0=len(a)/3600*S
    ans=reach(a,E,R,eta,S,0.,E/2,E/2)
    feasible=bool(ans[0] and ans[2][-1]-1e-9<=E/2<=ans[3][-1]+1e-9)
    upper=bound(a,S,eta,R)
    coarse=optimize(a.reshape(-1,900).mean(axis=1),E,R,S,eta)
    row=dict(month=key,days=len(files),hours=len(a)/3600,no_reserve_mwh=H0,
             native_feasible=feasible,native_upper_mwh=upper['upper_mwh'],dual=upper,
             quarter_feasible=bool(coarse['success']))
    if feasible:
        bs,ss=reconstruct(a,E,R,eta,*ans[2:],E/2)
        audit=audit_schedule(a,bs,E/2,E,R,eta,S,0.)
        error=float(max(audit[-1],abs(audit[0]-E/2),abs(ss[0]-E/2)))
        assert error<1e-6
        lower=float((S-bs).sum()*.25)
        assert lower<=upper['upper_mwh']+1e-6
        row.update(native_lower_mwh=lower,native_witness_error_mwh=error)
        row['native_sign']='loss' if upper['upper_mwh']<H0-1e-6 else ('gain attainable' if lower>H0+1e-6 else 'unresolved')
        np.savez_compressed(OUT/f'native_{key}.npz',baseline_mw=bs,inventory_mwh=ss)
    else:row['native_sign']='infeasible'
    if coarse['success']:
        h=coarse['hydrogen_input_mwh'];row['quarter_optimum_mwh']=h
        row['quarter_sign']='gain' if h>H0+1e-6 else ('loss' if h<H0-1e-6 else 'zero')
        np.savez_compressed(OUT/f'quarter_{key}.npz',baseline_mw=coarse['baseline'],inventory_mwh=coarse['states'])
    else:row['quarter_sign']='infeasible'
    row['sign_reversal_established']=row['native_sign']=='loss' and row['quarter_sign']=='gain'
    row['seconds']=time.perf_counter()-started;rows.append(row)
    (OUT/'results.json').write_text(json.dumps(rows,indent=2));print(json.dumps(row),flush=True)
assert sum(r['hours'] for r in rows)==5087
