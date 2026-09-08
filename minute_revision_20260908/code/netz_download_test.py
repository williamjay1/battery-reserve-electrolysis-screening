from pathlib import Path
import requests,re,json
from bs4 import BeautifulSoup
RAW=Path('E:/AcademicData/06/raw/minute_revision_20260908');ROOT=Path(__file__).resolve().parents[1]
url='https://www.netztransparenz.de/en/Balancing-Capacity/Balancing-Capacity-data/Data-in-second-resolution'
session=requests.Session();r=session.get(url,timeout=40);r.raise_for_status();soup=BeautifulSoup(r.text,'html.parser')
data={x['name']:x.get('value','') for x in soup.select('input[type=hidden][name]')}
data['__EVENTTARGET']='dnn$ctr3321$View$btnHiddenNrvSecondlyValueFileDownload';data['__EVENTARGUMENT']=''
data['dnn$ctr3321$View$hFNrvSecondlyValueDownloadFileId']='71850a63-c065-4848-ad8f-45d2d3a56863'
data['dnn$ctr3321$View$hFNrvSecondlyValueDownloadFileName']='SRL_Soll_20250101_20250131.csv.zip'
r=session.post(url,data=data,timeout=100);print(r.status_code,r.headers.get('Content-Type'),len(r.content),r.content[:100],flush=True)
if r.status_code==200 and r.content[:2]==b'PK':
    p=RAW/'SRL_Soll_20250101_20250131.csv.zip'
    if not p.exists():
        with p.open('xb') as f:f.write(r.content)
else:(ROOT/'temp'/'netz_post_response.html').write_bytes(r.content)
