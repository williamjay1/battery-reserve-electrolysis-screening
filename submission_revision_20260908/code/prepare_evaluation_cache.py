"""Build the normalized native evaluation cache from included daily caches."""
from pathlib import Path
import json
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent/'minute_revision_20260908'
(ROOT/'temp').mkdir(exist_ok=True)
files=sorted(f for f in (BASE/'datasets/germany_seconds').glob('*.npz') if f.stem>='2026-01-01')
assert len(files)==212,len(files)
scale=json.loads((BASE/'results/germany_main_config.json').read_text())['scale_mw']
a=np.concatenate([np.clip(np.load(f)['mw']/scale,-1,1) for f in files])
assert len(a)==18313200
np.save(ROOT/'temp/native_evaluation.npy',a)
print(f'Prepared {len(a)} native evaluation samples.',flush=True)
