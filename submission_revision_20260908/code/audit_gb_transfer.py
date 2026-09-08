from pathlib import Path
import json,hashlib,datetime,shutil,subprocess,sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'results/gb_frequency_downloads.json').read_text());checks=[]
for r in manifest:
    d=pd.read_csv(r['path']);a=np.load(ROOT/'datasets/gb_frequency'/f"{r['month']}.npz")
    f=d.f.to_numpy();expected=np.minimum(1,np.maximum(-1,5*(50-f))).reshape(-1,900)
    assert np.max(abs(expected-a['activation']))<1e-13
    starts=a['quarter_start_s'];assert np.all(np.diff(starts)==900)
    for index in [0,len(d)-1,*range(0,len(d),900)]:
        observed=int(datetime.datetime.strptime(d.dtm.iloc[index],'%Y-%m-%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp())
        assert observed==int(starts[0])+index
    checks.append(dict(month=r['month'],seconds=len(d),quarter_start_checks=len(starts),max_activation_error=float(np.max(abs(expected-a['activation'])))))
    print(r['month'],'independent transform/timestamp PASS',flush=True)
fresh=ROOT.parent/'gb_transfer_independent_20260908';fresh.mkdir(exist_ok=False)
for name in ['code','results','datasets/gb_frequency']:(fresh/name).mkdir(parents=True,exist_ok=True)
for name in ['run_local.py','distribution_screen.py','distribution_envelope.py','run_gb_transfer.py']:shutil.copy2(ROOT/'code'/name,fresh/'code'/name)
for p in (ROOT/'datasets/gb_frequency').glob('*.npz'):shutil.copy2(p,fresh/'datasets/gb_frequency'/p.name)
subprocess.run([sys.executable,'-X','utf8','-u',str(fresh/'code/run_local.py'),str(fresh/'code/run_gb_transfer.py')],check=True)
a=json.loads((ROOT/'results/gb_transfer.json').read_text());b=json.loads((fresh/'results/gb_transfer.json').read_text());assert len(a)==len(b)==42
count=0
for x,y in zip(a,b):
    assert x.keys()==y.keys()
    for k in x:
        if isinstance(x[k],(int,float)):assert abs(x[k]-y[k])<1e-9
        else:assert x[k]==y[k]
        count+=1
report=dict(status='PASS',raw_transform_and_time_checks=checks,envelopes=42,independent_result_comparisons=count,fresh_directory=str(fresh))
(ROOT/'results/gb_transfer_audit.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
