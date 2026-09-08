from pathlib import Path
import json
R=Path('D:/MLWork/06/submission_revision_20260908')
a=json.loads((R/'results/distribution_envelope.json').read_text());b=json.loads((R/'results/gb_transfer.json').read_text())
assert len(a)==78 and len(b)==42
for rows in [a,b]:
 for r in rows:
  native=r.get('native_relaxed_mwh',r.get('native_upper_mwh'))
  assert r['lower_relaxed_mwh']<=native<=r['upper_relaxed_mwh']+1e-7
for m in sorted(set(r['month'] for r in b)):
 rr=[r for r in b if r['month']==m]
 assert min(r['k'] for r in rr if r['width_kw']<=.1)==45
 assert all(r['upper_relaxed_mwh']<r['no_reserve_mwh'] for r in rr)
print('Final 120 empirical interval and all-month narrative checks PASS')
