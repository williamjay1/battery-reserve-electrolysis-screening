"""Audit official local-clock exports; cache complete native days on D only."""
import os
from pathlib import Path
import zipfile,json,sys
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
RAW=Path(os.environ.get('RESERVE_RAW_DIR', 'E:/AcademicData/06/raw/minute_revision_20260908'))
OUT=ROOT/'datasets'/'germany_seconds';OUT.mkdir(exist_ok=True)
audit_path=ROOT/'docs'/'germany_day_audit.csv'
audit=pd.read_csv(audit_path).to_dict('records') if audit_path.exists() else []
def day_cache(frame,source):
    label=frame.iloc[0,0]
    naive=pd.DatetimeIndex(pd.to_datetime(frame.iloc[:,0]+' '+frame.iloc[:,1],format='%d.%m.%Y %H:%M:%S'))
    day=naive[0].normalize()
    start=day.tz_localize('Europe/Berlin');end=(day+pd.Timedelta(days=1)).tz_localize('Europe/Berlin')
    expected=int((end-start).total_seconds())
    # Infer fall-back order from the complete day, never from a CSV chunk.
    try:
        utc=naive.tz_localize('Europe/Berlin',ambiguous='infer',nonexistent='raise').tz_convert('UTC')
        offsets=((utc-start.tz_convert('UTC')).total_seconds()).astype(np.int64)
        vals=pd.to_numeric(frame.iloc[:,2],errors='coerce').to_numpy(dtype=np.float64)
        duplicates=int(pd.Index(offsets).duplicated().sum())
        good=(offsets>=0)&(offsets<expected)&np.isfinite(vals)
        arr=np.full(expected,np.nan);arr[offsets[good]]=vals[good]
        missing=int(np.isnan(arr).sum())
        ordered=bool(np.all(np.diff(offsets)>0))
        complete=missing==0 and duplicates==0 and ordered
        item=dict(day=str(day.date()),source=source,rows=len(frame),expected_seconds=expected,missing_seconds=missing,duplicate_seconds=duplicates,ordered=ordered,complete=complete)
        if complete:
            np.savez_compressed(OUT/(str(day.date())+'.npz'),mw=arr,utc_start=np.int64(start.timestamp()))
    except Exception as exc:
        item=dict(day=str(day.date()),source=source,rows=len(frame),complete=False,error=str(exc))
    audit.append(item)
def process(path):
    with zipfile.ZipFile(path) as z:
        members=[n for n in z.namelist() if n.endswith('.csv')];assert len(members)==1,members
        carry=None
        for chunk in pd.read_csv(z.open(members[0]),sep=';',decimal=',',chunksize=500000):
            if carry is not None:chunk=pd.concat([carry,chunk],ignore_index=True)
            last=chunk.iloc[-1,0];carry=chunk.loc[chunk.iloc[:,0]==last].copy()
            for _,group in chunk.loc[chunk.iloc[:,0]!=last].groupby(chunk.columns[0],sort=False):day_cache(group,path.name)
        if carry is not None:day_cache(carry,path.name)
    print(path.name,len(audit),'days audited',flush=True)
paths=sorted(RAW.glob('SRL_Soll_*.csv.zip'))
for p in paths:
    # Exclude annual files to prevent duplicate observations.
    if p.name[9:15]!=p.name[18:24]:continue
    if len(sys.argv)>1 and sys.argv[1] not in p.name:continue
    prior=[r for r in audit if r['source']==p.name]
    if prior and all((not r['complete']) or (OUT/(r['day']+'.npz')).exists() for r in prior):
        print('Already audited',p.name,flush=True);continue
    process(p)
pd.DataFrame(audit).sort_values('day').to_csv(audit_path,index=False)
print(json.dumps(dict(days=len(audit),complete=sum(x['complete'] for x in audit)),indent=2),flush=True)
