"""Independent AC-throughput check of the cyclic electrolysis sign criterion."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent/'minute_revision_20260908'
d=pd.read_csv(ROOT/'results/hydrogen_matrix.csv')
assert len(d)==45 and int(d.cyclic_zero_deficit_feasible.sum())==19
eta=.94;kappa=(1-eta**2)/(1+eta**2);rows=[]
for source,folder,config,step,dt in [('Germany_seconds','germany_seconds','germany_main_config.json',900,1/3600),('Germany_quarters','germany_seconds','germany_main_config.json',1,.25),('Belgium_quarters','belgium_quarters','belgium_validated_config.json',1,.25)]:
 scale=json.loads((BASE/'results'/config).read_text())['scale_mw']
 chunks=[]
 for f in sorted((BASE/'datasets'/folder).glob('*.npz')):
  if f.stem<'2026-01-01':continue
  a=np.clip(np.load(f)['mw']/scale,-1,1)
  if source=='Germany_quarters':a=a.reshape(-1,900).mean(axis=1)
  chunks.append(a)
 for row in d[(d.source==source)&d.cyclic_zero_deficit_feasible].itertuples():
  path=ROOT/'results'/f'hydrogen_{source}_{row.capacity_mwh}_{row.supply_mw}.npz'
  if not path.exists() and source=='Germany_seconds':path=ROOT/'results'/f'native_hydrogen_witness_{row.capacity_mwh}_{row.supply_mw}.npz'
  z=np.load(path);bs=z['baseline_mw'];charge=discharge=signal=0.;q=0
  for a in chunks:
   n=len(a)//step;b=np.repeat(bs[q:q+n],step);q+=n
   p=.75*a-b
   charge+=np.maximum(-p,0).sum()*dt
   discharge+=np.maximum(p,0).sum()*dt
   signal+=(.75*a).sum()*dt
  assert q==len(bs)
  h=row.supply_mw*row.hours-bs.sum()*.25
  throughput=charge+discharge;balance=eta*charge-discharge/eta
  predicted_gain=-signal-kappa*throughput
  residual=h-row.no_reserve_input_mwh-predicted_gain
  assert abs(balance)<1e-6 and abs(residual)<1e-6
  assert abs(h-row.hydrogen_lower_mwh)<1e-6
  rows.append(dict(source=source,capacity_mwh=row.capacity_mwh,supply_mw=row.supply_mw,net_reserve_energy_mwh=signal,charge_mwh=charge,discharge_mwh=discharge,throughput_mwh=throughput,inventory_drift_mwh=balance,identity_residual_mwh=residual,gain_mwh=h-row.no_reserve_input_mwh,gain_threshold_mwh=-signal/kappa,minimum_throughput_lower_bound_mwh=(-signal-(row.hydrogen_upper_mwh-row.no_reserve_input_mwh))/kappa))
report=dict(status='PASS',eta=eta,kappa=kappa,cases=len(rows),rows=rows,scope='Energy identity checked from saved physical schedules across all feasible matrix cases; does not establish a new loss law or exact native optimum.')
(ROOT/'results/energy_identity_audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
