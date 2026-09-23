"""Retrospective decision-duration sensitivity and audited native bounds.

Native physics is always replayed at one second. Evaluated dual objectives are
upper bounds on electrical allocation; feasible schedules are lower bounds.
"""
import os
os.environ.setdefault('NUMBA_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
from pathlib import Path
import argparse, csv, hashlib, json, time
import numpy as np
from numba import njit
from scipy.optimize import linprog
from scipy.sparse import coo_matrix
from reachability import reach, reconstruct, audit_schedule, features, interval_step

ROOT = Path(os.environ.get('SCREEN_PROJECT_ROOT', str(Path(__file__).resolve().parents[2])))
OUT = Path(os.environ.get('SCREEN_INTERVAL_OUTPUT', str(ROOT / 'results' / 'interval_bounds')))
INPUT = Path(os.environ.get('SCREEN_NATIVE_INPUT', str(ROOT / 'prepared_inputs' / 'native_evaluation.npy')))
E, R, S, ETA = 2.0, .75, .1, .94
BL, BH = -.25, .1

def save(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2), encoding='utf-8')
    print(json.dumps({'saved':name, **data}, default=str), flush=True)

@njit(cache=True)
def eval_dual(u, prefix, lam, eta, bl, bh, seconds):
    n,m=u.shape
    fraction=(1/eta-1/lam)/(1/eta-eta)
    idx=max(0,min(m-1,int(np.ceil(fraction*m))-1))
    cost=0.; sf=0.
    for q in range(n):
        b=bl if fraction<=0 else (bh if fraction>=1 else min(bh,max(bl,u[q,idx])))
        j=np.searchsorted(u[q],b,side='right')
        charge=(j*b-prefix[q,j])/3600
        discharge=(prefix[q,m]-prefix[q,j]-(m-j)*b)/3600
        f=eta*charge-discharge/eta
        sf+=f;cost+=b*seconds/3600-lam*f
    return cost,sf

def capfree(a, step):
    t=time.perf_counter();u=np.sort(R*np.asarray(a).reshape(-1,step),axis=1)
    prefix=np.c_[np.zeros(len(u)),np.cumsum(u,axis=1)]
    lo,hi=ETA,1/ETA;best=(-np.inf,0.,0.)
    for _ in range(55):
        lam=(lo+hi)/2;dual,f=eval_dual(u,prefix,lam,ETA,BL,BH,step)
        if dual>best[0]:best=(dual,lam,f)
        if f<0:lo=lam
        else:hi=lam
    return dict(capacity_free_upper_mwh=S*len(a)/3600-best[0]+1e-6,
                dual_cost_mwh=best[0],multiplier=best[1],inventory_sum_at_selected_multiplier=best[2],
                numerical_margin_mwh=1e-6,seconds=time.perf_counter()-t)

