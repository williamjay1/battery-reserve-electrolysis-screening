from pathlib import Path
import pandas as pd,numpy as np,json
RAW=Path('E:/AcademicData/06/raw/minute_revision_20260908');ROOT=Path(__file__).resolve().parents[1]
ds=[]
for p in sorted(RAW.glob('ods128_20*.csv')):
    x=pd.read_csv(p,sep=';');x['source']=p.name;ds.append(x)
d=pd.concat(ds,ignore_index=True);d['t']=pd.to_datetime(d.datetime,utc=True);d['q']=pd.to_datetime(d.quarterhour,utc=True);d=d.sort_values('t')
d['k']=((d.t-d.q).dt.total_seconds()/60+1).astype(int)
assert d.k.between(1,15).all();assert not d.t.duplicated().any()
reports=[]
for col in ['afrrvolumeup','afrrvolumedown']:
    cum=d[col]*d.k;dif=cum-cum.groupby(d.q).shift(1).fillna(0)
    # A published 0.001 MW cumulative average implies <=(2k-1)*.0005 MW increment error.
    tol=(2*d.k-1)*.0005+1e-9
    d[col+'_minute']=dif;d[col+'_bad']=dif.lt(-tol)|dif.isna()
    reports.append({'variable':col,'negative':int(dif.lt(0).sum()),'beyond_rounding':int(dif.lt(-tol).sum()),'minimum':float(dif.min()),'maximum':float(dif.max())})
g=d.groupby('q').agg(n=('k','size'),n_unique=('k','nunique'),bad_up=('afrrvolumeup_bad','any'),bad_down=('afrrvolumedown_bad','any'),quality_issue=('qualitystatus',lambda x:x.eq('DataIssue').any()),last_up=('afrrvolumeup','last'),last_down=('afrrvolumedown','last'))
qpath=RAW/'ods127_2025_2026.csv'
if qpath.exists():
    q=pd.read_csv(qpath,sep=';');q['q']=pd.to_datetime(q.datetime,utc=True)
    g=g.merge(q[['q','afrrvolumeup','afrrvolumedown','qualitystatus']],on='q',how='left',validate='one_to_one')
    for direction in ['up','down']:g['error_'+direction]=g['last_'+direction]-g['afrrvolume'+direction]
    print('quarter errors',g[['error_up','error_down']].abs().quantile([0,.5,.9,.95,.99,1]).to_dict(),flush=True)
    print('quarter quality',g.qualitystatus.value_counts().to_dict(),flush=True)
    g.to_csv(ROOT/'datasets'/'elia_quarter_audit.csv',index=False)
report={'files':len(ds),'rows':len(d),'quality':d.qualitystatus.value_counts().to_dict(),'quarters':len(g),'complete':int((g.n.eq(15)&g.n_unique.eq(15)).sum()),'negative_audit':reports,'bad_up_quarters':int(g.bad_up.sum()),'data_issue_quarters':int(g.quality_issue.sum())}
(ROOT/'docs'/'ELIA_MINUTE_AUDIT.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report),flush=True)
d.to_csv(ROOT/'datasets'/'elia_minutes_unfiltered.csv.gz',index=False)
