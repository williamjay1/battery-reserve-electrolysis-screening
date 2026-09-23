"""Final-size revision figures from archived numeric ledgers; no fitted results."""
import json, csv, shutil
from pathlib import Path
import numpy as np
from matplotlib.patches import Rectangle, FancyArrowPatch
from journal_style import *

def read(p): return json.loads(p.read_text(encoding='utf-8'))
DATA=ROOT/'plotting/data'
RES=ROOT/'results/interval_bounds'

def framework():
    fig=plt.figure(figsize=(WIDTH,3.65))
    left=fig.add_axes([.02,.05,.46,.88]); right=fig.add_axes([.53,.05,.45,.88])
    for ax in [left,right]: ax.set(xlim=(0,1),ylim=(0,1)); ax.axis('off')
    def card(ax,x,y,w,h,title,body,color=BLUE):
        ax.add_patch(Rectangle((x,y),w,h,edgecolor=GRID,facecolor=PALE,lw=.65))
        ax.plot([x,x+w],[y+h,y+h],color=color,lw=1.4)
        ax.text(x+.025,y+h-.045,title,fontsize=8,weight='bold',va='top')
        ax.text(x+.025,y+h-.115,body,fontsize=7.4,va='top',linespacing=1.35)
    def arr(ax,a,b): ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=9,lw=.8,color=GREY))
    left.text(0,1.04,'a',weight='bold',fontsize=11); left.text(.09,1.04,'Allocation problem',fontsize=9)
    right.text(0,1.04,'b',weight='bold',fontsize=11);right.text(.09,1.04,'Conservative screen',fontsize=9)
    card(left,0,.75,1,.23,'One native record, matched conditions','Supply, reserve, efficiency and capacity\nSame signed energy and cyclic inventory',INK)
    arr(left,(.24,.75),(.24,.66));arr(left,(.76,.75),(.76,.66))
    card(left,0,.40,.47,.26,'Coarse model','Interval mean\nExact optimum',ORANGE)
    card(left,.53,.40,.47,.26,'Native model','Every second\nFeasible + upper',BLUE)
    arr(left,(.24,.40),(.24,.32));arr(left,(.76,.40),(.76,.32))
    card(left,0,.09,1,.23,r'Compare against no reserve, $H_0$','Coarse gain + native upper below $H_0$\n→ aggregation false positive',INK)
    left.text(0,.015,'Finite-capacity feasibility uses native chronology.',fontsize=7.1,color=GREY)
    card(right,0,.77,1,.21,'1  Summarize each decision interval','Sort native values; retain K rank means')
    arr(right,(.5,.77),(.5,.70))
    card(right,0,.49,1,.21,'2  Evaluate an optimistic upper',r'Nonnegative dual multiplier → $U_K^+$')
    arr(right,(.5,.49),(.5,.42))
    card(right,0,.21,1,.21,'3  Apply the screening rule','$U_K^+ < H_0$: exclude a gain\nOtherwise: inconclusive',TEAL)
    right.text(0,.13,'Optional: endpoints → compression enclosure.',fontsize=7.1)
    right.text(0,.067,'Dispatch or positive gain: native replay required.',fontsize=7.1)
    save(fig,'decision_framework')

