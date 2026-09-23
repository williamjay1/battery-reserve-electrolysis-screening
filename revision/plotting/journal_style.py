"""Shared, final-size figure style based on SciencePlots 2.2.2.

The community `nature` style is a starting point, not publisher endorsement.
All figures are designed at the 138.6 mm MDPI text-column width.
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import scienceplots  # registers styles

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Definitions' / 'figures'
OUT.mkdir(parents=True, exist_ok=True)
(ROOT / 'qa').mkdir(exist_ok=True)
WIDTH = 138.6 / 25.4
BLUE = '#0072B2'
ORANGE = '#D55E00'
TEAL = '#009E73'
PURPLE = '#8055A0'
INK = '#202830'
GREY = '#737B83'
PALE = '#F3F5F7'
GRID = '#E1E5E9'

plt.style.use(['science', 'nature', 'no-latex'])
plt.rcParams.update({
    'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'font.size': 8, 'axes.labelsize': 8, 'axes.titlesize': 9,
    'xtick.labelsize': 7, 'ytick.labelsize': 7,
    'legend.fontsize': 7, 'legend.frameon': False,
    'axes.linewidth': 0.6, 'lines.linewidth': 1.1,
    'axes.edgecolor': INK, 'axes.labelcolor': INK, 'text.color': INK,
    'xtick.color': INK, 'ytick.color': INK,
    'xtick.direction': 'out', 'ytick.direction': 'out',
    'xtick.top': False, 'ytick.right': False,
    'xtick.minor.visible': False, 'ytick.minor.visible': False,
    'xtick.major.size': 3, 'ytick.major.size': 3,
    'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': False, 'figure.facecolor': 'white',
    'savefig.facecolor': 'white', 'pdf.fonttype': 42, 'ps.fonttype': 42,
    'svg.fonttype': 'none', 'mathtext.fontset': 'dejavusans',
    'savefig.bbox': None, 'savefig.pad_inches': 0,
})

def panel(ax, letter, title=None, x=-0.16, y=1.07):
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=10,
            fontweight='bold', ha='left', va='bottom')
    if title:
        ax.set_title(title, loc='left', pad=9, fontweight='normal')

def clean(ax, grid='y'):
    ax.spines[['top', 'right']].set_visible(False)
    if grid:
        ax.grid(axis=grid, color=GRID, linewidth=0.45, zorder=0)
    ax.set_axisbelow(True)

def save(fig, name):
    """Export editable vector PDF/SVG and a true 900-dpi bitmap."""
    fig.savefig(OUT / f'{name}.pdf')
    fig.savefig(OUT / f'{name}.svg')
    fig.savefig(OUT / f'{name}_900dpi.png', dpi=900)
    fig.savefig(ROOT / 'qa' / f'{name}.png', dpi=160)
    plt.close(fig)
