from pathlib import Path
import json,time
import numpy as np
from distribution_envelope import envelope
ROOT=Path(__file__).resolve().parents[1]
old=json.loads((ROOT/'results/distribution_screen/results.json').read_text())
months=json.loads((ROOT/'results/monthly_energy_challenge/results.json').read_text())
offset=0;ranges={}
for r in months:
    size=round(r['hours']*3600);ranges[r['month']]=(offset,offset+size);offset+=size
a=np.load(ROOT/'temp/native_evaluation.npy',mmap_mode='r');cases=list(dict.fromkeys(x['case'] for x in old));rows=[]
for case in cases:
    prior=[x for x in old if x['case']==case];eta=prior[0]['eta'];amp=prior[0]['amplitude']
    start,end=ranges.get(case,(0,len(a)));T=(end-start)/3600
    u=np.sort(.75*np.clip(a[start:end].reshape(-1,900)*amp,-1,1),axis=1)
    truth=prior[-1]['upper_mwh']-prior[-1]['margin_mwh']
    for k in [1,3,9,45,225,900]:
        t=time.perf_counter();r=envelope(u,k,eta=eta)
        r.update(case=case,k=k,hours=T,eta=eta,amplitude=amp,native_relaxed_mwh=truth,seconds=time.perf_counter()-t)
        assert r['lower_relaxed_mwh']<=truth+1e-7<=r['upper_relaxed_mwh']+1e-7
        assert abs(r['upper_relaxed_mwh']-next(x['upper_mwh'] for x in prior if x['k']==k))<2e-6
        r['width_kw']=1000*r['gap_mwh']/T
        rows.append(r)
    print(case,[(x['k'],round(x['width_kw'],6)) for x in rows if x['case']==case],flush=True)
    (ROOT/'results/distribution_envelope.json').write_text(json.dumps(rows,indent=2))
