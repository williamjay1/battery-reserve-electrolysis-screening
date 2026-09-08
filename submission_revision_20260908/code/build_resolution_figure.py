from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
resolution=json.loads((ROOT/'results/resolution_challenge/results.json').read_text())
monthly=json.loads((ROOT/'results/monthly_energy_challenge/results.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
fig,axs=plt.subplots(1,2,figsize=(9,4.1))
for i,r in enumerate(resolution):
    lo=r['lower_mwh']-r['no_reserve_mwh'];hi=r['reported_upper_mwh']-r['no_reserve_mwh']
    axs[0].plot([i,i],[lo,hi],color='#275D90',lw=2)
    axs[0].plot([i,i],[lo,hi],'_',color='#275D90',ms=8)
    if r['scale_seconds']==900:axs[0].plot(i,lo,'o',color='#B35B59',ms=5)
for i,r in enumerate(monthly):
    lo=r['native_lower_mwh']-r['no_reserve_mwh'];hi=r['native_upper_mwh']-r['no_reserve_mwh']
    axs[1].plot([i-.1,i-.1],[lo,hi],color='#275D90',lw=2)
    axs[1].plot([i-.1,i-.1],[lo,hi],'_',color='#275D90',ms=8)
    axs[1].plot(i+.1,r['quarter_optimum_mwh']-r['no_reserve_mwh'],'o',color='#B35B59',ms=4)
axs[0].set_xticks(range(8),['1 s','5 s','15 s','30 s','1 min','3 min','5 min','15 min'],rotation=45,ha='right')
axs[1].set_xticks(range(7),['Jan','Feb','Mar','Apr','May','Jun','Jul'])
axs[0].set_xlabel('Input averaging scale');axs[1].set_xlabel('Separate month in 2026')
axs[0].set_title('(a) Fixed full-period horizon',fontsize=10)
axs[1].set_title('(b) Monthly cyclic operation',fontsize=10)
for ax in axs:
    ax.axhline(0,color='.4',lw=.8,ls='--');ax.grid(axis='y',alpha=.2)
    ax.set_ylabel('Input change from no reserve (MWh)')
fig.legend(handles=[plt.Line2D([0],[0],color='#275D90',lw=2,label='Feasible–upper range'),plt.Line2D([0],[0],marker='o',color='#B35B59',lw=0,label='Exact 15-minute optimum')],loc='lower center',ncol=2,frameon=False)
fig.subplots_adjust(bottom=.29,wspace=.28,top=.9)
out=ROOT/'paper/figures';out.mkdir(exist_ok=True)
fig.savefig(out/'resolution_horizon.pdf',bbox_inches='tight')
fig.savefig(out/'resolution_horizon.png',dpi=900,bbox_inches='tight')
plt.close(fig)
