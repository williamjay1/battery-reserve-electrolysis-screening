from pathlib import Path
import json,time,platform
import numpy as np
from distribution_screen import summarize,screen

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/distribution_screen'; OUT.mkdir(exist_ok=True)
a=np.load(ROOT/'temp/native_evaluation.npy',mmap_mode='r')
ks=[1,3,9,45,225,900]; rows=[]
months=json.loads((ROOT/'results/monthly_energy_challenge/results.json').read_text())
cases=[('full',0,len(a),.94,1.)]
offset=0
for r in months:
    size=round(r['hours']*3600)
    cases.append((r['month'],offset,offset+size,.94,1.)); offset+=size
assert offset==len(a)
for eta,amp in [(.90,1.),(.98,1.),(1.,1.),(.94,.8),(.94,1.2)]:
    cases.append((f'eta{eta}_amp{amp}',0,len(a),eta,amp))
for name,start,end,eta,amp in cases:
    raw=.75*np.clip(np.asarray(a[start:end]).reshape(-1,900)*amp,-1,1)
    t=time.perf_counter(); u=np.sort(raw,axis=1)
    sorting=time.perf_counter()-t; H0=(end-start)/3600*.1
    case=[]
    for k in ks:
        t=time.perf_counter(); z=summarize(u,k); prep=time.perf_counter()-t
        times=[]
        for repeat in range(3):
            t=time.perf_counter(); out=screen(z,eta=eta);times.append(time.perf_counter()-t)
        row=dict(case=name,eta=eta,amplitude=amp,k=k,no_reserve_mwh=H0,
                 summary_bytes=z.nbytes,native_bytes=u.nbytes,sorting_seconds=sorting,
                 summary_seconds=prep,query_seconds=times,query_median_seconds=float(np.median(times)),
                 mean_error_mw=float(np.max(np.abs(z.mean(axis=1)-u.mean(axis=1)))),**out)
        row['loss_certified']=out['upper_mwh']<H0-1e-6
        t=time.perf_counter(); temporal=np.sort(raw.reshape(-1,k,900//k).mean(axis=2),axis=1)
        temporal_prep=time.perf_counter()-t
        t=time.perf_counter(); temporal_out=screen(temporal,eta=eta)
        row.update(temporal_upper_mwh=temporal_out['upper_mwh'],temporal_query_seconds=time.perf_counter()-t,
                   temporal_summary_seconds=temporal_prep)
        assert row['upper_mwh']<=row['temporal_upper_mwh']+1e-6
        case.append(row); rows.append(row)
    assert all(case[j]['upper_mwh']>=case[j+1]['upper_mwh']-1e-6 for j in range(len(ks)-1))
    print(name,[(r['k'],round(r['upper_mwh'],6),r['loss_certified']) for r in case],flush=True)
    (OUT/'results.json').write_text(json.dumps(rows,indent=2))
(OUT/'run_environment.json').write_text(json.dumps(dict(python=platform.python_version(),numpy=np.__version__,timing_repeats=3),indent=2))
