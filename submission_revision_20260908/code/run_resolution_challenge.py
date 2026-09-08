"""Fixed dispatch interval, changed input averaging only. All scales retained."""
from pathlib import Path
import json,time,hashlib
import numpy as np
from reachability import reach,reconstruct,audit_schedule
from cyclic_energy_dual import bound
from hydrogen_lp_pilot import optimize

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/resolution_challenge';OUT.mkdir(exist_ok=True)
base=np.load(ROOT/'temp/native_evaluation.npy',mmap_mode='r')
E,S,R,eta=2.,.1,.75,.94
H0=len(base)/3600*S
signed=float(np.sum(base,dtype=np.float64)*R/3600)
rows=[]
for scale in [1,5,15,30,60,180,300,900]:
    started=time.perf_counter()
    a=np.asarray(base) if scale==1 else np.asarray(base).reshape(-1,scale).mean(axis=1)
    step=900//scale;dt=scale/3600
    energy=float(np.sum(a,dtype=np.float64)*R*dt)
    assert abs(energy-signed)<1e-8
    ans=reach(a,E,R,eta,S,0.,E/2,E/2,step,dt)
    feasible=bool(ans[0] and ans[2][-1]-1e-9<=E/2<=ans[3][-1]+1e-9)
    expanded=np.asarray(base) if scale==1 else np.repeat(a,scale)
    upper=bound(expanded,S,eta,R)
    row=dict(scale_seconds=scale,dispatch_seconds=900,capacity_mwh=E,supply_mw=S,
             reserve_mw=R,eta=eta,no_reserve_mwh=H0,signed_reserve_mwh=energy,
             signed_energy_error_mwh=abs(energy-signed),feasible=feasible,
             capacity_free_upper_mwh=upper['upper_mwh'],dual=upper)
    if feasible:
        bs,ss=reconstruct(a,E,R,eta,*ans[2:],E/2,step,dt)
        witness_kind='reachability witness'
        if scale==900:
            exact=optimize(a,E,R,S,eta)
            assert exact['success']
            bs=exact['baseline'];ss=exact['states']
            row['exact_optimum_mwh']=exact['hydrogen_input_mwh']
            witness_kind='exact interval-constant optimum'
        au=audit_schedule(a,bs,E/2,E,R,eta,S,0.,step,dt)
        error=float(max(au[-1],abs(au[0]-E/2),abs(ss[0]-E/2)))
        assert error<1e-6,error
        # Direct energy calculation does not use the recurrence evaluator.
        p=R*a.reshape(-1,step)-bs[:,None]
        charge=float(np.maximum(-p,0).sum()*dt)
        discharge=float(np.maximum(p,0).sum()*dt)
        h=float((S-bs).sum()*.25)
        identity=h-H0+energy+(1-eta**2)/(1+eta**2)*(charge+discharge)
        assert abs(identity)<1e-7
        assert h<=upper['upper_mwh']+1e-6
        native=audit_schedule(np.asarray(base),bs,E/2,E,R,eta,S,0.)
        row.update(lower_mwh=h,witness_kind=witness_kind,witness_error_mwh=error,
                   charge_mwh=charge,discharge_mwh=discharge,identity_residual_mwh=float(identity),
                   native_transfer_terminal_mwh=float(native[0]),
                   native_transfer_minimum_mwh=float(native[1]),
                   native_transfer_maximum_mwh=float(native[2]),
                   native_transfer_violation=float(native[-1]))
        hi=row.get('exact_optimum_mwh',upper['upper_mwh'])
        row['reported_upper_mwh']=hi
        row['sign']='loss' if hi<H0-1e-6 else ('gain attainable' if h>H0+1e-6 else 'unresolved')
        np.savez_compressed(OUT/f'schedule_{scale}s.npz',baseline_mw=bs,inventory_mwh=ss)
    else:row['sign']='infeasible'
    row['seconds']=time.perf_counter()-started
    rows.append(row)
    (OUT/'results.json').write_text(json.dumps(rows,indent=2))
    print(json.dumps(row),flush=True)
(OUT/'input_manifest.json').write_text(json.dumps(dict(
    input_cache_sha256=hashlib.sha256((ROOT/'temp/native_evaluation.npy').read_bytes()).hexdigest(),
    scales=8,samples=len(base),status='COMPLETE'),indent=2))
