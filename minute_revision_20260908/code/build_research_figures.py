from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]
os.environ['MPLCONFIGDIR']=str(ROOT/'temp'/'matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator
import pandas as pd,numpy as np
OUT=ROOT/'paper'/'figures';OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none'})
def save(fig,name):
    for ext in ('pdf','svg','png'):fig.savefig(OUT/(name+'.'+ext),dpi=900,bbox_inches='tight')
    plt.close(fig)
d=pd.read_csv(ROOT/'results'/'recovery_scarcity_summary.csv')
x=d[(d.period=='evaluation')&(d.reserve_mw==.75)]
fig,ax=plt.subplots(figsize=(6.8,3.9))
colors=plt.cm.viridis(np.linspace(.08,.9,6))
for (s,g),color in zip(x.groupby('supply_mw'),colors):
    ax.plot(g.capacity_mwh,g.deficit_pct,'o-',color=color,label=f'{s:g} MW',lw=1.5,ms=3)
ax.axhline(.5,color='#b64136',ls='--',lw=1,label='0.5% threshold')
ax.set(xlabel='Usable battery capacity (MWh)',ylabel='Reserve energy deficit (%)',xscale='log',xticks=[.5,1,2,4,8])
ax.set_xticklabels(['0.5','1','2','4','8']);ax.grid(axis='y',alpha=.2)
ax.xaxis.set_minor_locator(NullLocator())
ax.legend(title='Scheduled supply',ncol=4,loc='upper center',bbox_to_anchor=(.5,-.19),frameon=False,fontsize=8)
save(fig,'recovery_frontier')

main=pd.read_csv(ROOT/'results'/'germany_main_summary.csv');measured=pd.read_csv(ROOT/'results'/'germany_measured_summary.csv')
fig,axes=plt.subplots(1,2,figsize=(7,3.3),sharey=True)
labels=['native','minute','5minute','quarter']
for ax,table,title in zip(axes,[main,measured],['(a) Modeled state feedback','(b) Ideal state assimilation']):
    g=table[(table.period=='evaluation')&(table.capacity_mwh==1)&(table.reserve_mw==.75)&(table.supply_mw==.5)].set_index('model').loc[labels]
    p=np.arange(4);ax.bar(p-.18,g.predicted_deficit_pct,width=.36,label='Model forecast',color='#5b8ba8');ax.bar(p+.18,g.native_deficit_pct,width=.36,label='Native audit',color='#d88948')
    ax.axhline(.5,color='#b64136',ls='--',lw=1);ax.set_xticks(p,['1 s','1 min','5 min','15 min']);ax.set_title(title,fontsize=10);ax.set_xlabel('Replay resolution');ax.grid(axis='y',alpha=.15)
axes[0].set_ylabel('Reserve energy deficit (%)');axes[1].legend(frameon=False,fontsize=8)
save(fig,'feedback_challenge')

fig,ax=plt.subplots(figsize=(6.8,3.7))
daily=pd.read_csv(ROOT/'results'/'recovery_scarcity_daily.csv.gz',usecols=['day','hours'])
evaluation_hours=daily[daily.day>='2026-01-01'].drop_duplicates('day').hours.sum()
for cap,g in x.groupby('capacity_mwh'):
    g=g[g.supply_mw>0];hours=evaluation_hours
    change=100*(g.restored_hydrogen_energy_mwh/(g.supply_mw*hours)-1)
    ax.plot(g.supply_mw,change,'o-',ms=3,label=f'{cap:g} MWh')
ax.axhline(0,color='grey',lw=.8);ax.set(xlabel='Scheduled supply (MW)',ylabel='Hydrogen input change after\ninventory restoration (%)')
ax.legend(ncol=3,frameon=False,fontsize=8);ax.grid(axis='y',alpha=.2)
save(fig,'hydrogen_tradeoff')
(ROOT/'paper'/'figure_captions.md').write_text('''Figure 1. Recovery supply and storage capacity. German second-resolution replay, January–July 2026, 0.75 MW reserve. Curves show fixed scheduled supply scenarios; dashed line is the study screening threshold.

Figure 2. State feedback and replay bias. Panel (a) uses propagated modeled state; panel (b) assimilates measured state at quarter boundaries. German evaluation period, 1 MWh storage, 0.75 MW reserve and 0.5 MW supply.

Figure 3. Electrolyzer input tradeoff. Percentage change relative to identical scheduled supply without reserve, after stated terminal inventory restoration. Downward activation imports energy; positive changes do not imply renewable hydrogen certification.
''',encoding='utf-8')
print('Three scientific figures saved as vector PDF/SVG and 900 dpi PNG.')
