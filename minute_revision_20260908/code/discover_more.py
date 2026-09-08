from pathlib import Path
import requests,json,re
from bs4 import BeautifulSoup
RAW=Path('E:/AcademicData/06/raw/minute_revision_20260908')
jobs=[('elia_catalog.json','https://opendata.elia.be/api/explore/v2.1/catalog/datasets?limit=100&offset=0'),('netz_seconds.html','https://www.netztransparenz.de/en/Balancing-Capacity/Balancing-Capacity-data/Data-in-second-resolution'),('finland_zenodo.json','https://zenodo.org/api/records/17494556')]
for name,url in jobs:
    p=RAW/name
    if not p.exists():
        r=requests.get(url,timeout=45);print(name,r.status_code,flush=True)
        if r.status_code!=200:continue
        with p.open('xb') as f:f.write(r.content)
    s=p.read_text(encoding='utf-8')
    if name=='elia_catalog.json':
        x=json.loads(s);print('catalog',x.get('total_count'))
        for d in x.get('results',[]):
            title=d.get('metas',{}).get('default',{}).get('title','')
            if any(w in title.lower() for w in ['minute','activated','volume component']): print(d['dataset_id'],title)
    elif name=='netz_seconds.html':
        soup=BeautifulSoup(s,'html.parser');print('scripts',[a.get('src') for a in soup.find_all('script',src=True)])
        for term in ['afrr','AFRR','SRL','DataSource','api/','Download']:
            hits=list(re.finditer(term,s));print(term,[s[max(0,h.start()-90):h.end()+150] for h in hits[-8:]])
    else:
        x=json.loads(s);print(x.get('metadata',{}).get('title'));print(x.get('files',[]))
