from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent
rows=json.loads((root/'MANIFEST.json').read_text())
for row in rows:
 p=root/row['path']
 assert p.is_file(), row['path']
 assert p.stat().st_size==row['bytes'], row['path']
 assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],row['path']
print(f'PASS: {len(rows)} files match the release manifest')
