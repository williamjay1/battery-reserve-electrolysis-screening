import os
from pathlib import Path
import requests,json,re,base64,io,csv,concurrent.futures
from bs4 import BeautifulSoup
RAW=Path(os.environ.get('RESERVE_RAW_DIR', 'E:/AcademicData/06/raw/minute_revision_20260908'));ROOT=Path(__file__).resolve().parents[1]
url='https://www.netztransparenz.de/en/Balancing-Capacity/Balancing-Capacity-data/Data-in-second-resolution'
RAW.mkdir(parents=True,exist_ok=True)
page=RAW/'netz_seconds.html'
if not page.exists():
    response=requests.get(url,timeout=60);response.raise_for_status()
    with page.open('x',encoding='utf-8') as out:out.write(response.text)
s=page.read_text(encoding='utf-8');cfg=json.loads(re.search(r'const downloadHandlerConfig = (\{.*?\});',s).group(1))
req={'LocalFrom':'2025-01-01','LocalTo':'2026-07-31','ResultTimeZone':'UTC','Settings':cfg['Settings']}
p=RAW/'germany_file_inventory.csv'
if not p.exists():
    r=requests.get('https://www.netztransparenz.de'+cfg['CsvDownloadApiRoute'],params={'request':base64.b64encode(json.dumps(req).encode()).decode()},timeout=60);r.raise_for_status()
    with p.open('xb') as f:f.write(r.content)
rows=list(csv.reader(io.StringIO(p.read_text(encoding='utf-8-sig')),delimiter=';'));jobs=[]
for row in rows:
    if len(row)<5:continue
    name=row[0]
    if re.match(r'SRL_Soll_(2025\d\d)01_\1\d\d.csv.zip$',name) or re.match(r'SRL_Soll_(20260[1-7])01_\1\d\d.csv.zip$',name):jobs.append((name,row[4]))
print('jobs',jobs,flush=True)
def one(job):
    name,fileid=job;p=RAW/name
    if p.exists():return {'file':name,'status':'existing','bytes':p.stat().st_size}
    session=requests.Session();r=session.get(url,timeout=50);r.raise_for_status();soup=BeautifulSoup(r.text,'html.parser')
    data={x['name']:x.get('value','') for x in soup.select('input[type=hidden][name]')}
    data.update({'__EVENTTARGET':'dnn$ctr3321$View$btnHiddenNrvSecondlyValueFileDownload','__EVENTARGUMENT':'','dnn$ctr3321$View$hFNrvSecondlyValueDownloadFileId':fileid,'dnn$ctr3321$View$hFNrvSecondlyValueDownloadFileName':name})
    r=session.post(url,data=data,timeout=200);r.raise_for_status();assert r.content[:2]==b'PK',(name,r.headers.get('Content-Type'))
    with p.open('xb') as f:f.write(r.content)
    item={'file':name,'file_id':fileid,'status':'downloaded','bytes':len(r.content)};print(json.dumps(item),flush=True);return item
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:res=list(ex.map(one,jobs))
(ROOT/'docs'/'germany_download_manifest.json').write_text(json.dumps(res,indent=2),encoding='utf-8');print('DONE',len(res),flush=True)

