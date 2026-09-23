"""Regenerate the native replay and supplementary diagnostics from frozen results.

Only aggregate tables are copied into plotting/data. The one-second input cache
is opened read-only in its external location and is never redistributed here.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from journal_style import (
    ROOT, WIDTH, BLUE, ORANGE, TEAL, PURPLE, INK, GREY, PALE, GRID,
    plt, clean, panel, save,
)

DATA = ROOT / 'plotting' / 'data'
DATA.mkdir(exist_ok=True)
plt.rcParams['path.simplify'] = False
SOURCES = ['Germany_seconds', 'Germany_quarters', 'Belgium_quarters']
TITLES = ['German native', 'German quarter mean', 'Belgian validated quarter']


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def aggregate_records(source, name):
    """Package only small, already published aggregate plotting inputs."""
    target = DATA / f'{name}.json'
    if target.exists():
        return json.loads(target.read_text(encoding='utf-8'))
    with Path(source).open(encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.DictReader(handle))
    target.write_text(json.dumps(rows, indent=2), encoding='utf-8')
    return rows


def mechanism(input_root):
    q = 11272
    raw_path = input_root / 'native_evaluation.npy'
    quarter_path = input_root / 'reference_quarter_solution.npz'
    native = np.load(raw_path, mmap_mode='r')
    if native.shape != (18_313_200,):
        raise ValueError(f'Unexpected native shape: {native.shape}')
    activation = np.asarray(native[q * 900:(q + 1) * 900])
    with np.load(quarter_path) as stored:
        baseline = float(stored['baseline_mw'][q])
        initial = float(stored['inventory_mwh'][q])
    mean = float(activation.mean())
    power = 0.75 * activation - baseline
    inventory = initial + np.r_[0., np.cumsum(
        np.where(power >= 0., -power / .94, -power * .94) / 3600.)]
    coarse_power = .75 * mean - baseline
    coarse_increment = .25 * (-coarse_power / .94 if coarse_power >= 0. else -coarse_power * .94)
    loss = (initial - inventory[-1]) * 1000
    assert len(activation) == 900 and len(inventory) == 901
    assert abs(loss - 7.343636220582428) < 1e-9
    assert abs(coarse_increment) < 1e-12
    assert abs(inventory.min() - .23197039015131393) < 1e-12

    fig, axes = plt.subplots(3, 1, figsize=(WIDTH, 4.65), sharex=True)
    fig.subplots_adjust(left=.155, right=.968, top=.865, bottom=.105, hspace=.40)
    fig.text(.155, .985, 'Averaging removes within-quarter cycling', ha='left', va='top', fontsize=9)
    fig.text(.155, .953, 'Criterion-selected interval  |  28 April 2026, 09:00 UTC', ha='left', va='top', fontsize=7, color=GREY)
    minutes = np.arange(900) / 60

    ax = axes[0]
    ax.plot(minutes, activation, color=BLUE, linewidth=.8, label='Native, 1 s')
    ax.axhline(mean, color=ORANGE, linestyle=(0, (4, 2)), linewidth=1., label='Quarter mean')
    ax.set_ylabel('Normalized\nactivation')
    panel(ax, 'a', x=-.15, y=.99)
    ax.legend(loc='upper right', ncol=2, fontsize=7, handlelength=2.2, columnspacing=1.1,
              bbox_to_anchor=(1., 1.16), borderaxespad=0)
    ax.set_ylim(-1.08, 1.08)
    ax.set_yticks([-1., 0., 1.])

    ax = axes[1]
    ax.fill_between(minutes, 0, power, where=power >= 0, color=ORANGE, alpha=.12, linewidth=0)
    ax.fill_between(minutes, 0, power, where=power < 0, color=BLUE, alpha=.11, linewidth=0)
    ax.plot(minutes, power, color=BLUE, linewidth=.8)
    ax.axhline(coarse_power, color=ORANGE, linestyle=(0, (4, 2)), linewidth=1.)
    ax.set_ylabel('Battery power\n(MW)')
    panel(ax, 'b', x=-.15, y=.99)
    ax.set_yticks([-.5, 0., .5])
    ax.set_ylim(-.72, .93)
    ax.text(.985, .90, '+ Discharge', transform=ax.transAxes, ha='right', va='top', fontsize=7,
            bbox=dict(facecolor='white', edgecolor='none', alpha=.9, pad=1))
    ax.text(.985, .18, '− Charge', transform=ax.transAxes, ha='right', va='bottom', fontsize=7,
            bbox=dict(facecolor='white', edgecolor='none', alpha=.9, pad=1))

    ax = axes[2]
    ax.plot(np.arange(901) / 60, inventory, color=BLUE, linewidth=1.05)
    ax.axhline(initial, color=ORANGE, linestyle=(0, (4, 2)), linewidth=1.)
    ax.plot(15, inventory[-1], 'o', color=BLUE, markersize=3, clip_on=False)
    ax.set_ylabel('Inventory\n(MWh)')
    ax.set_xlabel('Time from interval start (min)')
    ax.set_ylim(.222, .315)
    ax.set_yticks([.23, .26, .29])
    ax.set_xticks([0, 3, 6, 9, 12, 15])
    panel(ax, 'c', x=-.15, y=.99)
    ax.text(.025, .955, 'Quarter mean: no inventory change', transform=ax.transAxes,
            va='top', fontsize=7)
    ax.annotate(f'Native net loss\n{loss:.3f} kWh', xy=(15, inventory[-1]), xycoords='data',
                xytext=(.985, .05), textcoords='axes fraction', ha='right', va='bottom', fontsize=7,
                arrowprops=dict(arrowstyle='-', color=GREY, linewidth=.65, shrinkA=3, shrinkB=4),
                bbox=dict(facecolor='white', edgecolor='none', alpha=.94, pad=1.2))
    for ax in axes:
        ax.set_xlim(0, 15)
        clean(ax, grid=None)
    for ax, values in zip(axes, [activation, power, inventory]):
        assert ax.get_ylim()[0] < values.min() and ax.get_ylim()[1] > values.max()
    save(fig, 'mechanism_time_window')
    return {
        'quarter_index_zero_based': q, 'start_utc': '2026-04-28 09:00:00',
        'native_samples_plotted': 900, 'inventory_points_plotted': 901,
        'smoothing': False, 'path_simplification': False, 'all_values_inside_axes': True,
        'mean_activation': mean,
        'quarter_baseline_mw': baseline, 'initial_inventory_mwh': initial,
        'native_end_inventory_mwh': float(inventory[-1]),
        'native_minimum_inventory_mwh': float(inventory.min()),
        'native_increment_mwh': float(inventory[-1] - initial),
        'quarter_mean_increment_mwh': coarse_increment,
        'positive_discharge_seconds': int((power >= 0).sum()),
        'source_native_sha256': sha256(raw_path),
        'source_reference_solution_sha256': sha256(quarter_path),
        'source_cache_redistributed': False,
    }


def monthly(rows):
    months = [f'{year}-{month:02}' for year, end in [(2025, 12), (2026, 7)]
              for month in range(1, end + 1)]
    counts = Counter(row['status'] for row in rows)
    assert counts == {'feasible': 162, 'infeasible': 3, 'incomplete_calendar_month': 2}
    styles = [(2, BLUE, 'o'), (4, PURPLE, 's'), (8, TEAL, '^')]
    fig = plt.figure(figsize=(WIDTH, 3.80))
    gs = fig.add_gridspec(4, 1, height_ratios=[1, 1, 1, .18],
                          left=.145, right=.977, top=.93, bottom=.12, hspace=.46)
    axes = [fig.add_subplot(gs[i]) for i in range(3)]
    band = fig.add_subplot(gs[3], sharex=axes[2])
    fig.legend(handles=[Line2D([0], [0], color=c, marker=m, markersize=3, lw=1,
                               label=f'{cap} MWh') for cap, c, m in styles],
               loc='upper right', bbox_to_anchor=(.984, .995), ncol=3,
               handlelength=1.6, columnspacing=1.3)
    plotted = {}
    for ax, source, title, letter in zip(axes, SOURCES, TITLES, 'abc'):
        plotted[source] = {}
        for cap, color, marker in styles:
            lookup = {r['month']: r for r in rows if r['source'] == source and r['capacity_mwh']
                      and float(r['capacity_mwh']) == cap}
            values = np.array([float(lookup[m]['supply_upper_mw'])
                               if m in lookup and lookup[m]['status'] == 'feasible'
                               else np.nan for m in months])
            ax.plot(range(19), values, color=color, marker=marker,
                    markersize=3., markeredgewidth=.6, linewidth=.9)
            plotted[source][str(cap)] = int(np.isfinite(values).sum())
        ax.set_ylim(-.004, .25)
        ax.set_yticks([0., .1, .2])
        ax.set_xlim(-.3, 18.3)
        ax.set_ylabel('Supply (MW)')
        ax.set_xticks(range(19))
        ax.tick_params(axis='x', labelbottom=False, length=2)
        ax.set_title(title, loc='left', fontsize=8, pad=4)
        panel(ax, letter, x=-.15, y=1.055)
        clean(ax, grid=None)
        if source == 'Belgium_quarters':
            for i in [11, 18]:
                ax.axvspan(i-.27, i+.27, facecolor=PALE, edgecolor='none', zorder=0)
    band.set_ylim(0, 1)
    band.set_yticks([])
    band.spines[:].set_visible(False)
    band.set_facecolor(PALE)
    band.set_xlim(-.3, 18.3)
    bad = [months.index(r['month']) for r in rows if r['source'] == 'Belgium_quarters'
           and r['status'] == 'infeasible']
    band.scatter(bad, [.5] * len(bad), color=BLUE, marker='x', s=23, linewidths=1)
    band.text(.01, .5, 'Infeasible (2 MWh)', transform=band.transAxes, ha='left', va='center', fontsize=7)
    ticks = [0, 3, 6, 9, 12, 15, 18]
    labels = ['Jan\n2025', 'Apr', 'Jul', 'Oct', 'Jan\n2026', 'Apr', 'Jul']
    band.set_xticks(ticks, labels)
    band.tick_params(axis='x', length=0, pad=6)
    fig.text(.145, .016, 'Grey bands: incomplete Belgian months; line gaps are retained.', fontsize=7, color=GREY)
    save(fig, 'monthly')
    return {'status_counts': dict(counts), 'feasible_points_plotted': plotted,
            'infeasible_months': [months[i] for i in bad],
            'infeasible_marker_band_not_numeric': True, 'months': months,
            'missing_values_interpolated': False}


def feasibility(rows):
    selected = [r for r in rows if float(r['tau_hours']) == 1.]
    caps = sorted({float(r['capacity_mwh']) for r in selected})
    supplies = sorted({float(r['supply_mw']) for r in selected})
    classes = {
        'causal_success': ('S', '#D8EBF6', BLUE, 'Causal success'),
        'policy_avoidable': ('P', '#F8E0D0', ORANGE, 'Policy-avoidable failure'),
        'physically_infeasible': ('I', '#E4E7EA', GREY, 'Physically infeasible'),
    }
    expected = [[8, 4, 18], [8, 4, 18], [2, 3, 25]]
    fig, axes = plt.subplots(1, 3, figsize=(WIDTH, 2.25), sharey=True)
    fig.subplots_adjust(left=.115, right=.988, top=.76, bottom=.37, wspace=.17)
    summaries = {}
    for ax, source, title, letter, want in zip(axes, SOURCES, TITLES, 'abc', expected):
        source_rows = [r for r in selected if r['source'] == source]
        lookup = {(float(r['capacity_mwh']), float(r['supply_mw'])): r['classification'] for r in source_rows}
        counts = Counter(r['classification'] for r in source_rows)
        assert [counts[c] for c in classes] == want
        assert len(lookup) == 30
        summaries[source] = dict(counts)
        for y, cap in enumerate(caps):
            for x, supply in enumerate(supplies):
                code, fill, edge, _ = classes[lookup[cap, supply]]
                ax.add_patch(Rectangle((x-.46, y-.46), .92, .92,
                                       facecolor=fill, edgecolor='white', linewidth=.4))
                ax.text(x, y, code, ha='center', va='center', fontsize=7, color=INK)
        ax.set_xlim(-.55, len(supplies)-.45)
        ax.set_ylim(-.55, len(caps)-.45)
        ax.set_xticks(range(len(supplies)), [f'{x:g}' for x in supplies], rotation=50, ha='right')
        ax.set_yticks(range(len(caps)), [f'{x:g}' for x in caps])
        ax.tick_params(axis='both', length=0, pad=3, labelsize=6.6)
        ax.spines[:].set_visible(False)
        ax.set_xlabel('Supply (MW)', labelpad=3)
        label = title.replace('Belgian validated quarter', 'Belgian validated\nquarter').replace('German quarter mean', 'German quarter\nmean')
        ax.text(0, 1.48, letter, transform=ax.transAxes, fontsize=10, fontweight='bold', va='top')
        ax.text(.12, 1.48, label, transform=ax.transAxes, fontsize=8, va='top')
        ax.text(.5, 1.035, f'{want[0]} S  ·  {want[1]} P  ·  {want[2]} I',
                transform=ax.transAxes, ha='center', va='bottom', fontsize=6.8, color=GREY)
    axes[0].set_ylabel('Usable capacity (MWh)', labelpad=6)
    for y, (code, fill, edge, label) in zip([.145, .095, .045], classes.values()):
        fig.add_artist(Rectangle((.20, y-.011), .029, .033,
                                transform=fig.transFigure, facecolor=fill, edgecolor='none'))
        fig.text(.2145, y+.005, code, ha='center', va='center', fontsize=7)
        fig.text(.245, y+.005, label, ha='left', va='center', fontsize=7)
    save(fig, 'feasibility')
    return {'feedback_hours': 1, 'configurations_plotted': len(selected),
            'classification_counts': summaries, 'capacity_mwh': caps, 'supply_mw': supplies}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-root', type=Path,
                        default=ROOT / 'prepared_inputs')
    parser.add_argument('--results-root', type=Path,
                        default=ROOT / 'results')
    parser.add_argument('--skip-mechanism', action='store_true', default=True,
                        help='Regenerate the supplementary figures using packaged aggregate JSON only.')
    args = parser.parse_args()
    (ROOT / 'qa').mkdir(exist_ok=True)
    monthly_path = args.results_root / 'monthly_oracle.csv'
    control_path = args.results_root / 'control_classification.csv'
    monthly_rows = aggregate_records(monthly_path, 'monthly_oracle')
    control_rows = aggregate_records(control_path, 'control_classification')
    report = {'mechanism': {'status': 'SKIPPED'} if args.skip_mechanism else mechanism(args.input_root), 'monthly': monthly(monthly_rows),
              'feasibility': feasibility(control_rows),
              'aggregate_sources': {
                  'monthly_oracle.csv': {'sha256': sha256(monthly_path) if monthly_path.exists() else None},
                  'control_classification.csv': {'sha256': sha256(control_path) if control_path.exists() else None},
              }, 'status': 'PASS', 'exports': ['editable PDF', 'editable SVG', '900 dpi PNG']}
    (DATA / 'mechanism_supp_manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
