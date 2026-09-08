from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'paper/figures';OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
def save(fig,name):
    fig.savefig(OUT/(name+'.pdf'),bbox_inches='tight')
    fig.savefig(OUT/(name+'.png'),dpi=900,bbox_inches='tight')
    plt.close(fig)
sources=['Germany_seconds','Germany_quarters','Belgium_quarters']
labels=['German native','German quarter mean','Belgian validated quarter']
d=pd.read_csv(ROOT/'results/control_classification.csv');d=d[d.tau_hours==1]
colors=['#275D90','#E3AC32','#B35B59']
code={'causal_success':0,'policy_avoidable':1,'physically_infeasible':2}
fig,axs=plt.subplots(1,3,figsize=(9,3.2),sharey=True)
for ax,source,label in zip(axs,sources,labels):
    p=d[d.source==source].pivot(index='capacity_mwh',columns='supply_mw',values='classification')
    a=p.map(code.get).to_numpy()
    ax.imshow(a,origin='lower',aspect='auto',cmap=ListedColormap(colors),vmin=-.5,vmax=2.5)
    ax.set_xticks(range(len(p.columns)),[f'{x:g}' for x in p.columns],rotation=45)
    ax.set_yticks(range(len(p.index)),[f'{x:g}' for x in p.index])
    ax.set_xlabel('Supply (MW)');ax.set_title(label,fontsize=10)
axs[0].set_ylabel('Usable capacity (MWh)')
fig.legend(handles=[Patch(color=c,label=l) for c,l in zip(colors,['Causal success','Policy avoidable','Physically infeasible'])],loc='lower center',ncol=3,bbox_to_anchor=(.5,-.04),frameon=False)
fig.subplots_adjust(bottom=.27,wspace=.15)
save(fig,'feasibility')

challenge=json.loads((ROOT/'results/energy_challenge.json').read_text())
fig,axs=plt.subplots(1,2,figsize=(8.7,3.8),sharey=True)
for ax,rows,xlabels in [(axs[0],[challenge[1],challenge[0],challenge[2],challenge[3]],['0.90','0.94','0.98','1.00']),(axs[1], [challenge[4],challenge[0],challenge[5]],['0.8','1.0','1.2'])]:
    for x,row in enumerate(rows):
        low=row['native_feasible_input_mwh']-row['no_reserve_mwh']
        high=row['upper_mwh']-row['no_reserve_mwh']
        ax.plot([x-.09,x-.09],[low,high],color='#275D90',lw=3)
        ax.plot(x-.09,low,'_',color='#275D90',ms=10)
        ax.plot(x-.09,high,'_',color='#275D90',ms=10)
        ax.plot(x+.09,row['quarter_optimum_mwh']-row['no_reserve_mwh'],'o',color='#B35B59',ms=5)
    ax.axhline(0,color='.4',lw=.8,ls='--');ax.set_xticks(range(len(rows)),xlabels)
    ax.grid(axis='y',alpha=.2)
axs[0].set_xlabel('One-way efficiency');axs[1].set_xlabel('Activation multiplier')
axs[0].set_ylabel('Input change from no reserve (MWh)')
axs[0].set_title('(a) Efficiency',fontsize=10);axs[1].set_title('(b) Signal strength',fontsize=10)
fig.legend(handles=[plt.Line2D([0],[0],color='#275D90',lw=3,label='Native feasible–upper range'),plt.Line2D([0],[0],marker='o',color='#B35B59',lw=0,label='Quarter optimum')],loc='lower center',ncol=2,frameon=False)
fig.subplots_adjust(bottom=.24,wspace=.16)
save(fig,'energy_challenge')

d=pd.read_csv(ROOT/'results/monthly_oracle.csv');months=pd.period_range('2025-01','2026-07',freq='M').astype(str).tolist()
fig,axs=plt.subplots(3,1,figsize=(8.7,6),sharex=True,sharey=True)
for ax,source,label in zip(axs,sources,labels):
    for E,color in zip([2,4,8],['#275D90','#BF7627','#59805D']):
        rows=d[(d.source==source)&(d.capacity_mwh==E)].set_index('month')
        vals=[float(rows.loc[m,'supply_upper_mw']) if m in rows.index and rows.loc[m,'status']=='feasible' else np.nan for m in months]
        ax.plot(range(19),vals,'o-',color=color,ms=3,lw=1,label=f'{E} MWh')
        bad=[i for i,m in enumerate(months) if m in rows.index and rows.loc[m,'status']=='infeasible']
        ax.scatter(bad,[.26]*len(bad),marker='x',color=color,s=35)
    ax.set_title(label,loc='left',fontsize=10);ax.set_ylim(-.01,.28);ax.grid(alpha=.15)
    ax.set_ylabel('Supply (MW)')
axs[-1].set_xticks(range(19),months,rotation=60,ha='right',fontsize=8)
axs[0].legend(loc='upper right',ncol=3,frameon=False)
fig.tight_layout()
save(fig,'monthly')
print('Exported three vector PDFs and 900 dpi PNGs.',flush=True)
