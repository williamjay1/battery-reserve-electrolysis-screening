"""Redraw the decision framework, physical schematic, main result and grid.

Only saved numerical outputs are read. No optimization is rerun or tuned.
"""
import csv
import json
import hashlib
import shutil
from pathlib import Path
import numpy as np
from matplotlib.patches import Rectangle, FancyArrowPatch
from journal_style import *

DATA = Path(__file__).parent / 'data' / 'core'
DATA.mkdir(parents=True, exist_ok=True)
SOURCE = Path(r'D:\MLWork\06\Applied_Sciences_energy_revision_20260923')
SOURCE_OLD = Path(r'D:\MLWork\06\submission_revision_20260908')
INPUTS = {
    'energy_challenge.json': SOURCE / 'public_repository/results/energy_challenge.json',
    'native_hydrogen_bounds.json': SOURCE / 'public_repository/results/native_hydrogen_bounds.json',
    'finite_capacity_certificate.json': SOURCE / 'public_repository/results/dual_certificate_2.0_0.1_0.94_17_20348.json',
    'revision_evidence_manifest.json': SOURCE / 'revision_results/revision_evidence_manifest.json',
    'parameter_decision_grid.csv': SOURCE / 'revision_results/parameter_decision_grid.csv',
    'distribution_screen.json': SOURCE_OLD / 'results/distribution_screen/results.json',
}