def screen():
    rows=[r for r in read(DATA/'comparison_distribution.json') if r['case']=='full']
    enc=read(DATA/'core/revision_evidence_manifest.json')['selected_primal_dual_enclosures']
    fig,axs=plt.subplots(1,2,figsize=(WIDTH,2.8),gridspec_kw={'width_ratios':[1.10,1]})
    fig.subplots_adjust(left=.10,right=.97,bottom=.21,top=.86,wspace=.48)
    ax=axs[0];x=[r['k'] for r in rows]
    ax.plot(x,[r['temporal_upper_mwh'] for r in rows],'^--',color=ORANGE,ms=3.5,label='Time blocks')
    ax.plot(x,[r['upper_mwh'] for r in rows],'o-',color=BLUE,ms=3.5,label='Rank groups')
    ax.axhline(508.7,color=GREY,lw=.8,ls=':');ax.text(5,509.15,'No reserve',color=GREY,fontsize=7)
    ax.set(xscale='log',xlabel='Groups per interval, K',ylabel='Evaluated upper bound (MWh)',ylim=(502.4,514))
    ax.set_xticks([1,3,9,45,225,900],['1','3','9','45','225','900']);clean(ax);ax.legend(loc='upper right',fontsize=6.6)
    panel(ax,'a','Sign exclusion',x=-.27)
    ax=axs[1];de=[e for e in enc if e['source']=='German aFRR'];gb=[e for e in enc if e['source']!='German aFRR']
    for ix,rs,color in [(0,de,BLUE),(1,gb,PURPLE)]:
        offsets=np.linspace(-.12,.12,len(rs))
        ax.scatter(ix+offsets,[e['width_kw'] for e in rs],c=color,s=17,edgecolors='white',linewidths=.4,zorder=3)
    ax.axhline(.1,color=GREY,lw=.8,ls=':');ax.text(.5,.103,'0.1 kW tolerance',ha='center',color=GREY,fontsize=7)
    ax.set(xlim=(-.5,1.5),ylim=(-.003,.115),ylabel='Enclosure width / duration (kW)')
    ax.set_xticks([0,1],['Germany\nK ≤ 9; 13 cases','GB\nK = 45; 7 months'])
    clean(ax);panel(ax,'b','Compression accuracy',x=-.29)
    save(fig,'distribution_screen')

def main():
    lo=read(RES/'guided_witness_900s_round3_policy0.json')['hydrogen_lower_mwh']
    up=read(RES/'upper_900s_round3.json')['hydrogen_upper_mwh']
    h0=508.7
    fig,axs=plt.subplots(1,2,figsize=(WIDTH,3.0),gridspec_kw={'width_ratios':[1,1.05]})
    fig.subplots_adjust(left=.18,right=.96,bottom=.22,top=.83,wspace=.47)
    ax=axs[0]; ax.axvline(0,color=GREY,lw=.8,ls=':')
    ax.hlines(1,496.72539079811526-h0,up-h0,color=GRID,lw=3)
    ax.plot(496.72539079811526-h0,1,'s',mfc='white',mec=GREY,ms=4)
    ax.hlines(1,lo-h0,up-h0,color=BLUE,lw=3);ax.plot(lo-h0,1,'s',color=BLUE,ms=4);ax.plot(up-h0,1,'|',color=BLUE,ms=9)
    ax.plot(512.8566778258428-h0,0,'D',color=ORANGE,ms=4)
    ax.text(-5.89,1.28,f'{lo:.3f}–{up:.3f}',fontsize=7,color=BLUE,ha='center')
    ax.annotate('Earlier witness',xy=(-11.9746,1),xytext=(-11.8,1.55),fontsize=6.6,color=GREY,arrowprops={'arrowstyle':'-','lw':.6,'color':GREY})
    ax.set(yticks=[0,1],yticklabels=['Coarse exact','Native bounds'],ylim=(-.5,1.9),xlim=(-13.3,5.7),xlabel=r'Input minus $H_0$ (MWh)')
    ax.set_xticks([-12,-6,0,6]);clean(ax,'x');panel(ax,'a','15-min reference',x=-.52)
    ax=axs[1];ax.axvline(0,color=GREY,lw=.8,ls=':')
    vals=[]
    for i,step in enumerate([60,300,900]):
        q=read(RES/f'interval_{step}s_quick.json')
        cofile=RES/f'interval_{step}s_coarse_network.json'
        if not cofile.exists():cofile=RES/f'interval_{step}s_coarse.json'
        co=read(cofile)['exact_coarse_mwh']
        lower=max(lo,q['new_reachability_witness']['hydrogen_lower_mwh'])
        for f in RES.glob(f'guided_witness_{step}s_*policy*.json'):
            lower=max(lower,read(f)['hydrogen_lower_mwh'])
        upper=q['capacity_free_upper_mwh'];vals.append(dict(step=step,lower=lower,upper=upper,coarse=co))
        ax.hlines(i,lower-h0,upper-h0,color=BLUE,lw=1.2);ax.plot(lower-h0,i,'s',color=BLUE,ms=4);ax.plot(upper-h0,i,'|',color=BLUE,ms=9);ax.plot(co-h0,i,'D',color=ORANGE,ms=4)
        ax.text(upper-h0,i-.21,f'U: {upper-h0:+.3f}',ha='center',va='top',fontsize=6.5,color=BLUE)
    ax.set(yticks=[0,1,2],yticklabels=['1 min','5 min','15 min'],ylim=(2.6,-.5),xlim=(-7,5.7),xlabel=r'Input minus $H_0$ (MWh)')
    ax.set_xticks([-6,-3,0,3,6]);clean(ax,'x');panel(ax,'b','Baseline decision interval',x=-.34)
    fig.text(.5,.057,'Blue: native lower / upper     Orange diamonds: coarse exact',ha='center',fontsize=7)
    fig.text(.5,.012,r'$H_0$ = 508.700 MWh',ha='center',fontsize=7)
    save(fig,'main_sign_comparison');(ROOT/'results/plot_interval_values.json').write_text(json.dumps(vals,indent=2))

