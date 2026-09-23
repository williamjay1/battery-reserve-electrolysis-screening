"""Collect completed values without substituting pending computations."""
import csv, hashlib, json, platform
import numpy as np
import scipy, numba
from numba import njit
from run_interval_bounds import OUT, INPUT, E, R, S, ETA, audit_schedule

def read(name):return json.loads((OUT/name).read_text())

@njit(cache=True)
def energy_audit(a,b,step):
    signed=0.;charge=0.;discharge=0.
    for i in range(len(a)):
        u=R*a[i];signed+=u/3600;p=u-b[i//step]
        if p>=0:discharge+=p/3600
        else:charge-=p/3600
    return signed,charge,discharge

if __name__=='__main__':
    a=np.load(INPUT,mmap_mode='r');H0=len(a)/3600*S
    reference_lower=read('guided_witness_900s_round3_policy0.json')
    refschedule=np.load(OUT/'guided_witness_900s_round3_policy0.npz')['baseline']
    reference_upper=read('upper_900s_round3_certificate.json')
    rows=[]
    for step in [60,300,900]:
        q=read(f'interval_{step}s_quick.json');co=read(f'interval_{step}s_coarse_network.json')
        inherited=audit_schedule(a,np.repeat(refschedule,900//step),E/2,E,R,ETA,S,0.,step)
        assert inherited[4]<1e-9 and abs(inherited[0]-E/2)<1e-9
        inherited_record=dict(source='refined 900 s witness repeated',hydrogen_lower_mwh=inherited[3],
            end_inventory=inherited[0],minimum_inventory=inherited[1],maximum_inventory=inherited[2],
            maximum_violation=inherited[4],terminal_residual=abs(inherited[0]-E/2))
        (OUT/f'inherited_refined_witness_{step}s.json').write_text(json.dumps(inherited_record,indent=2))
        candidates=[inherited_record,dict(source='new reachability reconstruction',**q['new_reachability_witness'])]
        for f in sorted(OUT.glob(f'guided_witness_{step}s_*.json')):
            candidate=json.loads(f.read_text());candidate['source']=f.name;candidates.append(candidate)
        best=max(candidates,key=lambda z:z['hydrogen_lower_mwh'])
        upper=reference_upper['hydrogen_upper_mwh'] if step==900 else q['capacity_free_upper_mwh']
        row=dict(step_seconds=step,intervals=len(a)//step,H0_mwh=H0,
                 exact_coarse_mwh=co['exact_coarse_mwh'],native_lower_mwh=best['hydrogen_lower_mwh'],
                 native_lower_source=best['source'],native_upper_mwh=upper,
                 native_upper_type='finite capacity, 20 inverse supports' if step==900 else 'capacity-free evaluated dual',
                 capacity_free_upper_mwh=q['capacity_free_upper_mwh'],
                 native_bracket_mwh=upper-best['hydrogen_lower_mwh'],
                 native_gap_pct_upper=100*(upper-best['hydrogen_lower_mwh'])/upper,
                 native_exclusion_margin_mwh=H0-upper,coarse_gain_mwh=co['exact_coarse_mwh']-H0,
                 conclusion='aggregation false positive' if co['exact_coarse_mwh']>H0 and upper<H0 else 'consistent loss',
                 native_candidates=candidates,coarse_validation=co)
        rows.append(row)
    signed,charge,discharge=energy_audit(a,refschedule,900)
    kappa=(1-ETA**2)/(1+ETA**2)
    ref=rows[-1]
    reference=dict(reference_lower=reference_lower,reference_upper=reference_upper,
        gap_mwh=ref['native_bracket_mwh'],gap_pct_upper=ref['native_gap_pct_upper'],
        coarse_overstatement_lower_mwh=ref['exact_coarse_mwh']-ref['native_upper_mwh'],
        coarse_overstatement_upper_mwh=ref['exact_coarse_mwh']-ref['native_lower_mwh'],
        native_upper_loss_pct_H0=100*(ref['native_upper_mwh']-H0)/H0,
        native_lower_loss_pct_H0=100*(ref['native_lower_mwh']-H0)/H0,
        signed_activation_energy_mwh=signed,throughput_gain_threshold_mwh=-signed/kappa,
        implied_native_minimum_throughput_mwh=(H0-signed-ref['native_upper_mwh'])/kappa,
        feasible_native_charge_mwh=charge,feasible_native_discharge_mwh=discharge,
        feasible_native_throughput_mwh=charge+discharge,
        native_energy_identity_residual_mwh=(H0-signed-kappa*(charge+discharge))-ref['native_lower_mwh'])
    hs=hashlib.sha256()
    with INPUT.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):hs.update(chunk)
    manifest=dict(status='COMPLETE',description='Executed retrospective native bound refinement and decision-interval sensitivity',
        input_sha256=hs.hexdigest(),input_samples=len(a),input_duration_hours=len(a)/3600,
        operating_parameters=dict(capacity_mwh=E,reserve_mw=R,supply_mw=S,eta=ETA,initial_final_inventory_mwh=E/2),
        software=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,numba=numba.__version__),
        independent_small_instance_audit=read('small_instance_audit.json'),
        active_constraint_audit=read('active_constraint_audit.json'),
        reference=reference,decision_intervals=rows)
    (OUT/'final_manifest.json').write_text(json.dumps(manifest,indent=2))
    with (OUT/'decision_interval_table.csv').open('w',newline='') as f:
        fields=[k for k in rows[0] if k not in ('native_candidates','coarse_validation')]
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        writer.writerows({k:r[k] for k in fields} for r in rows)
    print(json.dumps(dict(reference=reference,decision_intervals=[{k:r[k] for k in fields} for r in rows]),indent=2))
