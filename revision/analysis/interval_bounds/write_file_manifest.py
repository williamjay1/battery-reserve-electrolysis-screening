"""Checksum the portable module and its completed outputs, excluding caches."""
from pathlib import Path
import hashlib,json
from run_interval_bounds import OUT

def checksum(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

if __name__=='__main__':
    files=[]
    for folder,label in [(Path(__file__).resolve().parent,'analysis/interval_bounds'),(OUT,'results/interval_bounds')]:
        for p in sorted(folder.iterdir()):
            if p.is_file() and p.name!='file_manifest.json' and p.suffix in ('.py','.md','.json','.npz','.csv','.log'):
                files.append(dict(path=f'{label}/{p.name}',bytes=p.stat().st_size,sha256=checksum(p)))
    report=dict(description='Portable native-bound and decision-duration analysis; original German activation excluded',
        files=files,file_count=len(files))
    (OUT/'file_manifest.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(dict(files=len(files),manifest='results/interval_bounds/file_manifest.json')))
