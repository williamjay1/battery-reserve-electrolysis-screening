from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
de=json.loads((ROOT/'results/distribution_envelope.json').read_text())
gb=json.loads((ROOT/'results/gb_transfer.json').read_text())
assert len(gb)==42
ks=[1,3,9,45,225,900]
plt.rcParams.update({'font.size':10,'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(1,2,figsize=(9,3.7),layout='constrained')
for rows,label,col,mark in [(de,'German conditions','#2378a6','o'),(gb,'GB frequency input','#c44e52','s')]:
    ax[0].plot(ks,[max(r['width_kw'] for r in rows if r['k']==k) for k in ks],marker=mark,color=col,label=label)
ax[0].axhline(.1,color='.35',ls=':',label='0.1 kW tolerance')
ax[0].set_xscale('log');ax[0].set_yscale('log');ax[0].set_xticks(ks,labels=[str(k) for k in ks]);ax[0].set_xlabel('Rank groups per quarter');ax[0].set_ylabel('Maximum interval width (kW)');ax[0].set_title('(a) Accuracy across inputs',loc='left');ax[0].legend(frameon=False,fontsize=8)
months=sorted(set(r['month'] for r in gb))
for k,label,col,marker in [(1,'Quarter mean','#c44e52','s'),(900,'Native relaxed bound','#2378a6','o')]:
    rows=[next(r for r in gb if r['month']==m and r['k']==k) for m in months]
    ax[1].plot(range(7),[r['upper_relaxed_mwh']-r['no_reserve_mwh'] for r in rows],marker=marker,color=col,label=label)
ax[1].axhline(0,color='.35',lw=.8);ax[1].set_xticks(range(7),labels=['Jan','Feb','Mar','Apr','May','Jun','Jul']);ax[1].set_ylabel('Upper bound minus $H_0$ (MWh)');ax[1].set_xlabel('Month in 2026');ax[1].set_title('(b) GB energy screen',loc='left');ax[1].legend(frameon=False,fontsize=8,loc='upper left',bbox_to_anchor=(0,.85))
for a in ax:a.grid(alpha=.15)
fig.savefig(ROOT/'paper/figures/error_transfer.pdf');fig.savefig(ROOT/'paper/figures/error_transfer.png',dpi=900)