def inputs():
    provenance = []
    for name, source in INPUTS.items():
        target = DATA / name
        if not target.exists():
            shutil.copy2(source, target)
        provenance.append({'file': f'data/core/{name}', 'source': str(source),
                           'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
    (DATA / 'input_provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    read = lambda name: json.loads((DATA / name).read_text(encoding='utf-8'))
    ref = next(r for r in read('energy_challenge.json') if r['eta'] == .94 and r['amplitude'] == 1)
    native = next(r for r in read('native_hydrogen_bounds.json') if r['capacity_mwh'] == 2 and r['supply_mw'] == .1)
    e = next(r for r in read('revision_evidence_manifest.json')['selected_primal_dual_enclosures']
             if r['case'] == 'full' and r['k'] == 9 and r['eta'] == .94 and r['amplitude'] == 1)
    k3 = next(r for r in read('distribution_screen.json') if r['case'] == 'full' and r['k'] == 3)
    result = dict(h0=ref['no_reserve_mwh'], coarse=ref['quarter_optimum_mwh'],
                  lower=native['hydrogen_feasible_lower_mwh'],
                  upper=read('finite_capacity_certificate.json')['hydrogen_upper_mwh'],
                  k3=k3['upper_mwh'], enclosure_lower=e['lower_relaxed_mwh'],
                  enclosure_upper=e['upper_relaxed_mwh'])
    assert result['lower'] < result['upper'] < result['h0'] < result['coarse']
    assert result['k3'] < result['h0']
    assert abs(result['upper'] - 502.97258481639153) < 1e-12
    return result

def arrow(ax, start, end, color=GREY, both=False, **kwargs):
    patch = FancyArrowPatch(start, end, arrowstyle='<->' if both else '-|>',
                            mutation_scale=9, linewidth=.8, color=color,
                            shrinkA=0, shrinkB=0, **kwargs)
    ax.add_patch(patch)

def card(ax, xy, width, height, accent=GREY, fill='white'):
    x, y = xy
    ax.add_patch(Rectangle((x,y),width,height,linewidth=.6,edgecolor=GRID,facecolor=fill))
    ax.plot([x,x+width],[y+height,y+height],color=accent,lw=1.5,solid_capstyle='butt')

def framework(v):
    fig = plt.figure(figsize=(WIDTH,5.20))
    ax = fig.add_axes([.015,.01,.97,.98]); ax.set(xlim=(0,100),ylim=(0,100)); ax.axis('off')
    card(ax,(1,84),98,15,INK,PALE)
    ax.text(4,95.7,'Same activation record and operating conditions',fontsize=9,fontweight='bold')
    ax.text(4,90.8,'One-second driver  •  15-min baseline decisions  •  Fixed supply',fontsize=8)
    ax.text(4,86.5,'Matched signed energy, power limits and cyclic battery inventory',fontsize=7.5)
    arrow(ax,(25,84),(25,79)); arrow(ax,(75,84),(75,79))
    card(ax,(1,58),47,21,ORANGE)
    card(ax,(52,58),47,21,BLUE)
    ax.text(4,74.8,'15-min representation',fontsize=9,fontweight='bold')
    ax.text(55,74.8,'Native representation',fontsize=9,fontweight='bold')
    ax.text(4,69.7,'Exact optimum',fontsize=8)
    ax.text(4,63.2,f"{v['coarse']:.3f} MWh",fontsize=13,fontweight='bold')
    ax.text(55,69.4,'Feasible schedule',fontsize=8)
    ax.text(96,69.4,f"{v['lower']:.3f}",ha='right',fontsize=8)
    ax.text(55,65.0,'Finite-capacity upper',fontsize=8)
    ax.text(96,65.0,f"{v['upper']:.3f}",ha='right',fontsize=8)
    ax.text(55,60.7,'MWh; native optimum lies between',fontsize=7.2)
    arrow(ax,(25,58),(25,53)); arrow(ax,(75,58),(75,53))
    card(ax,(1,43),98,10,INK,PALE)
    ax.text(50,49.7,f"Sign reversal at the no-reserve comparator: {v['h0']:.3f} MWh",
            ha='center',fontsize=8.6,fontweight='bold')
    ax.text(50,45.5,'Quarter optimum above the comparator; native upper bound below it',
            ha='center',fontsize=7.6)
    arrow(ax,(25,43),(25,38)); arrow(ax,(75,43),(75,38))
    card(ax,(1,12),47,26,BLUE)
    card(ax,(52,12),47,26,PURPLE)
    ax.text(4,33.8,'Screen the energy sign',fontsize=8.7,fontweight='bold')
    ax.text(55,33.8,'Bound compression error',fontsize=8.7,fontweight='bold')
    ax.text(4,28.9,'3 rank means per quarter',fontsize=8)
    ax.text(4,23.8,f"Upper bound: {v['k3']:.3f} MWh",fontsize=8)
    ax.text(4,18.9,'Below comparator → reject gain',fontsize=7.5,fontweight='bold')
    ax.text(4,14.6,'300 times fewer summary values',fontsize=7.3)
    ax.text(55,28.9,'9 rank groups per quarter',fontsize=8)
    ax.text(55,23.8,f"{v['enclosure_lower']:.3f}–{v['enclosure_upper']:.3f} MWh",fontsize=9,fontweight='bold')
    ax.text(55,18.9,'Endpoint primal / mean dual',fontsize=7.7)
    ax.text(55,14.6,'Capacity-free numerical enclosure',fontsize=7.3)
    ax.plot([1,99],[8.4,8.4],lw=.6,color=GRID)
    ax.text(1,4.2,'Companion diagnostics',fontsize=7.8,fontweight='bold')
    ax.text(39,4.2,'Recovery supply and controller feasibility (Figs. S1, S2)',fontsize=7.2)
    save(fig,'decision_framework')

def system():
    fig = plt.figure(figsize=(WIDTH,3.22))
    ax = fig.add_axes([.015,.02,.97,.96]); ax.axis('off'); ax.set(xlim=(0,100),ylim=(0,100))
    ax.text(50,94,r'Power balance:  $S+p_t=h_q+Ra_t$',ha='center',fontsize=10)
    # All arrowheads follow the signed power equation. No directional reserve claim is hidden.
    card(ax,(1,47),25,24,GREY)
    ax.text(13.5,61,'Scheduled supply',ha='center',fontsize=8.4,fontweight='bold')
    ax.text(13.5,52.5,r'Fixed $S$',ha='center',fontsize=8)
    card(ax,(37,10),26,24,BLUE)
    ax.text(50,24,'Battery',ha='center',fontsize=8.4,fontweight='bold')
    ax.text(50,15.6,r'$p_t=Ra_t-b_q$',ha='center',fontsize=8)
    card(ax,(74,47),25,24,TEAL)
    ax.text(86.5,61,'Electrolyzer',ha='center',fontsize=8.4,fontweight='bold')
    ax.text(86.5,52.5,'Electrical input',ha='center',fontsize=8)
    ax.plot([31,69],[59,59],color=INK,lw=1.1)
    ax.plot(50,59,'o',ms=3,color=INK)
    arrow(ax,(26,59),(37,59),color=INK)
    arrow(ax,(63,59),(74,59),color=TEAL)
    ax.text(68,65,r'$h_q=S-b_q$',ha='center',fontsize=8)
    arrow(ax,(50,34),(50,57),color=BLUE)
    ax.text(53,43,r'$p_t$',fontsize=9)
    arrow(ax,(50,61),(50,80),color=ORANGE)
    ax.text(50,84,'Reserve exchange with grid',ha='center',fontsize=8.4,fontweight='bold')
    ax.text(53,72,r'$Ra_t$',fontsize=9)
    ax.text(2,1,'Arrows indicate positive power. Negative power reverses the corresponding flow.',fontsize=7.2)
    save(fig,'system_energy_flow')

def sign_comparison(v):
    fig = plt.figure(figsize=(WIDTH,2.95))
    ax = fig.add_axes([.31,.27,.65,.56])
    lo,hi,q = [v[k]-v['h0'] for k in ('lower','upper','coarse')]
    ax.axvline(0,color=GREY,lw=.8,ls=(0,(3,2)))
    ax.plot([lo,hi],[0,0],lw=1.6,color=BLUE)
    ax.plot(lo,0,'s',ms=4.5,color=BLUE)
    ax.plot(hi,0,'|',ms=12,mew=1.4,color=BLUE)
    ax.plot(q,1,'D',ms=5,color=ORANGE)
    ax.text(q,1.20,f"{v['coarse']:.3f} MWh",ha='center',fontsize=8,fontweight='bold')
    ax.text(q,.70,f'+{q:.3f}',ha='center',fontsize=8)
    ax.text(lo,-.23,f"{v['lower']:.3f}\nFeasible",ha='center',va='top',fontsize=7.3,linespacing=1.6)
    ax.text(hi,-.23,f"{v['upper']:.3f}\nUpper bound",ha='center',va='top',fontsize=7.3,linespacing=1.6)
    ax.text((lo+hi)/2,.24,'Native optimum bracket',ha='center',fontsize=7.5)
    ax.set(xlim=(-14,6.5),ylim=(-.8,1.55),xticks=[-12,-8,-4,0,4],yticks=[0,1],
           yticklabels=['Native model','15-min model'])
    ax.tick_params(axis='y',length=0,pad=8,labelsize=8.2)
    ax.spines[['left','top','right']].set_visible(False)
    ax.set_xlabel(r'Change in electrical input, $H-H_0$ (MWh)',labelpad=8)
    fig.text(.04,.94,'Same record, opposite energy signs',fontsize=9,fontweight='bold')
    fig.text(.04,.065,f"No-reserve comparator: {v['h0']:.3f} MWh   •   Equal initial and final inventory",fontsize=7.5)
    save(fig,'main_sign_comparison')

def decision_grid():
    rows = list(csv.DictReader((DATA/'parameter_decision_grid.csv').open(encoding='utf-8')))
    etas = sorted({float(r['eta_one_way']) for r in rows})
    amps = sorted({float(r['activation_multiplier']) for r in rows})
    lookup={(float(r['eta_one_way']),float(r['activation_multiplier'])):r['classification'] for r in rows}
    spec={
        'consistent_loss': ('L', '#D9DFE4', 'Loss in both models'),
        'aggregation_false_positive': ('F', '#F5C6B4', 'Aggregation false positive'),
        'indeterminate': ('?', '#FAE6AD', 'Native sign unresolved'),
        'native_gain_verified': ('G', '#B7DDCC', 'Native gain verified'),
        'infeasible': ('×', '#74808A', 'Cyclic problem infeasible'),
    }
    fig=plt.figure(figsize=(WIDTH,3.35)); ax=fig.add_axes([.13,.19,.45,.65])
    for (eta,amp),status in lookup.items():
        i,j=etas.index(eta),amps.index(amp)
        code,color,_=spec[status]
        ax.add_patch(Rectangle((j-.45,i-.42),.90,.84,facecolor=color,edgecolor='white',lw=.5))
        ax.text(j,i,code,ha='center',va='center',fontsize=12,fontweight='bold',
                color='white' if status=='infeasible' else INK)
    ax.set(xlim=(-.55,2.55),ylim=(-.55,4.55),xticks=range(3),yticks=range(5),
           xticklabels=[f'{a:.1f}' for a in amps],yticklabels=[f'{e:.2f}' for e in etas])
    ax.set_xlabel('Activation multiplier',labelpad=8)
    ax.set_ylabel('One-way efficiency',labelpad=8)
    ax.spines[:].set_visible(False); ax.tick_params(length=0)
    legend_ax=fig.add_axes([.64,.22,.35,.59]); legend_ax.axis('off')
    for i,status in enumerate(['aggregation_false_positive','native_gain_verified','indeterminate','consistent_loss','infeasible']):
        code,color,label=spec[status]; y=.95-i*.195
        legend_ax.add_patch(Rectangle((0,y-.065),.11,.13,facecolor=color,edgecolor='none'))
        legend_ax.text(.055,y,code,ha='center',va='center',fontsize=8,fontweight='bold',color='white' if status=='infeasible' else INK)
        legend_ax.text(.16,y,label,va='center',fontsize=7.4)
    fig.text(.03,.94,'Energy decision across 15 tested conditions',fontsize=9,fontweight='bold')
    fig.text(.13,.035,r'$E=2$ MWh   $S=0.1$ MW   $R=0.75$ MW   •   Discrete cases; no interpolation',fontsize=7.2)
    assert len(rows)==15
    counts={s:sum(r['classification']==s for r in rows) for s in spec}
    assert counts=={'consistent_loss':2,'aggregation_false_positive':5,'indeterminate':3,'native_gain_verified':3,'infeasible':2},counts
    save(fig,'parameter_decision_grid')
    return counts

if __name__=='__main__':
    # Main figures are superseded by plot_revision.py; retain the 15-cell map.
    counts=decision_grid()
    (ROOT/'qa/core_numeric_checks.json').write_text(json.dumps({'status':'PASS','grid_counts':counts},indent=2))
    print('PASS: supplementary 15-cell map')
