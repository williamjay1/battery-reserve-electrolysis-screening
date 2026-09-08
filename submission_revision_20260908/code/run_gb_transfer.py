from pathlib import Path
import json,hashlib
import numpy as np
from distribution_envelope import envelope
from distribution_screen import screen,summarize
ROOT=Path(__file__).resolve().parents[1];output=ROOT/'results/gb_transfer.json'
rows=json.loads(output.read_text()) if output.exists() else []
files=sorted((ROOT/'datasets/gb_frequency').glob('2026-*.npz'))
for p in files:
    sha=hashlib.sha256(p.read_bytes()).hexdigest()
    prior=[r for r in rows if r['month']==p.stem]
    if len(prior)==6 and all(r.get('cache_sha256')==sha for r in prior):
        print('Previously completed '+p.stem,flush=True);continue
    rows=[r for r in rows if r['month']!=p.stem]
    raw=.75*np.load(p)['activation'];u=np.sort(raw,axis=1);T=len(u)*.25
    native=screen(u)['upper_mwh']
    for k in [1,3,9,45,225,900]:
        e=envelope(u,k);temporal=np.sort(raw.reshape(len(u),k,900//k).mean(axis=2),axis=1)
        r=dict(month=p.stem,k=k,hours=T,no_reserve_mwh=T*.1,native_upper_mwh=native,cache_sha256=sha,
               temporal_upper_mwh=screen(temporal)['upper_mwh'],**e)
        r['width_kw']=e['gap_mwh']/T*1000
        assert e['lower_relaxed_mwh']<=native<=e['upper_relaxed_mwh']+1e-7
        assert e['upper_relaxed_mwh']<=r['temporal_upper_mwh']+1e-7
        rows.append(r)
    print(p.stem,[(r['k'],round(r['width_kw'],6)) for r in rows if r['month']==p.stem],flush=True)
    (ROOT/'results/gb_transfer.json').write_text(json.dumps(rows,indent=2))
