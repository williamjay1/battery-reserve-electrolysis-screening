from pathlib import Path
import pandas as pd,numpy as np,json
ROOT=Path(__file__).resolve().parents[1]
d=pd.read_csv(ROOT/'results'/'electrolyzer_constraints_daily.csv.gz');d=d[d.day>='2026-01-01']
g=d.groupby(['source','capacity_mwh','supply_mw','minimum_load_mw','dwell_quarters']).agg(deficit_mwh=('deficit_mwh','sum'),request_mwh=('request_mwh','sum'),hydrogen_energy_mwh=('hydrogen_energy_mwh','sum'),startups=('startups','sum'),on_hours=('on_hours','sum')).reset_index();g['deficit_pct']=100*g.deficit_mwh/g.request_mwh
g.to_csv(ROOT/'results'/'electrolyzer_constraints_summary.csv',index=False)
errors=[]
for source,path in [('Germany_seconds','recovery_scarcity_daily.csv.gz'),('Belgium','cross_source_daily.csv.gz')]:
    base=pd.read_csv(ROOT/'results'/path)
    if 'source' in base:base=base[base.source==source]
    base=base[(base.day>='2026-01-01')&(base.reserve_mw==.75)]
    ref=d[(d.source==source)&(d.minimum_load_mw==0)]
    z=ref.merge(base,on=['day','capacity_mwh','supply_mw'],suffixes=('_new','_base'),validate='one_to_one')
    errors.append(float((z.deficit_mwh-z.native_deficit_mwh).abs().max()))
assert max(errors)<1e-7,errors
(ROOT/'results'/'electrolyzer_baseline_verification.json').write_text(json.dumps(dict(status='PASS',max_daily_deficit_discrepancy=max(errors)),indent=2))
print(g[(g.capacity_mwh==2)&g.supply_mw.isin([.05,.1])][['source','supply_mw','minimum_load_mw','deficit_pct','startups','on_hours']].to_string(index=False))
