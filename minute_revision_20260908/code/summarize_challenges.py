from pathlib import Path
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[1]
for prefix,keys in [('robustness',['capacity_mwh','eta','horizon_hours','measured_feedback','model']),('recovery_scarcity',['capacity_mwh','reserve_mw','supply_mw'])]:
    path=ROOT/'results'/(prefix+'_daily.csv.gz')
    if not path.exists():continue
    d=pd.read_csv(path);d['period']=np.where(d.day<'2025-07-01','calibration',np.where(d.day<'2026-01-01','development','evaluation'))
    g=d.groupby(['period']+keys).agg(deficit_mwh=('native_deficit_mwh','sum'),requested_mwh=('requested_reserve_mwh','sum'),hydrogen_energy_mwh=('hydrogen_energy_mwh','sum'),max_state_error=('maximum_state_error_mwh','max'),initial_inventory=('initial_actual_state_mwh','first'),terminal_inventory=('actual_state_mwh','last')).reset_index()
    g['deficit_pct']=100*g.deficit_mwh/g.requested_mwh
    eta=g.eta if 'eta' in g else .94
    diff=g.initial_inventory-g.terminal_inventory
    g['terminal_restoration_mwh']=np.where(diff>=0,diff/eta,diff*eta)
    g['restored_hydrogen_energy_mwh']=g.hydrogen_energy_mwh-g.terminal_restoration_mwh
    g.to_csv(ROOT/'results'/(prefix+'_summary.csv'),index=False)
    print(prefix)
    if prefix=='recovery_scarcity':print(g.query("period=='evaluation' and reserve_mw==0.75")[['capacity_mwh','supply_mw','deficit_pct','restored_hydrogen_energy_mwh']].to_string(index=False))
    else:print(g.query("period=='evaluation' and capacity_mwh==1 and model in ['native','quarter']")[['eta','horizon_hours','measured_feedback','model','deficit_pct']].to_string(index=False))
