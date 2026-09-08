from pathlib import Path
import requests,re
RAW=Path('E:/AcademicData/06/raw/minute_revision_20260908');base='https://www.netztransparenz.de'
for path,name in [('/DesktopModules/LotesCharts/Javascript/lotes.Netztransparenz.Charts.DownloadHandler.js','netz_download.js'),('/DesktopModules/LotesNetztransparenz/Scripts/Lotes.Netztransparenz.js','netz_main.js')]:
    p=RAW/name
    if not p.exists():
        r=requests.get(base+path,timeout=40);r.raise_for_status()
        with p.open('xb') as f:f.write(r.content)
    s=p.read_text(encoding='utf-8')
    for term in ['url:', '.ashx','Download','Csv','downloadFile']:
        hits=list(re.finditer(re.escape(term),s));print(name,term,[s[max(0,h.start()-80):h.end()+250] for h in hits[:8]])
s=(RAW/'netz_seconds.html').read_text(encoding='utf-8')
for term in ['HandlerUrl','DownloadUrl','DownloadHandler','DataType":20','localProductId = 33']:
    hits=list(re.finditer(re.escape(term),s));print(term,[s[max(0,h.start()-200):h.end()+600] for h in hits[:2]])
