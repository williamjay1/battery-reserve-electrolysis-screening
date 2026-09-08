from pathlib import Path
import json,hashlib,calendar
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'datasets/gb_frequency';OUT.mkdir(parents=True,exist_ok=True)
sources=json.loads((ROOT/'results/gb_frequency_downloads.json').read_text());reports=[]
for source in sources:
    key=source['month'];p=Path(source['path'])
    assert hashlib.sha256(p.read_bytes()).hexdigest()==source['sha256']
    d=pd.read_csv(p);assert list(d.columns)==['dtm','f']
    stamps=pd.to_datetime(d.dtm,format='%Y-%m-%d %H:%M:%S',errors='coerce',utc=True)
    hz=pd.to_numeric(d.f,errors='coerce').to_numpy(dtype=float)
    valid=stamps.notna().to_numpy()&np.isfinite(hz)
    inmonth=(stamps.dt.strftime('%Y-%m')==key).to_numpy()
    ts=stamps.dt.tz_localize(None).to_numpy(dtype='datetime64[s]').astype('int64')[valid&inmonth];f=hz[valid&inmonth]
    assert np.min(ts)>=int(np.datetime64('2026-01-01','s').astype('int64'))
    unordered=int(np.sum(np.diff(ts)<0));idx=np.argsort(ts,kind='stable');ts=ts[idx];f=f[idx]
    q=ts//900;unique,first,count=np.unique(q,return_index=True,return_counts=True)
    good=(count==900)&(ts[first]==unique*900)&(ts[first+count-1]==unique*900+899)
    bad_q=np.unique(q[1:][(q[1:]==q[:-1])&(np.diff(ts)!=1)])
    good &= ~np.isin(unique,bad_q)
    keep=np.isin(q,unique[good]);a=np.clip((50-f[keep])/.2,-1,1).reshape(-1,900)
    assert len(a)>0,'No complete quarter; inspect QC before proceeding'
    np.savez_compressed(OUT/f'{key}.npz',activation=a,quarter_start_s=unique[good]*900)
    expected=calendar.monthrange(2026,int(key[-2:]))[1]*96
    report=dict(month=key,raw_rows=len(d),invalid_rows=int((~valid).sum()),outside_month_rows=int((valid&~inmonth).sum()),
                duplicate_seconds=int(np.sum(np.diff(ts)==0)),unordered_adjacent_rows=unordered,
                expected_quarters=expected,retained_quarters=len(a),excluded_quarters=expected-len(a),hours=len(a)*.25,
                minimum_hz=float(np.min(f)),maximum_hz=float(np.max(f)),clipped_fraction=float(np.mean(abs((50-f[keep])/.2)>1)),
                source_sha256=source['sha256'],cache_sha256=hashlib.sha256((OUT/f'{key}.npz').read_bytes()).hexdigest())
    reports.append(report);print(report,flush=True)
    (ROOT/'results/gb_frequency_qc.json').write_text(json.dumps(reports,indent=2))
