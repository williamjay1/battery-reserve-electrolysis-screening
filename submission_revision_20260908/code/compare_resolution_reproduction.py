"""Compare separately regenerated extension results, excluding runtime only."""
from pathlib import Path
import json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
fresh=Path(sys.argv[1]);checks=0
def compare(a,b,path=''):
    global checks
    if isinstance(a,dict):
        assert set(a)==set(b),path
        for k in a:
            if k!='seconds':compare(a[k],b[k],path+'/'+k)
    elif isinstance(a,list):
        assert len(a)==len(b),path
        for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+f'/{i}')
    else:
        if isinstance(a,(float,int)) and not isinstance(a,bool):
            assert np.isclose(a,b,atol=1e-7,rtol=1e-9), (path,a,b)
        else:assert a==b,(path,a,b)
        checks+=1
for folder in ['resolution_challenge','monthly_energy_challenge']:
    compare(json.loads((ROOT/'results'/folder/'results.json').read_text()),json.loads((fresh/'results'/folder/'results.json').read_text()),folder)
    for p in (ROOT/'results'/folder).glob('*.npz'):
        q=fresh/'results'/folder/p.name
        with np.load(p) as a,np.load(q) as b:
            assert set(a.files)==set(b.files)
            for k in a.files:
                assert np.allclose(a[k],b[k],atol=1e-7,rtol=1e-9),(str(p),k)
                checks+=1
report=dict(status='PASS',checks=checks,scope='Two separately regenerated extension tables and all 22 saved schedules; runtime excluded. Previous 198-check production comparison remains separate.')
(ROOT/'results/resolution_reproduction_comparison.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
