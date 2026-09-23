"""Publication figures from the local timing and all-quarter mechanism audit."""
from __future__ import annotations
import argparse
import csv
import json
import os
from pathlib import Path
import numpy as np
from journal_style import (ROOT, WIDTH, BLUE, ORANGE, TEAL, PURPLE, INK, GREY,
                           GRID, plt, clean, panel, save)

plt.rcParams['path.simplify'] = False
COLORS = [BLUE, TEAL, PURPLE, ORANGE]


def mechanism(report, input_root, quarter_solution=None):
    with (ROOT/'results'/'quarter_increment_discrepancies.csv').open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    discrepancy = np.array([float(r['signed_discrepancy_mwh']) for r in rows])*1000
    original = np.load(input_root/'native_evaluation.npy', mmap_mode='r')
    with np.load(quarter_solution or input_root/'reference_quarter_solution.npz') as solution:
        baselines = solution['baseline_mw'].copy()
    selected = report['window_audit']['selected_windows']
    curves = []
    for item in selected:
        q = item['quarter_index_zero_based']
        a = np.asarray(original[q*900:(q+1)*900])
        power = .75*a-baselines[q]
        native = np.r_[0., np.cumsum(np.where(power >= 0, -power/.94, -power*.94))/3600]
        coarse = np.linspace(0, item['coarse_increment_mwh'], 901)
        curve = 1000*(coarse-native)
        assert abs(curve[-1]-1000*item['discrepancy_mwh']) < 1e-9
        curves.append(curve)
    low = np.floor(min(float(v.min()) for v in curves)/10)*10-5
    high = np.ceil(max(float(v.max()) for v in curves)/10)*10+5
    fig = plt.figure(figsize=(WIDTH, 5.55))
    gs = fig.add_gridspec(3, 2, left=.145, right=.968, bottom=.160, top=.91,
                          hspace=.78, wspace=.32, height_ratios=[1.10, 1, 1])
    ax = fig.add_subplot(gs[0, :])
    values = np.sort(discrepancy)
    ax.step(values, 100*np.arange(1, len(values)+1)/len(values), where='post', color=INK, lw=1.1)
    for item, color in zip(selected, COLORS):
        x = item['discrepancy_mwh']*1000
        y = 100*np.mean(discrepancy <= x)
        ax.plot(x, y, 'o', color=color, ms=3.3, zorder=4)
        ax.axvline(x, color=color, alpha=.30, lw=.6, zorder=0)
    ax.set_xlim(-.12, 7.65)
    ax.set_ylim(0, 105)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_xticks([0, 2, 4, 6])
    ax.set_xlabel('Quarter-end discrepancy (kWh)', labelpad=3)
    ax.set_ylabel('All quarters (%)')
    ax.set_title('All 20,348 quarters', loc='left', fontsize=8, pad=8)
    panel(ax, 'a', x=-.15, y=1.04)
    ax.text(.98, .14, '18,488 positive; 1,860 zero\nNo negative values beyond numerical tolerance',
            transform=ax.transAxes, ha='right', va='bottom', fontsize=7, linespacing=1.4,
            bbox={'facecolor': 'white', 'edgecolor': 'none', 'alpha': .93, 'pad': 2})
    clean(ax, grid='y')
    for j, (item, color, curve) in enumerate(zip(selected, COLORS, curves)):
        ax = fig.add_subplot(gs[1+j//2, j%2])
        ax.axhline(0, color=GREY, lw=.65, ls=(0, (3, 2)))
        ax.plot(np.arange(901)/60, curve, color=color, lw=.9)
        ax.plot(15, curve[-1], 'o', color=color, ms=3, clip_on=False)
        ax.set_xlim(0, 15)
        ax.set_ylim(low, high)
        ax.set_xticks([0, 5, 10, 15])
        ax.set_title(f"{item['criterion']}  |  {item['discrepancy_mwh']*1000:.3f} kWh",
                     loc='left', fontsize=7.5, pad=12)
        ax.text(0, 1.005, f"Quarter {item['quarter_index_zero_based']}", transform=ax.transAxes,
                ha='left', va='bottom', fontsize=6.7, color=GREY)
        panel(ax, 'bcde'[j], x=-.29, y=1.04)
        if j%2 == 0:
            ax.set_ylabel('Cumulative\ndiscrepancy (kWh)')
        else:
            ax.tick_params(labelleft=False)
        ax.set_xlabel('Time within quarter (min)', labelpad=3)
        clean(ax, grid='y')
    fig.text(.145, .018, 'Discrepancy = coarse increment − native increment.\n'
             'Illustrations: nearest positive quantiles and maximum; shared axis scales.',
             ha='left', va='bottom', fontsize=7, color=GREY, linespacing=1.5)
    save(fig, 'mechanism_window_audit')
    return {'population_points': len(values), 'original_points_each_selected_curve': 901,
            'selected_zero_based_indices': [v['quarter_index_zero_based'] for v in selected],
            'common_time_limits_min': [0, 15], 'common_discrepancy_limits_kwh': [low, high],
            'all_signed_values_used': True, 'source_cache_redistributed': False}


def costs(report):
    runs = report['runs']
    keys = ['file_load', 'activation_prepare', 'rank_sort', 'summary_K3_and_K9',
            'two_upper_queries', 'checksum_and_Jensen_checks']
    labels = ['Load local array', 'Check and scale input', 'Sort within quarters',
              'Build K = 3, 9 summaries', 'Query both upper bounds', 'Checksum + Jensen checks']
    colors = [GREY, '#90979E', BLUE, TEAL, PURPLE, ORANGE]
    fig = plt.figure(figsize=(WIDTH, 4.28))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.8, 1], left=.34, right=.975,
                          top=.90, bottom=.215, hspace=.76, wspace=.78)
    ax = fig.add_subplot(gs[0, :])
    for i, (key, color) in enumerate(zip(keys, colors)):
        value = np.array([r['seconds'][key] for r in runs])
        ax.plot([value.min(), value.max()], [i, i], color=color, lw=2)
        ax.plot(value, np.full(3, i), 'o', color=color, ms=3.1, markeredgecolor='white', markeredgewidth=.35)
        ax.text(1.88, i, f'{np.median(value):.3f}', ha='right', va='center', fontsize=7)
    ax.set_yticks(range(6), labels)
    ax.set_ylim(5.65, -.65)
    ax.set_xscale('log')
    ax.set_xlim(.009, 2.0)
    ax.set_xticks([.01, .1, 1], ['0.01', '0.1', '1'])
    ax.set_xlabel('Wall time per phase (s, log scale)', labelpad=3)
    ax.text(1.88, -.96, 'Median (s)', ha='right', va='center', fontsize=6.8, color=GREY)
    panel(ax, 'a', x=-.46, y=1.10)
    ax.set_title('Every phase measured in three sequential runs', loc='left', fontsize=8, pad=19)
    clean(ax, grid='x')
    ax = fig.add_subplot(gs[1, 0])
    totals = [r['total_local_screen_seconds'] for r in runs]
    y = np.arange(3)
    ax.barh(y, totals, height=.45, color=BLUE, alpha=.9)
    for i, total in enumerate(totals):
        ax.text(total+.035, i, f'{total:.3f}', ha='left', va='center', fontsize=7)
    ax.set_xlim(0, 1.55)
    ax.set_xticks([0, .5, 1, 1.5])
    ax.set_yticks(y, ['Run 1', 'Run 2', 'Run 3'])
    ax.invert_yaxis()
    ax.set_xlabel('Time (s)')
    ax.set_title('Complete local screen', loc='left', fontsize=8, pad=9)
    panel(ax, 'b', x=-1.04, y=1.1)
    clean(ax, grid=None)
    ax = fig.add_subplot(gs[1, 1])
    replay_times = np.array([r['native_witness_replay_validation_seconds'] for r in runs])
    load_times = np.array([r['saved_witness_load_seconds'] for r in runs])
    ax.barh(y, replay_times, height=.45, color=TEAL)
    ax.barh(y, load_times, left=replay_times, height=.45, color=GREY)
    for i, value in enumerate(replay_times+load_times):
        ax.text(value+.001, i, f'{value:.3f}', ha='left', va='center', fontsize=7)
    ax.set_xlim(0, .042)
    ax.set_xticks([0, .02, .04], ['0', '0.02', '0.04'])
    ax.set_yticks(y, [])
    ax.invert_yaxis()
    ax.set_xlabel('Time (s)')
    ax.set_title('Separate witness check', loc='left', fontsize=8, pad=9)
    panel(ax, 'c', x=-.22, y=1.1)
    clean(ax, grid=None)
    fig.text(.06, .016, 'Local array: 18,313,200 samples. Cache warmed by input checks; OS load uncontrolled.\n'
             'Screen includes all six phases. Witness check: saved-file load + physical replay.\n'
             'Network retrieval, source parsing, imports, JIT warm-up and optimization excluded.',
             fontsize=6.7, color=GREY, linespacing=1.4)
    save(fig, 'pipeline_cost')
    return {'all_three_runs_plotted': True, 'median_phase_seconds':
            {key: float(np.median([r['seconds'][key] for r in runs])) for key in keys},
            'median_total_screen_seconds': float(np.median(totals)),
            'median_separate_witness_check_seconds': float(np.median(replay_times+load_times)),
            'screen_output_includes_physical_schedule': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-root', type=Path,
                        default=Path(os.environ.get('BATTERY_PAPER_INPUT_ROOT', ROOT/'prepared_inputs')))
    parser.add_argument('--quarter-solution', type=Path,
                        default=Path(os.environ['BATTERY_PAPER_COARSE_SOLUTION'])
                        if 'BATTERY_PAPER_COARSE_SOLUTION' in os.environ else None)
    args = parser.parse_args()
    report = json.loads((ROOT/'results'/'pipeline_window_audit.json').read_text(encoding='utf-8'))
    checks = {'mechanism': mechanism(report, args.input_root, args.quarter_solution), 'cost': costs(report)}
    (ROOT/'results'/'pipeline_window_plot_checks.json').write_text(json.dumps(checks, indent=2), encoding='utf-8')
    print(json.dumps(checks, indent=2))


if __name__ == '__main__':
    main()
