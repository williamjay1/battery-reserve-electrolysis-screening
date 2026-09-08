from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
d=pd.read_csv(ROOT/'results'/'germany_measured_daily.csv.gz')
d['period']=np.where(d.day<'2025-07-01','calibration',np.where(d.day<'2026-01-01','development','evaluation'))
keys=['period','capacity_mwh','reserve_mw','supply_mw','model']
g=d.groupby(keys,sort=True).agg(native_deficit_mwh=('native_deficit_mwh','sum'),predicted_deficit_mwh=('predicted_deficit_mwh','sum'),requested_reserve_mwh=('requested_reserve_mwh','sum'),hydrogen_energy_mwh=('hydrogen_energy_mwh','sum'),baseline_charge_mwh=('baseline_charge_mwh','sum'),maximum_state_error_mwh=('maximum_state_error_mwh','max'),initial_inventory_mwh=('initial_actual_state_mwh','first'),terminal_inventory_mwh=('actual_state_mwh','last'),hours=('hours','sum')).reset_index()
g['native_deficit_pct']=100*g.native_deficit_mwh/g.requested_reserve_mwh
g['predicted_deficit_pct']=100*g.predicted_deficit_mwh/g.requested_reserve_mwh
g.loc[g.model.eq('gross'),'predicted_deficit_pct']=np.nan
# Restore to the starting inventory using AC-side charging or discharge.
inventory=g.initial_inventory_mwh-g.terminal_inventory_mwh
g['terminal_restoration_mwh']=np.where(inventory>=0,inventory/.94,inventory*.94)
g['restored_hydrogen_energy_mwh']=g.hydrogen_energy_mwh-g.terminal_restoration_mwh
g['restored_hydrogen_change_mwh']=g.restored_hydrogen_energy_mwh-g.supply_mw*g.hours
g.to_csv(ROOT/'results'/'germany_measured_summary.csv',index=False)
decisions=[]
for threshold in (.1,.5,1.):
    for key,x in g[g.model.ne('gross')].groupby(['period','reserve_mw','supply_mw','model']):
        x=x.sort_values('capacity_mwh');passing=x[x.predicted_deficit_pct<=threshold]
        if len(passing):
            a=passing.iloc[0];cap=float(a.capacity_mwh);actual=float(a.native_deficit_pct);false=actual>threshold
        else:cap=None;actual=None;false=None
        decisions.append(dict(zip(['period','reserve_mw','supply_mw','model'],key))|dict(threshold_pct=threshold,selected_capacity_mwh=cap,native_deficit_pct=actual,false_feasible=false))
pd.DataFrame(decisions).to_csv(ROOT/'results'/'germany_measured_capacity_decisions.csv',index=False)
# Paired blocks retain daily serial dependence; no per-second sample inflation.
rng=np.random.default_rng(20260908);cis=[]
focus=d[(d.period=='evaluation')&(d.capacity_mwh==1)&(d.reserve_mw==.75)&(d.supply_mw==.5)]
base=focus[focus.model=='native'].set_index('day')
for label in ['minute','5minute','quarter','gross','envelope']:
    x=focus[focus.model==label].set_index('day').loc[base.index]
    delta=(x.native_deficit_mwh-base.native_deficit_mwh).to_numpy();den=base.requested_reserve_mwh.to_numpy();n=len(delta)
    for block in (3,7,14):
        starts=rng.integers(0,n,size=(2000,int(np.ceil(n/block))))
        ix=((starts[:,:,None]+np.arange(block))%n).reshape(2000,-1)[:,:n]
        stat=100*delta[ix].sum(axis=1)/den[ix].sum(axis=1)
        cis.append(dict(model=label,block_days=block,estimate_percentage_points=float(100*delta.sum()/den.sum()),ci_low=float(np.quantile(stat,.025)),ci_high=float(np.quantile(stat,.975))))
pd.DataFrame(cis).to_csv(ROOT/'results'/'germany_measured_paired_uncertainty.csv',index=False)
print(g[(g.period=='evaluation')&(g.reserve_mw==.75)&(g.supply_mw==.5)][['capacity_mwh','model','native_deficit_pct','predicted_deficit_pct','restored_hydrogen_change_mwh']].to_string(index=False))
print('Capacity selection audit:')
print(pd.DataFrame(decisions).query("period == 'evaluation' and threshold_pct == 0.5").groupby('model').false_feasible.agg(['sum','count']).to_string())

