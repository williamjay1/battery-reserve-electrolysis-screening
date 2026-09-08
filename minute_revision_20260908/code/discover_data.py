from pathlib import Path
import requests,json,concurrent.futures
RAW=Path('E:/AcademicData/06/raw/minute_revision_20260908');RAW.mkdir(parents=True,exist_ok=True)
BASE='https://opendata.elia.be/api/explore/v2.1/catalog/datasets/'
def one(ds):
    p=RAW/(ds+'_metadata.json')
    if not p.exists():
        r=requests.get(BASE+ds,timeout=45);r.raise_for_status()
        with p.open('xb') as f:f.write(r.content)
    x=json.loads(p.read_text(encoding='utf-8'))
    fields=[{'name':f.get('name'),'label':f.get('label'),'description':f.get('description')} for f in x.get('fields',[])]
    print(json.dumps({'id':ds,'title':x.get('metas',{}).get('default',{}).get('title'),'fields':fields},ensure_ascii=False),flush=True)
    p=RAW/(ds+'_sample.json')
    if not p.exists():
        r=requests.get(BASE+ds+'/records',params={'limit':3,'order_by':'datetime ASC'},timeout=45);r.raise_for_status()
        with p.open('xb') as f:f.write(r.content)
    print(ds,p.read_text(encoding='utf-8')[:2200],flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
    for r in ex.map(one,['ods128','ods132','ods133']):pass
