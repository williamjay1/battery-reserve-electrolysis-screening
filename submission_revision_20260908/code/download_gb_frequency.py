from pathlib import Path
import requests,json,hashlib
RAW=Path(r'E:\AcademicData\06\raw\submission_revision_20260908')
ROOT=Path(__file__).resolve().parents[1]
ids=['dbc3d95b-57f2-4e12-9281-44aad0667e6e','7f5364d6-5a06-4d34-bd60-6c4348cd892e','e7023794-d9f8-43ed-bfee-31c6f36a87f2','41b25b04-a824-402e-a3eb-2a0eeb348293','06315187-afcf-4fe2-8439-0eacc3f7bc35','dc7c5468-08a1-4586-bcdd-77ced39a5067','027227d0-7c70-4497-bdc4-a80cff7726f8']
manifest=ROOT/'results/gb_frequency_downloads.json'
rows=json.loads(manifest.read_text()) if manifest.exists() else []
for m,id in enumerate(ids,1):
    url=f'https://api.neso.energy/dataset/cb1cc925-ecd8-4406-b021-3a3f368196e1/resource/{id}/download/fnew-2026-{m}.csv'
    prior=next((r for r in rows if r['month']==f'2026-{m:02}'),None)
    if prior:
        assert hashlib.sha256(Path(prior['path']).read_bytes()).hexdigest()==prior['sha256']
        print('Verified existing '+prior['month'],flush=True);continue
    success=False
    for attempt in range(1,5):
        p=RAW/f'neso_frequency_2026-{m:02}_attempt{attempt}.csv'
        if p.exists():continue
        try:
            with requests.get(url,stream=True,timeout=(20,45),headers={'Accept-Encoding':'identity','Connection':'close'}) as response:
                response.raise_for_status(); expected=int(response.headers.get('Content-Length',0))
                with p.open('xb') as f:
                    for chunk in response.iter_content(256*1024):f.write(chunk)
                if expected:assert p.stat().st_size==expected
            success=True;break
        except (requests.RequestException,AssertionError) as error:
            print(f'Month {m} attempt {attempt} failed; original partial file retained: {type(error).__name__}',flush=True)
    if not success:raise RuntimeError(f'No complete download for month {m}')
    row=dict(month=f'2026-{m:02}',url=url,path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    rows.append(row);print(row['month'],row['bytes'],p.open().readline().strip(),flush=True)
    manifest.write_text(json.dumps(rows,indent=2))
