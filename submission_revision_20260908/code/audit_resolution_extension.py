"""Independent direct sums and compact/expanded replay for new scale cases."""
from pathlib import Path
import json
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
base=np.load(ROOT/'temp/native_evaluation.npy',mmap_mode='r')
rows=json.loads((ROOT/'results/resolution_challenge/results.json').read_text())
assert [r['scale_seconds'] for r in rows]==[1,5,15,30,60,180,300,900]
checks=[]
for r in rows:
    k=r['scale_seconds'];a=base.reshape(-1,k).mean(axis=1)
    schedule=np.load(ROOT/f'results/resolution_challenge/schedule_{k}s.npz')
    b=schedule['baseline_mw'];m=900//k
    p=.75*a.reshape(-1,m)-b[:,None]
    inc=np.where(p>=0,-p/.94,-p*.94)*k/3600
    states=1+np.cumsum(inc.ravel())
    err=max(abs(states[-1]-1),max(0,-states.min()),max(0,states.max()-2))
    assert err<1e-6
    assert np.max(np.abs(states[m-1::m]-schedule['inventory_mwh'][1:]))<1e-6
    h=float((.1-b).sum()*.25)
    assert abs(h-r['lower_mwh'])<1e-8
    assert h<=r['reported_upper_mwh']+1e-6
    if k in [5,60,300]:
        pe=np.repeat(p,k,axis=1)
        ince=np.where(pe>=0,-pe/.94,-pe*.94)/3600
        assert np.max(np.abs(ince.sum(axis=1)-inc.sum(axis=1)))<1e-12
    checks.append(dict(scale_seconds=k,direct_state_error=float(err)))
assert all(r['sign']=='loss' for r in rows[:-1])
assert rows[-1]['sign']=='gain attainable'
months=json.loads((ROOT/'results/monthly_energy_challenge/results.json').read_text())
assert len(months)==7 and sum(r['hours'] for r in months)==5087
assert [r['month'] for r in months if r['sign_reversal_established']]==['2026-06']
assert all(r['native_feasible'] and r['quarter_feasible'] for r in months)
(ROOT/'results/resolution_extension_audit.json').write_text(json.dumps(dict(status='PASS_FOR_SPECIFIED_CHECKS',scales=checks,months=7,scope='Direct schedule reconstruction, compact/expanded increments, result signs and all-month coverage; not external validity.'),indent=2))
print('Verified eight resolution schedules and seven-month coverage.',flush=True)
