from pathlib import Path
import json
import numpy as np
from envelope_core import certificate,screen
ROOT=Path(__file__).resolve().parents[1]
rng=np.random.default_rng(20260908)
max_error=0.;cases=0;fallbacks=0
# Independent reference: evolve unconstrained state and clip energy increments.
for n in (1,15,60,900):
    for eta in (0.9,0.94,1.):
        for _ in range(100):
            p=rng.uniform(-1,1,n);dt=1/3600;cap=rng.uniform(0.001,0.25);s=rng.uniform(0,cap)
            increments=np.where(p>=0,-p*dt/eta,-p*dt*eta)
            path=np.r_[0,np.cumsum(increments)]
            c=certificate(p,dt,eta)
            assert np.allclose(c[:3],[path[-1],path.min(),path.max()],rtol=1e-12,atol=1e-12)
            ref=s;loss=0.
            for requested,inc in zip(p,increments):
                nxt=float(np.clip(ref+inc,0,cap));actual=nxt-ref
                served=-actual*eta/dt if actual<=0 else -actual/eta/dt
                loss+=abs(requested-served)*dt;ref=nxt
            final,shortfall,fallback=screen(p,dt,eta,s,cap)
            error=max(abs(final-ref),abs(shortfall-loss));max_error=max(error,max_error)
            assert error<1e-10,(n,eta,error)
            cases+=1;fallbacks+=int(fallback)
# Adversarial zero-mean signal: mean says no movement; native path can fail.
p=np.r_[np.ones(450),-np.ones(450)]
c=certificate(p,1/3600,0.94)
assert c[0]<0 and c[1]<-0.125
report=dict(cases=cases,max_absolute_error=max_error,fallback_cases=fallbacks,adversarial_delta=c[0],adversarial_minimum=c[1],status='PASS')
(ROOT/'results'/'certificate_verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