def capacity():
    src=Path(r'D:\MLWork\06\Applied_Sciences_energy_revision_20260923\public_repository\results\hydrogen_matrix.csv')
    dst=DATA/'core/hydrogen_matrix.csv'
    if not dst.exists():shutil.copy2(src,dst)
    rows=list(csv.DictReader(dst.open(encoding='utf-8-sig')))
    caps=[.5,1,2,4,8];sup=[.05,.1,.2];out=[]
    colors={'F':ORANGE,'G':TEAL,'?':'#F0C75E','L':BLUE,'X':'#CBD0D5'}
    fig,axs=plt.subplots(1,2,figsize=(WIDTH,3.2));fig.subplots_adjust(left=.12,right=.97,top=.81,bottom=.22,wspace=.5)
    for ax,source,title in zip(axs,['Germany_seconds','Belgium_quarters'],['Matched German decision','Belgian coarse allocation']):
        for i,e in enumerate(caps):
            for j,s in enumerate(sup):
                r=next(r for r in rows if r['source']==source and float(r['capacity_mwh'])==e and float(r['supply_mw'])==s)
                if r['cyclic_zero_deficit_feasible']=='False':cl='X'
                else:
                    lower=float(r['hydrogen_lower_mwh']);upper=float(r['hydrogen_upper_mwh'])+1e-6;h0=float(r['no_reserve_input_mwh'])
                    if source=='Germany_seconds' and e==2 and s==.1:
                        lower=read(RES/'guided_witness_900s_round3_policy0.json')['hydrogen_lower_mwh'];upper=read(RES/'upper_900s_round3.json')['hydrogen_upper_mwh']
                    cl='G' if lower>h0 else 'L' if upper<h0 else '?'
                    if source=='Germany_seconds' and cl=='L':
                        coarse=next(z for z in rows if z['source']=='Germany_quarters' and float(z['capacity_mwh'])==e and float(z['supply_mw'])==s)
                        if coarse['cyclic_zero_deficit_feasible']=='True' and float(coarse['hydrogen_lower_mwh'])>h0:cl='F'
                out.append(dict(source=source,E=e,S=s,classification=cl))
                ax.add_patch(Rectangle((j-.5,i-.5),1,1,facecolor=colors[cl],edgecolor='white',lw=2))
                ax.text(j,i,cl,ha='center',va='center',fontsize=10,color='white' if cl in ['F','G','L'] else INK,weight='bold')
        ax.set(xlim=(-.5,2.5),ylim=(-.5,4.5),xticks=range(3),xticklabels=sup,yticks=range(5),yticklabels=caps,xlabel='Supply (MW)',ylabel='Capacity (MWh)')
        ax.tick_params(length=0);ax.spines[:].set_visible(False);ax.set_title(title,fontsize=8,pad=10)
    panel(axs[0],'a',x=-.30);panel(axs[1],'b',x=-.30)
    fig.text(.5,.07,'F  False positive    G  Verified gain    L  Gain excluded',ha='center',fontsize=7)
    fig.text(.5,.015,'?  Indeterminate    X  Native / coarse infeasible',ha='center',fontsize=7)
    save(fig,'capacity_supply_map');(ROOT/'results/capacity_supply_classes.json').write_text(json.dumps(out,indent=2))

if __name__=='__main__':
    import sys
    functions={'framework':framework,'screen':screen,'main':main,'capacity':capacity}
    for name in sys.argv[1:] or functions:functions[name]()
