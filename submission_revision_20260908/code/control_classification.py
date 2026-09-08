from pathlib import Path
import json
import numpy as np,pandas as pd
from numba import njit
from reachability import reach
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent/'minute_revision_20260908'

@njit(cache=True)
def replay(a,cap,R,eta,S,tau,step,dt):
    s=cap/2;loss=0.;req=0.;wh=0.;under=0.;over=0.
    for q in range(len(a)//step):
        b=min(min(1-R,S),max(max(-(1-R),S-1),(cap/2-s)/tau))
        wh+=(S-b)*step*dt
        for j in range(q*step,(q+1)*step):
            p=R*a[j]-b;inc=(-p/eta if p>=0 else -p*eta)*dt
            nxt=min(cap,max(0.,s+inc))
            actual=-(nxt-s)*eta/dt if nxt<=s else -(nxt-s)/eta/dt
            e=abs(p-actual)*dt;loss+=e
            if p>0:under+=e
            else:over+=e
            req+=abs(R*a[j])*dt;s=nxt
    return loss,req,s,wh,under,over

@njit(cache=True)
def drawdown_bound(a,cap,R,eta,S,dt):
    b=min(1-R,S);total=0.;peak=0.;peakindex=0;draw=0.;start=0;end=0
    for i in range(len(a)):
        p=R*a[i]-b;total+=(-p/eta if p>=0 else -p*eta)*dt
        if total>peak:peak=total;peakindex=i+1
        if peak-total>draw:draw=peak-total;start=peakindex;end=i+1
    return draw,eta*max(0.,draw-cap),start,end

rows=[]
for source,folder,config,step,dt in [('Germany_seconds','germany_seconds','germany_main_config.json',900,1/3600),('Germany_quarters','germany_seconds','germany_main_config.json',1,.25),('Belgium_quarters','belgium_quarters','belgium_validated_config.json',1,.25)]:
    scale=json.loads((BASE/'results'/config).read_text())['scale_mw']
    files=sorted(f for f in (BASE/'datasets'/folder).glob('*.npz') if f.stem>='2026-01-01')
    chunks=[np.clip(np.load(f)['mw']/scale,-1,1) for f in files]
    if source=='Germany_quarters':chunks=[a.reshape(-1,900).mean(axis=1) for a in chunks]
    a=np.concatenate(chunks)
    for cap in [.5,1.,2.,4.,8.]:
        for S in [0.,.025,.05,.1,.2,.4]:
            oracle=reach(a,cap,.75,.94,S,0.,cap/2,cap/2,step,dt)
            bound=drawdown_bound(a,cap,.75,.94,S,dt)
            for tau in [.25,1.,4.]:
                loss,req,terminal,wh,under,over=replay(a,cap,.75,.94,S,tau,step,dt)
                assert loss+1e-7>=bound[1],(source,cap,S,tau,loss,bound)
                causal_ok=loss<1e-7
                if causal_ok:assert oracle[0]
                cls='causal_success' if causal_ok else ('policy_avoidable' if oracle[0] else 'physically_infeasible')
                rows.append(dict(source=source,capacity_mwh=cap,supply_mw=S,tau_hours=tau,oracle_zero_deficit=bool(oracle[0]),causal_zero_deficit=causal_ok,classification=cls,causal_deficit_pct=100*loss/req,causal_deficit_mwh=loss,terminal_mwh=terminal,hydrogen_input_mwh=wh,upward_deficit_mwh=under,downward_deficit_mwh=over,drawdown_mwh=bound[0],unavoidable_deficit_lower_mwh=bound[1],deficit_lower_pct=100*bound[1]/req,witness_start_index=int(bound[2]),witness_end_index=int(bound[3])))
        pd.DataFrame(rows).to_csv(ROOT/'results/control_classification.csv',index=False)
        print(source,cap,'complete',flush=True)
d=pd.DataFrame(rows)
print(d[d.tau_hours==1].groupby(['source','classification']).size().to_string(),flush=True)
(ROOT/'results/control_classification_audit.json').write_text(json.dumps(dict(status='PASS',rows=len(d),same_initial_inventory=True,terminal_condition='unconstrained for both causal and oracle in classification',same_metric='zero AC tracking deficit within 1e-7 MWh tolerance',lower_bound_exceeds_actual_cases=0),indent=2))