def quick(a, step):
    t=time.perf_counter();r=capfree(a,step)
    legacy=Path(os.environ.get('SCREEN_LEGACY_WITNESS', str(OUT/'native_reachability_900s.npz')))
    if legacy.exists():
        old=np.load(legacy);b=old['baseline_mw'] if 'baseline_mw' in old else old['baseline']
        inherited=np.repeat(b,900//step)
        ia=audit_schedule(a,inherited,E/2,E,R,ETA,S,0.,step)
        assert ia[4]<1e-7 and abs(ia[0]-E/2)<1e-7,ia
        r['inherited_witness']={'hydrogen_lower_mwh':ia[3], 'end_inventory':ia[0],
                               'min_inventory':ia[1],'max_inventory':ia[2],'maximum_violation':ia[4]}
    t0=time.perf_counter();ok,n,ls,us,bl,bh=reach(a,E,R,ETA,S,0.,E/2,E/2,step)
    assert ok and ls[-1]<=E/2<=us[-1],(ok,n,ls[-1],us[-1])
    b,states=reconstruct(a,E,R,ETA,ls,us,bl,bh,E/2,step)
    au=audit_schedule(a,b,E/2,E,R,ETA,S,0.,step)
    assert au[4]<1e-7 and abs(au[0]-E/2)<1e-7,au
    np.savez_compressed(OUT/f'native_reachability_{step}s.npz',baseline=b,states=states)
    r['new_reachability_witness']={'hydrogen_lower_mwh':au[3],'end_inventory':au[0],
                'min_inventory':au[1],'max_inventory':au[2],'maximum_violation':au[4],
                'seconds':time.perf_counter()-t0}
    r.update(step_seconds=step,sample_seconds=1,samples=len(a),intervals=len(a)//step,
             horizon_hours=len(a)/3600,H0_mwh=S*len(a)/3600,total_seconds=time.perf_counter()-t)
    save(f'interval_{step}s_quick.json',r)

def solve_endpoint(fs,cs,knots,E=E,S=S,step=900,method='highs-ipm',certificate_path=None):
    n,K=fs.shape;dt=step/3600;s0=E/2
    coeff=np.c_[np.ones(n),-np.ones(n),cs]
    rhs=np.c_[fs[:,1],-fs[:,0],cs*fs-knots]
    rhs[0,:]+=coeff[0,:]*s0
    m=K+2;rr=np.arange(n*m).reshape(n,m);q=np.repeat(np.arange(n)[:,None],m,axis=1)
    rows=[rr.ravel(),rr[1:].ravel(),rr[:,2:].ravel()]
    cols=[q.ravel(),(q[1:]-1).ravel(),(q[:,2:]+n).ravel()]
    vals=[coeff.ravel(),-coeff[1:].ravel(),-np.ones(n*K)]
    A=coo_matrix((np.concatenate(vals),(np.concatenate(rows),np.concatenate(cols))),shape=(n*m,2*n)).tocsr()
    c=np.r_[np.zeros(n),np.full(n,dt)]
    lower=np.r_[np.zeros(n-1),s0,np.full(n,BL)]
    upper=np.r_[np.full(n-1,E),s0,np.full(n,BH)]
    t=time.perf_counter()
    out=linprog(c,A_ub=A,b_ub=rhs.ravel(),bounds=np.c_[lower,upper],method=method,
                options={'threads':1,'time_limit':900.})
    assert out.success,out.message
    y=np.minimum(out.ineqlin.marginals,0.)
    residual=c-A.T@y
    dual=float(rhs.ravel()@y+lower@np.maximum(residual,0)+upper@np.minimum(residual,0))
    assert dual<=out.fun+1e-5,(dual,out.fun)
    report=dict(step_seconds=step,capacity_mwh=E,supply_mw=S,intervals=n,supports_per_interval=K,
        method=method,primal_objective=float(out.fun),dual_lower_objective=dual,
        duality_gap=float(out.fun-dual),roundoff_margin_mwh=1e-6,
        hydrogen_upper_mwh=float(S*n*dt-dual+1e-6),iterations=int(out.nit),seconds=time.perf_counter()-t,
        max_inequality_violation=float(max(0,np.max(A@out.x-rhs.ravel()))),
        max_full_stationarity_residual=float(np.max(np.abs(residual-out.lower.marginals-out.upper.marginals))),
        max_positive_inequality_dual=float(max(0,np.max(out.ineqlin.marginals))),
        evaluated_inequality_dual_cost=float(rhs.ravel()@y),
        box_residual_correction_mwh=float(lower@np.maximum(residual,0)+upper@np.minimum(residual,0)))
    if certificate_path is not None:
        np.savez_compressed(certificate_path,y=y,knots=knots,fs=fs,cs=cs,
            variable_lower=lower,variable_upper=upper,objective=c,primal_x=out.x,
            baseline_lower=BL,baseline_upper=BH,capacity_mwh=E,supply_mw=S,
            reserve_mw=R,eta=ETA,step_seconds=step,sample_seconds=1,numerical_margin_mwh=1e-6)
        report['certificate_file']=Path(certificate_path).name
    return report,np.r_[s0,out.x[:n]],out.x[n:]

@njit(cache=True)
def supports(a, knots, step, eta=ETA):
    n,K=knots.shape;fs=np.empty((n,K));cs=np.empty((n,K))
    for q in range(n):
        for j in range(K):
            b=knots[q,j];f=0.;deriv=0.
            for i in range(q*step,(q+1)*step):
                p=R*a[i]-b
                f+=(-p/eta if p>=0 else -p*eta)/3600
                deriv+=(eta if p<=0 else 1/eta)/3600
            fs[q,j]=f;cs[q,j]=1/deriv
    return fs,cs

@njit(cache=True)
def inverse_increments(a, target, step, eta=ETA):
    bs=np.empty(len(target))
    for q in range(len(target)):
        lo=BL;hi=BH
        for _ in range(40):
            mid=(lo+hi)/2
            v=features(a,q*step,(q+1)*step,mid,R,eta,1/3600)[0]
            if v<target[q]:lo=mid
            else:hi=mid
        bs[q]=(lo+hi)/2
    return bs

def coarse(a,step,pilot=False):
    t=time.perf_counter();u=R*np.asarray(a).reshape(-1,step).mean(axis=1);n=len(u);dt=step/3600
    if pilot:u=u[:200];n=len(u)
    knots=np.tile(np.array([BL,BH]),(n,1))
    # Both exact inverse branches are globally affine and must be retained.
    fs=np.empty((n,2));cs=np.tile(np.array([ETA/dt,1/(ETA*dt)]),(n,1))
    # solve_endpoint uses first two columns as exact endpoint bounds. To encode
    # inverse planes, append two branch-specific support values at u, with
    # coefficients eta/dt and 1/(eta*dt), and retain bound-column tangents too.
    for j,b in enumerate([BL,BH]):
        p=u-b;fs[:,j]=np.where(p>=0,-p/ETA,-p*ETA)*dt
    deriv=np.where(u[:,None]-knots>=0,dt/ETA,dt*ETA)
    fs=np.c_[fs,np.zeros((n,2))]
    cs=np.c_[1/deriv,cs]
    knots=np.c_[knots,np.repeat(u[:,None],2,axis=1)]
    report,states,b=solve_endpoint(fs,cs,knots,step=step)
    p=u-b;exact=np.where(p>=0,-p/ETA,-p*ETA)*dt
    equation=float(np.max(np.abs(np.diff(states)-exact)))
    replay=E/2+np.cumsum(exact)
    violation=float(max(0,-replay.min(),replay.max()-E,abs(replay[-1]-E/2)))
    assert equation<1e-6 and violation<1e-5,(equation,violation)
    report.update(exact_coarse_mwh=float(np.sum(S-b)*dt),maximum_equation_residual=equation,
                  maximum_replay_violation=violation,total_seconds=time.perf_counter()-t)
    suffix='pilot' if pilot else 'coarse'
    np.savez_compressed(OUT/f'interval_{step}s_{suffix}.npz',baseline=b,states=states)
    save(f'interval_{step}s_{suffix}.json',report)

def upper(a,step,rounds):
    n=len(a)//step
    # First two columns always represent the physical baseline endpoints.
    knots=np.tile(np.r_[BL,BH,np.linspace(BL,BH,17)[1:-1]],(n,1))
    fs,cs=supports(a,knots,step)
    for k in range(rounds+1):
        report,states,b=solve_endpoint(fs,cs,knots,step=step)
        report['adaptive_round']=k
        np.savez_compressed(OUT/f'upper_{step}s_round{k}.npz',states=states,baseline=b)
        save(f'upper_{step}s_round{k}.json',report)
        if k<rounds:
            added=inverse_increments(a,np.diff(states),step)[:,None]
            addf,addc=supports(a,added,step)
            knots=np.c_[knots,added];fs=np.c_[fs,addf];cs=np.c_[cs,addc]

@njit(cache=True)
def backward_reach(a,step,cap=E):
    rev=-a[::-1].copy();n=len(a)//step;ls=np.empty(n+1);us=np.empty(n+1)
    ls[0]=cap/2;us[0]=cap/2
    for q in range(n):
        ok,l,u,_,_=interval_step(rev,q*step,(q+1)*step,-BH,-BL,cap,ls[q],us[q],R,1/ETA,1/3600)
        if not ok:raise ValueError('Backward problem infeasible')
        ls[q+1]=l;us[q+1]=u
    return ls[::-1].copy(),us[::-1].copy()

@njit(cache=True)
def guided(a,step,targets,desired_b,back_l,back_u,policy,cap=E):
    n=len(targets)-1;seq=np.empty(n);states=np.empty(n+1);states[0]=cap/2
    for q in range(n):
        start=q*step;stop=(q+1)*step;s=states[q]
        # Project only the construction query coordinate at machine roundoff.
        # The state accumulator itself is unchanged, and an unclipped physical
        # replay below must validate the resulting schedule independently.
        query_s=min(cap,max(0.,s))
        if abs(query_s-s)>1e-12:raise ValueError('Construction coordinate exceeds roundoff tolerance')
        ok,_,_,bl,bh=interval_step(a,start,stop,BL,BH,cap,query_s,query_s,R,ETA,1/3600)
        if not ok:raise ValueError('Forward problem infeasible')
        lo=bl;hi=bh
        if s+features(a,start,stop,lo,R,ETA,1/3600)[0]<back_l[q+1]:
            l=lo;h=hi
            for _ in range(45):
                mid=(l+h)/2
                if s+features(a,start,stop,mid,R,ETA,1/3600)[0]<back_l[q+1]:l=mid
                else:h=mid
            lo=h
        if s+features(a,start,stop,hi,R,ETA,1/3600)[0]>back_u[q+1]:
            l=lo;h=hi
            for _ in range(45):
                mid=(l+h)/2
                if s+features(a,start,stop,mid,R,ETA,1/3600)[0]>back_u[q+1]:h=mid
                else:l=mid
            hi=l
        if lo>hi+1e-8:raise ValueError('Future interval mismatch')
        if policy==0:
            b=min(hi,max(lo,desired_b[q]))
        else:
            l=lo;h=hi
            for _ in range(40):
                mid=(l+h)/2
                if s+features(a,start,stop,mid,R,ETA,1/3600)[0]<targets[q+1]:l=mid
                else:h=mid
            b=(l+h)/2
        seq[q]=b;states[q+1]=s+features(a,start,stop,b,R,ETA,1/3600)[0]
    return seq,states

def witness(a,step,round_id,guide='native'):
    guide_file=(f'upper_{step}s_round{round_id}.npz' if guide=='native' else
                f'interval_{step}s_coarse_network.npz' if guide=='coarse' else f'interval_{step}s_capacityfree_guide.npz')
    label=f'round{round_id}' if guide=='native' else f'{guide}_guide'
    sol=np.load(OUT/guide_file);t=time.perf_counter()
    guard=1e-7;safe_cap=E-2*guard
    ls,us=backward_reach(np.asarray(a),step,safe_cap)
    for policy in [0,1]:
        b,states=guided(a,step,sol['states']-guard,sol['baseline'],ls,us,policy,safe_cap)
        states+=guard
        au=audit_schedule(a,b,E/2,E,R,ETA,S,0.,step)
        assert au[4]<1e-7 and abs(au[0]-E/2)<1e-7,au
        np.savez_compressed(OUT/f'guided_witness_{step}s_{label}_policy{policy}.npz',baseline=b,states=states)
        save(f'guided_witness_{step}s_{label}_policy{policy}.json',
             dict(step_seconds=step,adaptive_round=round_id if guide=='native' else None,guide=guide,policy=policy,
                  policy_name=['clamp relaxed baseline','track relaxed endpoint'][policy],
                  hydrogen_lower_mwh=au[3],end_inventory=au[0],min_inventory=au[1],max_inventory=au[2],
                  maximum_violation=au[4],inventory_safety_margin_mwh=guard,total_seconds=time.perf_counter()-t))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['quick','coarse','pilot','upper','witness'])
    ap.add_argument('--step',type=int,choices=[60,300,900],default=900)
    ap.add_argument('--rounds',type=int,default=3);ap.add_argument('--guide',choices=['native','coarse','capacityfree'],default='native')
    ap.add_argument('--input',type=Path,default=INPUT);ap.add_argument('--output',type=Path,default=OUT);args=ap.parse_args()
    INPUT=args.input;OUT=args.output
    OUT.mkdir(parents=True,exist_ok=True);a=np.load(INPUT,mmap_mode='r')
    assert len(a)==18313200 and len(a)%args.step==0
    print(json.dumps({'phase':args.phase,'step':args.step,'samples':len(a),'time_started':time.strftime('%Y-%m-%d %H:%M:%S')}),flush=True)
    if args.phase=='quick':quick(a,args.step)
    elif args.phase in ['coarse','pilot']:coarse(a,args.step,args.phase=='pilot')
    elif args.phase=='upper':upper(a,args.step,args.rounds)
    elif args.phase=='witness':witness(a,args.step,args.rounds,args.guide)
