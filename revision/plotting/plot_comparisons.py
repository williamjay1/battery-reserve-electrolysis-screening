"""Redraw saved model comparisons; no optimization or timing is rerun.

Inputs in data/comparison_*.json are copies of the frozen derived result files.
Source hashes and the input-to-panel mapping are recorded alongside this script.
"""
from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import NullLocator, FuncFormatter
from journal_style import WIDTH, BLUE, ORANGE, GREY, clean, panel, save

HERE = Path(__file__).resolve().parent
DATA = HERE / 'data'

def read(name):
    return json.loads((DATA / f'comparison_{name}.json').read_text(encoding='utf-8-sig'))

def bracket(ax, x, low, high, *, offset=0, cap=.070, color=BLUE):
    """A square feasible witness and capped upper bound; never a CI glyph."""
    x += offset
    ax.vlines(x, low, high, color=color, lw=1.25, zorder=3)
    ax.hlines(high, x-cap, x+cap, color=color, lw=1.1, zorder=4)
    ax.plot(x, low, marker='s', markersize=3.5, color=color, markeredgewidth=0,
            linestyle='none', zorder=5)

def optimization_legend(fig, *, y=.06):
    handles = [
        Line2D([], [], color=BLUE, lw=1.2, marker='s', markersize=3.3,
               label='Native optimization bounds'),
        Line2D([], [], color=ORANGE, lw=0, marker='D', markersize=3.7,
               label='Exact quarter optimum'),
    ]
    fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(.53,y),
               ncol=2, columnspacing=1.8, handletextpad=.65, handlelength=1.7)

def distribution():
    rows = sorted([r for r in read('distribution') if r['case']=='full'], key=lambda r:r['k'])
    k = np.array([r['k'] for r in rows])
    h0 = rows[0]['no_reserve_mwh']
    rank = np.array([r['upper_mwh']-h0 for r in rows])
    temporal = np.array([r['temporal_upper_mwh']-h0 for r in rows])
    query = np.array([r['query_median_seconds'] for r in rows])
    total = np.array([r['sorting_seconds']+r['summary_seconds']+r['query_median_seconds'] for r in rows])
    fig, axes = plt.subplots(1,2,figsize=(WIDTH,2.75))
    fig.subplots_adjust(left=.102,right=.985,bottom=.20,top=.84,wspace=.34)
    ax = axes[0]
    ax.axhspan(-6,0,color=BLUE,alpha=.045,zorder=0)
    ax.axhline(0,color=GREY,lw=.75,ls=(0,(4,3)),zorder=1)
    ax.plot(k,temporal,'s--',color=GREY,ms=3.5,lw=1.0,mfc='white',mew=.85,label='Temporal groups',zorder=3)
    ax.plot(k,rank,'o-',color=BLUE,ms=3.4,lw=1.25,label='Rank groups',zorder=4)
    ax.set_ylim(-6,6.2)
    ax.set_yticks([-5,0,5])
    ax.set_ylabel('Upper bound − $H_0$ (MWh)')
    ax.legend(loc='upper right',bbox_to_anchor=(1.02,.985),borderaxespad=0,handlelength=1.55,fontsize=6.8)
    ax.annotate('Gain excluded',xy=(20,-3.7),color=BLUE,fontsize=7,ha='center')
    panel(ax,'a','Screening decision',x=-.20)
    ax = axes[1]
    ax.plot(k,total,'s--',color=GREY,ms=3.5,lw=1.0,mfc='white',mew=.85,label='Sort + summary + query',zorder=3)
    ax.plot(k,query,'o-',color=BLUE,ms=3.4,lw=1.25,label='Query only',zorder=4)
    ax.set_yscale('log')
    ax.set_ylim(.015,4)
    ax.set_yticks([.02,.1,1])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v,p:f'{v:g}'))
    ax.yaxis.set_minor_locator(NullLocator())
    ax.set_ylabel('Recorded wall time (s)')
    ax.legend(loc='upper left',bbox_to_anchor=(-.025,1.01),borderaxespad=0,handlelength=1.55,fontsize=6.6)
    panel(ax,'b','Summary cost',x=-.20)
    for ax in axes:
        ax.set_xscale('log')
        ax.set_xlim(.8,1100)
        ax.set_xticks(k, [str(v) for v in k])
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_xlabel('Groups per 15-min interval',labelpad=5)
        clean(ax)
    save(fig,'distribution_screen')
    return {'reference_mwh':h0,'groups':k.tolist(),'rank_upper_mwh':[r['upper_mwh'] for r in rows],
            'temporal_upper_mwh':[r['temporal_upper_mwh'] for r in rows],
            'three_group_rank_upper_mwh':rows[1]['upper_mwh'],
            'timings':'saved measurements; not rerun'}

