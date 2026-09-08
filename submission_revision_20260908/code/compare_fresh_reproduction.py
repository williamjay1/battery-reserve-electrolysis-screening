"""Compare regenerated numerical artifacts; never use this to certify scientific validity."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
reference=Path(sys.argv[1]).resolve(); fresh=Path(sys.argv[2]).resolve()
state=json.loads((fresh.parent/'execution_status.json').read_text())
assert state['status']=='analysis_finished_comparison_pending',state['status']
checks=[]
specs={
 'control_classification':['source','capacity_mwh','supply_mw','tau_hours'],
 'oracle_frontier':['source','capacity_mwh','terminal_at_least_initial'],
 'monthly_oracle':['source','month','capacity_mwh'],
 'hydrogen_matrix':['source','capacity_mwh','supply_mw']}
for name,keys in specs.items():
 a=pd.read_csv(reference/'results'/(name+'.csv')).sort_values(keys).reset_index(drop=True)
 b=pd.read_csv(fresh/'results'/(name+'.csv')).sort_values(keys).reset_index(drop=True)
 assert len(a)==len(b),(name,len(a),len(b))
 assert set(a.columns)==set(b.columns),(name,'schema')
 for col in a.columns:
  if col=='seconds':continue
  if pd.api.types.is_numeric_dtype(a[col]) and not pd.api.types.is_bool_dtype(a[col]):
   x=a[col].to_numpy(dtype=float);y=b[col].to_numpy(dtype=float)
   passed=bool(np.allclose(x,y,atol=1e-6,rtol=1e-8,equal_nan=True))
   delta=np.abs(x-y);finite=delta[np.isfinite(delta)]
   checks.append(dict(artifact=name,column=col,passed=passed,max_abs_difference=float(finite.max()) if finite.size else None))
  else:
   checks.append(dict(artifact=name,column=col,passed=a[col].fillna('<missing>').equals(b[col].fillna('<missing>'))))
for name in ['energy_challenge','cyclic_energy_dual_challenge']:
 a=json.loads((reference/'results'/(name+'.json')).read_text())
 b=json.loads((fresh/'results'/(name+'.json')).read_text())
 a=sorted(a,key=lambda x:(x['eta'],x['amplitude']));b=sorted(b,key=lambda x:(x['eta'],x['amplitude']))
 assert len(a)==len(b)
 for i,(x,y) in enumerate(zip(a,b)):
  for key in x:
   if key=='seconds':continue
   xv,yv=x[key],y[key]
   if isinstance(xv,(float,int)) and not isinstance(xv,bool):passed=bool(np.isclose(xv,yv,atol=1e-6,rtol=1e-8,equal_nan=True))
   else:passed=xv==yv
   checks.append(dict(artifact=name,case=i,column=key,passed=passed))
for name in ['native_evaluation.npy']:
 a=hashlib.sha256((reference/'temp'/name).read_bytes()).hexdigest()
 b=hashlib.sha256((fresh/'temp'/name).read_bytes()).hexdigest()
 checks.append(dict(artifact=name,passed=a==b,reference_sha256=a,fresh_sha256=b))
report=dict(status='PASS' if all(c['passed'] for c in checks) else 'DIFFERENCES_REQUIRE_REVIEW',scope='Fresh numerical reproduction from included caches; excludes raw-source re-download, scientific validity, source attribution, author approval, journal compliance and PDF layout.',checks=checks,reference=str(reference),fresh=str(fresh))
(reference/'results/fresh_reproduction_comparison.json').write_text(json.dumps(report,indent=2))
print(json.dumps(dict(status=report['status'],checks=len(checks),failures=[c for c in checks if not c['passed']]),indent=2))
raise SystemExit(0 if report['status']=='PASS' else 1)
