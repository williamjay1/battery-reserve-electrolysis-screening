"""Matched efficiency and amplitude challenge of the sign-reversal finding."""
from pathlib import Path
import json,time
import numpy as np
from reachability import reach,reconstruct,audit_schedule
from hydrogen_lp_pilot import optimize

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'results/energy_challenge.json'
rows=json.loads(out.read_text()) if out.exists() else []
done={(r['eta'],r['amplitude']) for r in rows}
base=np.load(ROOT/'temp/native_evaluation.npy',mmap_mode='r')
duals=json.loads((ROOT/'results/cyclic_energy_dual_challenge.json').read_text())
for d in duals:
    eta,amp=d['eta'],d['amplitude']
    if (eta,amp) in done:continue
    t=time.perf_counter();a=np.clip(base*amp,-1,1)
    E,S,R=2.,.1,.75
    ans=reach(a,E,R,eta,S,0.,E/2,E/2)
    feasible=bool(ans[0] and ans[2][-1]-1e-9<=E/2<=ans[3][-1]+1e-9)
    row=dict(d,native_cyclic_feasible=feasible,capacity_mwh=E)
    if feasible:
        bs,ss=reconstruct(a,E,R,eta,*ans[2:],E/2)
        au=audit_schedule(a,bs,E/2,E,R,eta,S,0.)
        error=float(max(au[-1],abs(ss[0]-E/2),abs(au[0]-E/2)))
        assert error<1e-6
        assert au[3]<=d['upper_mwh']+1e-6
        row.update(native_feasible_input_mwh=float(au[3]),native_witness_error=error)
    coarse=optimize(a.reshape(-1,900).mean(axis=1),E,R,S,eta)
    row['quarter_feasible']=coarse['success']
    if coarse['success']:row['quarter_optimum_mwh']=coarse['hydrogen_input_mwh']
    row['seconds']=time.perf_counter()-t
    rows.append(row);out.write_text(json.dumps(rows,indent=2));print(row,flush=True)
