"""Use evaluated capacity-free dual baselines only as a finite-inventory guide."""
import argparse,json
import numpy as np
from numba import njit
from run_interval_bounds import INPUT,OUT,R,ETA,BL,BH,E,features,witness

@njit(cache=True)
def endpoints(a,b,step):
    f=np.empty(len(b))
    for q in range(len(b)):
        f[q]=features(a,q*step,(q+1)*step,b[q],R,ETA,1/3600)[0]
    return f

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--step',type=int,default=300);step=p.parse_args().step
    a=np.load(INPUT,mmap_mode='r');q=json.loads((OUT/f'interval_{step}s_quick.json').read_text())
    lam=q['multiplier'];fraction=(1/ETA-1/lam)/(1/ETA-ETA)
    rank=max(0,min(step-1,int(np.ceil(fraction*step))-1))
    u=np.sort(R*np.asarray(a).reshape(-1,step),axis=1)
    base=np.clip(u[:,rank],BL,BH);del u
    low=-1.;high=1.
    for _ in range(45):
        shift=(low+high)/2;b=np.clip(base+shift,BL,BH)
        f=endpoints(a,b,step)
        if np.sum(f)<0:low=shift
        else:high=shift
    b=np.clip(base+(low+high)/2,BL,BH);f=endpoints(a,b,step)
    states=np.r_[E/2,E/2+np.cumsum(f)]
    np.savez_compressed(OUT/f'interval_{step}s_capacityfree_guide.npz',baseline=b,states=states)
    (OUT/f'interval_{step}s_capacityfree_guide.json').write_text(json.dumps(dict(
        purpose='Nominal capacity-free guide only; may violate inventory limits',
        step_seconds=step,multiplier=lam,common_shift=(low+high)/2,
        cyclic_inventory_residual=float(states[-1]-E/2),
        min_inventory=float(states.min()),max_inventory=float(states.max())),indent=2))
    witness(a,step,0,'capacityfree')
