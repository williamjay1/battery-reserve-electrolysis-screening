from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
rows=json.loads((ROOT/'results/distribution_screen/results.json').read_text())
r=[x for x in rows if x['case']=='full']; k=[x['k'] for x in r]
plt.rcParams.update({'font.size':10,'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(1,2,figsize=(9,3.6),layout='constrained')
ax[0].plot(k,[x['temporal_upper_mwh']-508.7 for x in r],'s--',color='#c44e52',label='Time groups')
ax[0].plot(k,[x['upper_mwh']-508.7 for x in r],'o-',color='#2378a6',label='Rank groups')
ax[0].axhline(0,color='.35',lw=.8);ax[0].set_xscale('log');ax[0].set_xlabel('Representatives per quarter');ax[0].set_ylabel('Upper bound minus $H_0$ (MWh)');ax[0].legend(frameon=False);ax[0].set_title('(a) Equal summary size',loc='left')
ax[1].plot(k,[x['query_median_seconds'] for x in r],'o-',color='#2378a6',label='Bound query')
ax[1].plot(k,[x['sorting_seconds']+x['summary_seconds']+x['query_median_seconds'] for x in r],'s--',color='#7462a0',label='Sort, summarize and query')
ax[1].set_xscale('log');ax[1].set_yscale('log');ax[1].set_xlabel('Representatives per quarter');ax[1].set_ylabel('Wall time (s)');ax[1].set_title('(b) Computation cost',loc='left');ax[1].legend(frameon=False)
for a in ax:a.set_xticks([1,3,9,45,225,900],labels=['1','3','9','45','225','900']);a.grid(alpha=.15)
out=ROOT/'paper/figures';fig.savefig(out/'distribution_screen.pdf');fig.savefig(out/'distribution_screen.png',dpi=900)