def energy():
    source = read('energy')
    eta_rows = sorted([r for r in source if r['amplitude']==1], key=lambda r:r['eta'])
    amplitude_rows = sorted([r for r in source if r['eta']==.94], key=lambda r:r['amplitude'])
    fig, axes = plt.subplots(1,2,figsize=(WIDTH,2.92),sharey=True)
    fig.subplots_adjust(left=.104,right=.985,bottom=.27,top=.835,wspace=.20)
    for ax,rows,key,offset,cap,padding in [
        (axes[0],eta_rows,'eta',.0025,.0017,.012),
        (axes[1],amplitude_rows,'amplitude',.018,.014,.08),
    ]:
        for row in rows:
            x=row[key]
            h0=row['no_reserve_mwh']
            bracket(ax,x,row['native_feasible_input_mwh']-h0,row['upper_mwh']-h0,offset=-offset,cap=cap)
            ax.plot(x+offset,row['quarter_optimum_mwh']-h0,marker='D',color=ORANGE,ms=4,ls='none',mew=0,zorder=5)
        ax.axhline(0,color=GREY,lw=.8,ls=(0,(4,3)),zorder=1)
        ax.set_xlim(rows[0][key]-padding,rows[-1][key]+padding)
        ax.set_ylim(-35,20)
        ax.set_yticks([-30,-20,-10,0,10,20])
        clean(ax)
    axes[0].set_ylabel('Input change from $H_0$ (MWh)')
    axes[0].set_xticks([r['eta'] for r in eta_rows],[f'{r["eta"]:.2f}' for r in eta_rows])
    axes[0].set_xlabel(r'One-way efficiency, $\eta$',labelpad=5)
    axes[1].set_xticks([r['amplitude'] for r in amplitude_rows],[f'{r["amplitude"]:.1f}' for r in amplitude_rows])
    axes[1].set_xlabel('Activation multiplier',labelpad=5)
    panel(axes[0],'a','Efficiency sensitivity',x=-.205)
    panel(axes[1],'b','Activation sensitivity',x=-.08)
    axes[0].text(.985,.07,'Unit activation multiplier',transform=axes[0].transAxes,
                 ha='right',va='bottom',fontsize=6.7,color=GREY)
    axes[1].text(.985,.07,r'$\eta=0.94$',transform=axes[1].transAxes,
                 ha='right',va='bottom',fontsize=7,color=GREY)
    optimization_legend(fig,y=.025)
    save(fig,'energy_challenge')
    return {'conditions':len(source),'eta_values':[r['eta'] for r in eta_rows],
            'activation_values':[r['amplitude'] for r in amplitude_rows],
            'interval_kind':'optimization bounds, not confidence intervals',
            'reference_mwh':source[0]['no_reserve_mwh']}

def resolution():
    scales=sorted(read('resolution'),key=lambda r:r['scale_seconds'])
    months=sorted(read('monthly'),key=lambda r:r['month'])
    fig,axes=plt.subplots(1,2,figsize=(WIDTH,3.05))
    fig.subplots_adjust(left=.103,right=.985,bottom=.27,top=.84,wspace=.37)
    ax=axes[0]
    for i,row in enumerate(scales):
        lo=row['lower_mwh']-row['no_reserve_mwh']
        hi=row['reported_upper_mwh']-row['no_reserve_mwh']
        if row['scale_seconds']==900:
            ax.plot(i,lo,marker='D',color=ORANGE,ms=4,ls='none',mew=0,zorder=5)
        else:
            bracket(ax,i,lo,hi,cap=.11)
    ax.set_xticks(range(len(scales)),['1 s','5 s','15 s','30 s','1 min','3 min','5 min','15 min'],rotation=45,ha='right')
    ax.set_xlim(-.5,7.5)
    ax.set_ylim(-14,6)
    ax.set_yticks([-10,-5,0,5])
    ax.set_xlabel('Activation averaging scale',labelpad=4)
    ax.set_ylabel('Input change from $H_0$ (MWh)')
    panel(ax,'a','Full evaluation period',x=-.20)
    ax=axes[1]
    for i,row in enumerate(months):
        h0=row['no_reserve_mwh']
        bracket(ax,i,row['native_lower_mwh']-h0,row['native_upper_mwh']-h0,offset=-.14,cap=.11)
        ax.plot(i+.14,row['quarter_optimum_mwh']-h0,marker='D',color=ORANGE,ms=3.6,ls='none',mew=0,zorder=5)
    ax.set_xticks(range(len(months)),['Jan','Feb','Mar','Apr','May','Jun','Jul'],rotation=45,ha='right')
    ax.set_xlim(-.5,6.5)
    ax.set_ylim(-35,26)
    ax.set_yticks([-30,-15,0,15])
    ax.set_xlabel('Separate cyclic month in 2026',labelpad=4)
    ax.set_ylabel('Input change from $H_0$ (MWh)')
    panel(ax,'b','Operating horizon',x=-.22)
    for ax in axes:
        ax.axhline(0,color=GREY,lw=.8,ls=(0,(4,3)),zorder=1)
        clean(ax)
    optimization_legend(fig,y=.025)
    save(fig,'resolution_horizon')
    return {'scales_seconds':[r['scale_seconds'] for r in scales],
            'months':[r['month'] for r in months],
            'exact_900s_mwh':scales[-1]['lower_mwh'],
            'monthly_h0_mwh':[r['no_reserve_mwh'] for r in months],
            'interval_kind':'optimization bounds, not confidence intervals'}

if __name__=='__main__':
    # The main distribution figure is superseded by plot_revision.py.
    checks={'energy_challenge':energy(),'resolution_horizon':resolution()}
    (HERE/'comparison_numeric_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    print(json.dumps(checks,indent=2))
