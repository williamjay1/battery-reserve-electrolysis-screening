from pathlib import Path
import requests,json,calendar,time,concurrent.futures
RAW=Path('E:/AcademicData/06/raw/minute_revision_20260908');ROOT=Path(__file__).resolve().parents[1]
BASE='https://opendata.elia.be/api/explore/v2.1/catalog/datasets/'
jobs=[]
for y in [2025,2026]:
    for m in range(1,13 if y==2025 else 8):
        start=f'{y}-{m:02}-01T00:00:00Z';ny,nm=(y+1,1) if m==12 else (y,m+1);end=f'{ny}-{nm:02}-01T00:00:00Z'
        jobs.append(('ods128',f'{y}-{m:02}',start,end,'datetime,quarterhour,qualitystatus,afrrvolumeup,afrrvolumedown'))
jobs.append(('ods127','2025_2026','2025-01-01T00:00:00Z','2026-08-01T00:00:00Z','datetime,qualitystatus,afrrvolumeup,afrrvolumedown'))
def one(job):
    ds,tag,start,end,cols=job;p=RAW/f'{ds}_{tag}.csv'
    if p.exists():return dict(file=p.name,bytes=p.stat().st_size,status='existing')
    params={'where':f"datetime >= '{start}' AND datetime < '{end}'",'select':cols,'order_by':'datetime','delimiter':';','use_labels':'false'}
    for attempt in range(3):
        try:
            r=requests.get(BASE+ds+'/exports/csv',params=params,timeout=100);r.raise_for_status();content=r.content
            assert b'datetime' in content[:300] and len(content)>1000,content[:400]
            with p.open('xb') as f:f.write(content)
            record=dict(file=p.name,bytes=len(content),url=r.url,status='downloaded');print(json.dumps(record),flush=True);return record
        except Exception as e:
            if attempt==2:return dict(file=p.name,status='failed',error=str(e))
            time.sleep(2)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:res=list(ex.map(one,jobs))
(ROOT/'docs'/'elia_download_manifest.json').write_text(json.dumps(res,indent=2),encoding='utf-8')
print('DONE',len(res),'failures',sum(x['status']=='failed' for x in res),flush=True)
