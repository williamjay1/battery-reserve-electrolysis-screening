from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
r=ROOT/'results';d=ROOT/'docs'
tables={name:pd.read_csv(r/(name+'.csv')) for name in ['hydrogen_matrix','oracle_frontier','control_classification','monthly_oracle']}
parts=['# Result ledger\n\nExact machine-readable source values follow. Rounding belongs only in display tables. All results are deterministic conditional on the specified traces; optimization brackets are not confidence intervals.']
for name,table in tables.items():
    parts.append('## '+name+'\n\nSource: results/'+name+'.csv\n\n```csv\n'+table.to_csv(index=False)+'```')
parts.append('## Matched energy challenges\n\nSource: results/energy_challenge.json\n\n```json\n'+(r/'energy_challenge.json').read_text()+'\n```')
(d/'RESULT_LEDGER.md').write_text('\n\n'.join(parts),encoding='utf8')
month=tables['monthly_oracle'];valid=month[month.status=='feasible']
summary=valid.groupby(['source','capacity_mwh']).supply_upper_mw.agg(['count','min','median','max'])
print(summary.to_string())
print('Monthly statuses:',month.status.value_counts().to_dict())
control=tables['control_classification']
print(control[control.tau_hours==1].groupby(['source','classification']).size().to_string())
(r/'monthly_summary.csv').write_text(summary.to_csv(),encoding='utf8')
