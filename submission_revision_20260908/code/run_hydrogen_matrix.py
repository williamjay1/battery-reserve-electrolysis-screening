from pathlib import Path
import json,time,subprocess,sys
import numpy as np,pandas as pd
from reachability import reach,reconstruct,audit_schedule
from native_hydrogen_bound import upper_bound
from hydrogen_lp_pilot import optimize
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent/'minute_revision_20260908'
output=ROOT/'results/hydrogen_matrix.csv'
rows=pd.read_csv(output).to_dict('records') if output.exists() else []
done={(r['source'],r['capacity_mwh'],r['supply_mw']) for r in rows}
for source,folder,config,step,dt in [('Germany_seconds','germany_seconds','germany_main_config.json',900,1/3600),('Germany_quarters','germany_seconds','germany_main_config.json',1,.25),('Belgium_quarters','belgium_quarters','belgium_validated_config.json',1,.25)]:
    scale=json.loads((BASE/'results'/config).read_text())['scale_mw']
    files=sorted(f for f in (BASE/'datasets'/folder).glob('*.npz') if f.stem>='2026-01-01')
    chunks=[np.clip(np.load(f)['mw']/scale,-1,1) for f in files]
    if source=='Germany_quarters':chunks=[a.reshape(-1,900).mean(axis=1) for a in chunks]
    a=np.concatenate(chunks)
    if source=='Germany_seconds':
        cache=ROOT/'temp/native_evaluation.npy'
        if not cache.exists():np.save(cache,a)
    for E in [.5,1.,2.,4.,8.]:
        for S in [.05,.1,.2]:
            if (source,E,S) in done:continue
            t=time.perf_counter();ans=reach(a,E,.75,.94,S,0.,E/2,E/2,step,dt)
            feasible=bool(ans[0] and ans[2][-1]-1e-9<=E/2<=ans[3][-1]+1e-9)
            row=dict(source=source,capacity_mwh=E,supply_mw=S,cyclic_zero_deficit_feasible=feasible,hours=len(a)*dt)
            if feasible:
                if source=='Germany_seconds':
                    pilot_file=ROOT/'results/native_hydrogen_bounds.json'
                    pilot=json.loads(pilot_file.read_text()) if pilot_file.exists() else []
                    cached=next((r for r in pilot if r['capacity_mwh']==E and r['supply_mw']==S),None)
                    if cached:
                        lower=cached['hydrogen_feasible_lower_mwh'];upper=cached['hydrogen_relaxed_upper_mwh'];error=cached['native_schedule_error']
                    else:
                        bs,ss=reconstruct(a,E,.75,.94,*ans[2:],E/2,step,dt)
                        au=audit_schedule(a,bs,E/2,E,.75,.94,S,0.,step,dt)
                        lower=au[3];error=max(au[-1],abs(ss[0]-E/2),abs(au[0]-E/2))
                        worker_result=ROOT/'temp'/f'native_bound_{E}_{S}.json'
                        subprocess.run([sys.executable,'-X','utf8',str(ROOT/'code/run_local.py'),str(ROOT/'code/solve_native_bound_worker.py'),str(cache),str(E),str(S),str(worker_result)],check=True)
                        upper=json.loads(worker_result.read_text())['upper_mwh']
                        np.savez_compressed(ROOT/'results'/f'hydrogen_{source}_{E}_{S}.npz',baseline_mw=bs,inventory_mwh=ss)
                else:
                    sol=optimize(a,E,.75,S);assert sol['success'],sol
                    lower=upper=sol['hydrogen_input_mwh'];error=sol['maximum_replay_violation']
                    np.savez_compressed(ROOT/'results'/f'hydrogen_{source}_{E}_{S}.npz',baseline_mw=sol['baseline'],inventory_mwh=sol['states'])
                assert error<1e-5 and lower<=upper+1e-6,row
                row.update(hydrogen_lower_mwh=lower,hydrogen_upper_mwh=upper,bound_gap_pct=100*(upper-lower)/max(upper,1e-12),witness_error=error,no_reserve_input_mwh=S*len(a)*dt)
            row['seconds']=time.perf_counter()-t;rows.append(row)
            pd.DataFrame(rows).to_csv(output,index=False);print(row,flush=True)
assert len(rows)==45
(ROOT/'results/hydrogen_matrix_audit.json').write_text(json.dumps(dict(status='PASS',configurations=45,native_bounds='exact feasible witness and optimistic convex endpoint upper bound',quarter_results='exact LP with physical increment bounds and replay',terminal='half capacity at both endpoints'),indent=2))
