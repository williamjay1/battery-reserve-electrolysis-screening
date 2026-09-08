from pathlib import Path
import requests,json,re,base64
RAW=Path('E:/AcademicData/06/raw/minute_revision_20260908');ROOT=Path(__file__).resolve().parents[1]
s=(RAW/'netz_seconds.html').read_text(encoding='utf-8')
cfg=json.loads(re.search(r'const downloadHandlerConfig = (\{.*?\});',s).group(1))
req={'LocalFrom':'2025-01-01','LocalTo':'2025-01-02','ResultTimeZone':'UTC','Settings':cfg['Settings']}
url='https://www.netztransparenz.de'+cfg['CsvDownloadApiRoute']
r=requests.get(url,params={'request':base64.b64encode(json.dumps(req).encode()).decode()},timeout=55)
print(r.status_code,r.headers.get('Content-Type'),r.headers.get('Content-Disposition'),len(r.content));print(r.text[:2500])
if r.status_code==200 and len(r.content)>100:
    p=RAW/'netz_probe_2025-01-01.csv'
    if not p.exists():
        with p.open('xb') as f:f.write(r.content)
# Fetch the publicly served chart client to discover the file-list request.
p=RAW/'netz_chart.js'
if not p.exists():
    r=requests.get('https://www.netztransparenz.de/DesktopModules/LotesCharts/Javascript/lotes.highCharts.js',timeout=40);r.raise_for_status()
    with p.open('xb') as f:f.write(r.content)
s=p.read_text(encoding='utf-8')
for term in ['GetNrv','getNrv','Secondly','DownloadFile','Service.asmx']:
    hits=list(re.finditer(re.escape(term),s));print(term,[s[max(0,h.start()-100):h.end()+200] for h in hits[:5]])
