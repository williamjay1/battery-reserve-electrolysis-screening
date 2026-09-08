from pathlib import Path
import json,subprocess,sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
data=ROOT/'temp/native_evaluation.npy'
for E,S in [(1.,.2),(2.,.1),(2.,.2),(4.,.1),(4.,.2),(8.,.05),(8.,.1),(8.,.2)]:
    cert=ROOT/'results'/f'dual_certificate_{E}_{S}_0.94_17_20348.json'
    if not cert.exists():
        output=ROOT/'temp'/f'certified_{E}_{S}.json'
        subprocess.run([sys.executable,'-X','utf8',str(ROOT/'code/run_local.py'),str(ROOT/'code/solve_native_bound_worker.py'),str(data),str(E),str(S),str(output)],check=True)
    r=json.loads(cert.read_text());assert r['duality_gap']>=-1e-5
    print(E,S,r['hydrogen_upper_mwh'],r['duality_gap'],flush=True)
# Do not run until the original matrix writer is terminal, to avoid a write race.
d=pd.read_csv(ROOT/'results/hydrogen_matrix.csv');assert len(d)==45
for i,r in d[(d.source=='Germany_seconds')&d.cyclic_zero_deficit_feasible].iterrows():
    c=json.loads((ROOT/'results'/f'dual_certificate_{r.capacity_mwh}_{r.supply_mw}_0.94_17_20348.json').read_text())
    d.loc[i,'hydrogen_upper_mwh']=c['hydrogen_upper_mwh']
    d.loc[i,'bound_gap_pct']=100*(c['hydrogen_upper_mwh']-r.hydrogen_lower_mwh)/c['hydrogen_upper_mwh']
d.to_csv(ROOT/'results/hydrogen_matrix.csv',index=False)
