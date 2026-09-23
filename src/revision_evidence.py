"""Build the additional, traceable evidence for the revision-2 manuscript.

This script writes derived outputs under the repository root. It reads prepared,
source-dependent input caches reconstructed outside the public release. No raw
source record is modified or redistributed.

The endpoint lower side of each selected compression enclosure is a *primal*
endpoint-mixture witness.  A common clipped baseline shift enforces cyclic
inventory exactly in the endpoint model.  This is deliberately different from
the scalar dual search used for the mean-side upper bound: an incomplete dual
search can only be used safely on the upper side.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch
import numpy as np
import scipy


REVISION_ROOT = Path(__file__).resolve().parents[1]
FIGURES = REVISION_ROOT / "figures"
RESULTS = REVISION_ROOT / "results"
FIGURES.mkdir(exist_ok=True)
RESULTS.mkdir(exist_ok=True)
os.environ.setdefault("NUMBA_CACHE_DIR", str(REVISION_ROOT / "temp_numba"))

INPUT_ROOT = Path(os.environ.get("BATTERY_PAPER_INPUT_ROOT", REVISION_ROOT / "prepared_inputs"))
if not INPUT_ROOT.exists():
    raise FileNotFoundError(
        "Prepared inputs were not found. Place the authorized derived inputs in "
        f"{REVISION_ROOT / 'prepared_inputs'} or set BATTERY_PAPER_INPUT_ROOT. "
        "See REPRODUCE.md for source-provider reconstruction instructions."
    )

CODE = REVISION_ROOT / "src"
if not CODE.exists():
    raise FileNotFoundError(f"Analysis modules were not found: {CODE}")
sys.path.insert(0, str(CODE))
from hydrogen_lp_pilot import optimize  # noqa: E402
from reachability import audit_schedule, reach, reconstruct  # noqa: E402


DELTA_H = 0.25
E_MWH = 2.0
S_MW = 0.1
R_MW = 0.75
OUTWARD_MARGIN_MWH = 1e-6


def _sha256(path: Path) -> str:
    """Return a portable content identifier without exposing a workstation path."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _portable_path(path: Path) -> str:
    """Prefer an archive-relative path; name an explicit environment root otherwise."""
    try:
        return path.relative_to(REVISION_ROOT).as_posix()
    except ValueError:
        return f"$BATTERY_PAPER_INPUT_ROOT/{path.relative_to(INPUT_ROOT).as_posix()}"


def baseline_limits(supply_mw: float = S_MW, reserve_mw: float = R_MW) -> tuple[float, float]:
    return max(reserve_mw - 1.0, supply_mw - 1.0), min(1.0 - reserve_mw, supply_mw)


def _dual_choice(z: np.ndarray, w: np.ndarray, eta: float, lam: float) -> tuple[float, float, np.ndarray]:
    """Evaluate the mean-side scalar dual at one multiplier and retain b."""
    n, _ = z.shape
    bl, bh = baseline_limits()
    cumulative_w = np.cumsum(w, axis=1)
    cumulative_w[:, -1] = 1.0
    cumulative_u = np.cumsum(w * z, axis=1)
    total = cumulative_u[:, -1]
    cumulative_w = np.c_[np.zeros(n), cumulative_w]
    cumulative_u = np.c_[np.zeros(n), cumulative_u]

    fraction = (1.0 / eta - 1.0 / lam) / (1.0 / eta - eta)
    if fraction <= 0.0:
        baseline = np.full(n, bl)
    elif fraction >= 1.0:
        baseline = np.full(n, bh)
    else:
        index = (cumulative_w[:, 1:] >= fraction).argmax(axis=1)
        baseline = np.clip(z[np.arange(n), index], bl, bh)

    count = (z <= baseline[:, None]).sum(axis=1)
    weight = cumulative_w[np.arange(n), count]
    part = cumulative_u[np.arange(n), count]
    increment = DELTA_H * (
        eta * (weight * baseline - part)
        - (total - part - (1.0 - weight) * baseline) / eta
    )
    dual_cost = float(np.sum(baseline * DELTA_H - lam * increment))
    return dual_cost, float(increment.sum()), baseline


def _best_scalar_dual_choice(z: np.ndarray, w: np.ndarray, eta: float) -> tuple[float, float, np.ndarray, float]:
    """Return the best sampled dual value; it is safe only for an H upper bound."""
    if eta == 1.0:
        raise ValueError("Lossless case has an exact identity and bypasses the scalar dual.")
    lo, hi = eta, 1.0 / eta
    candidates: list[tuple[float, float, np.ndarray, float]] = []
    for lam in (lo, hi):
        value, residual, baseline = _dual_choice(z, w, eta, lam)
        candidates.append((value, residual, baseline, lam))
    for _ in range(55):
        lam = (lo + hi) / 2.0
        value, residual, baseline = _dual_choice(z, w, eta, lam)
        candidates.append((value, residual, baseline, lam))
        # Envelope theorem: d/dlambda of this concave dual is -sum(F_q).
        if residual < 0.0:
            lo = lam
        else:
            hi = lam
    return max(candidates, key=lambda item: item[0])


def _increment(z: np.ndarray, w: np.ndarray, baseline: np.ndarray, eta: float) -> np.ndarray:
    """Endpoint or mean model inventory increment at an admissible baseline."""
    charging = np.sum(w * np.maximum(baseline[:, None] - z, 0.0), axis=1)
    discharging = np.sum(w * np.maximum(z - baseline[:, None], 0.0), axis=1)
    return DELTA_H * (eta * charging - discharging / eta)


def _cyclic_common_shift(
    z: np.ndarray, w: np.ndarray, baseline0: np.ndarray, eta: float
) -> tuple[dict[str, float], np.ndarray]:
    """Bracket a cyclic common-shift root and return its conservative high side."""
    bl, bh = baseline_limits()

    def shifted(c: float) -> tuple[float, np.ndarray]:
        baseline = np.clip(baseline0 + c, bl, bh)
        return float(_increment(z, w, baseline, eta).sum()), baseline

    c_lo = bl - float(np.max(baseline0))
    c_hi = bh - float(np.min(baseline0))
    g_lo, _ = shifted(c_lo)
    g_hi, _ = shifted(c_hi)
    if not (g_lo <= 1e-12 and g_hi >= -1e-12):
        raise RuntimeError(f"Endpoint cyclic root not bracketed: {g_lo}, {g_hi}")
    for _ in range(62):
        mid = (c_lo + c_hi) / 2.0
        g_mid, _ = shifted(mid)
        if g_mid < 0.0:
            c_lo = mid
        else:
            c_hi = mid
    lower_residual, _ = shifted(c_lo)
    upper_residual, baseline = shifted(c_hi)
    return {
        "lower_shift_mw": c_lo,
        "upper_shift_mw": c_hi,
        "lower_residual_mwh": lower_residual,
        "upper_residual_mwh": upper_residual,
        "bracket_width_mw": c_hi - c_lo,
    }, baseline


def primal_endpoint_lower(z: np.ndarray, w: np.ndarray, eta: float) -> tuple[dict[str, float], np.ndarray]:
    """Construct a cyclic endpoint-mixture witness, hence a valid lower side.

    A clipped common shift is monotone in total endpoint-model inventory.  The
    returned high bisection side is conservative: its cost is never smaller
    than the exact-root cost, even if the final floating-point residual is not
    exactly zero. The returned anchor permits an explicit native-root audit.
    """
    dual_cost, initial_residual, baseline0, multiplier = _best_scalar_dual_choice(z, w, eta)
    root, baseline = _cyclic_common_shift(z, w, baseline0, eta)
    h_lower = float(S_MW * len(z) * DELTA_H - baseline.sum() * DELTA_H - OUTWARD_MARGIN_MWH)
    return {
        "lower_relaxed_mwh": h_lower,
        "endpoint_dual_value_mwh": float(S_MW * len(z) * DELTA_H - dual_cost),
        "endpoint_initial_inventory_residual_mwh": initial_residual,
        "endpoint_repair_shift_mw": root["upper_shift_mw"],
        "endpoint_repair_inventory_residual_mwh": root["upper_residual_mwh"],
        "endpoint_root_lower_shift_mw": root["lower_shift_mw"],
        "endpoint_root_lower_residual_mwh": root["lower_residual_mwh"],
        "endpoint_root_bracket_width_mw": root["bracket_width_mw"],
        "endpoint_minimum_baseline_mw": float(baseline.min()),
        "endpoint_maximum_baseline_mw": float(baseline.max()),
        "endpoint_multiplier": multiplier,
    }, baseline0


def conservative_enclosure(sorted_u: np.ndarray, k: int, eta: float) -> dict[str, float]:
    """Numerical primal--dual enclosure for the selected rank-group summary."""
    n, m = sorted_u.shape
    if m % k:
        raise ValueError("Group count must divide the 900 samples in a quarter.")
    groups = sorted_u.reshape(n, k, m // k)
    mean = groups.mean(axis=2)
    low = groups[:, :, 0]
    high = groups[:, :, -1]
    theta = np.divide(high - mean, high - low, out=np.ones_like(mean), where=high > low)
    theta = np.clip(theta, 0.0, 1.0)
    endpoints = np.stack([low, high], axis=2).reshape(n, 2 * k)
    endpoint_weights = np.stack([theta, 1.0 - theta], axis=2).reshape(n, 2 * k) / k

    if eta == 1.0:
        exact_h = float(S_MW * n * DELTA_H - np.sum(mean) * DELTA_H)
        return {
            "lower_relaxed_mwh": exact_h - OUTWARD_MARGIN_MWH,
            "upper_relaxed_mwh": exact_h + OUTWARD_MARGIN_MWH,
            "gap_mwh": 2.0 * OUTWARD_MARGIN_MWH,
            "summary_values": int(n * k * 3),
            "mean_multiplier": 1.0,
            "mean_inventory_residual_mwh": 0.0,
            "endpoint_repair_shift_mw": 0.0,
            "endpoint_repair_inventory_residual_mwh": 0.0,
        }

    mean_weights = np.full_like(mean, 1.0 / k)
    mean_dual, mean_residual, _, mean_multiplier = _best_scalar_dual_choice(mean, mean_weights, eta)
    upper = float(S_MW * n * DELTA_H - mean_dual + OUTWARD_MARGIN_MWH)
    lower, anchor = primal_endpoint_lower(endpoints, endpoint_weights, eta)
    native_weights = np.full_like(sorted_u, 1.0 / m)
    native_root, _ = _cyclic_common_shift(sorted_u, native_weights, anchor, eta)
    if native_root["upper_shift_mw"] > lower["endpoint_repair_shift_mw"] + 1e-12:
        raise RuntimeError("Native cyclic root is unexpectedly above the endpoint cyclic root.")
    lower.update(
        native_root_lower_shift_mw=native_root["lower_shift_mw"],
        native_root_upper_shift_mw=native_root["upper_shift_mw"],
        native_root_lower_residual_mwh=native_root["lower_residual_mwh"],
        native_root_upper_residual_mwh=native_root["upper_residual_mwh"],
        native_root_bracket_width_mw=native_root["bracket_width_mw"],
        native_root_offset_from_endpoint_mw=native_root["upper_shift_mw"] - lower["endpoint_repair_shift_mw"],
    )
    if lower["lower_relaxed_mwh"] > upper + 1e-8:
        raise RuntimeError("Primal lower side exceeds the dual upper side.")
    return {
        **lower,
        "upper_relaxed_mwh": upper,
        "gap_mwh": upper - lower["lower_relaxed_mwh"],
        "summary_values": int(n * k * 3),
        "mean_multiplier": mean_multiplier,
        "mean_inventory_residual_mwh": mean_residual,
    }


def _month_ranges() -> dict[str, tuple[int, int]]:
    rows = json.loads((INPUT_ROOT / "monthly_energy_results.json").read_text(encoding="utf-8"))
    offset = 0
    ranges: dict[str, tuple[int, int]] = {}
    for row in rows:
        length = round(float(row["hours"]) * 3600.0)
        ranges[row["month"]] = (offset, offset + length)
        offset += length
    return ranges


def selected_enclosures(base: np.ndarray) -> list[dict[str, object]]:
    """Recompute the exact stopping-rule cases with correct-direction endpoints."""
    month_ranges = _month_ranges()
    selections = [("full", 0, len(base), 0.94, 1.0, 9)]
    for month, (start, end) in month_ranges.items():
        selections.append((month, start, end, 0.94, 1.0, 9))
    selections.extend(
        [
            ("eta0.9_amp1.0", 0, len(base), 0.90, 1.0, 9),
            ("eta0.98_amp1.0", 0, len(base), 0.98, 1.0, 3),
            ("eta1.0_amp1.0", 0, len(base), 1.00, 1.0, 1),
            ("eta0.94_amp0.8", 0, len(base), 0.94, 0.8, 9),
            ("eta0.94_amp1.2", 0, len(base), 0.94, 1.2, 9),
        ]
    )
    out: list[dict[str, object]] = []
    for case, start, end, eta, amplitude, k in selections:
        native = np.clip(np.asarray(base[start:end]) * amplitude, -1.0, 1.0)
        sorted_u = np.sort(R_MW * native.reshape(-1, 900), axis=1)
        started = time.perf_counter()
        row: dict[str, object] = conservative_enclosure(sorted_u, k, eta)
        row.update(
            case=case,
            source="German aFRR",
            k=k,
            eta=eta,
            amplitude=amplitude,
            hours=(end - start) / 3600.0,
            width_kw=1000.0 * float(row["gap_mwh"]) / ((end - start) / 3600.0),
            seconds=time.perf_counter() - started,
        )
        out.append(row)
        print(f"German enclosure: {case}, K={k}, width={row['width_kw']:.6g} kW", flush=True)

    for file in sorted((INPUT_ROOT / "gb_frequency").glob("2026-*.npz")):
        activation = np.load(file)["activation"]
        sorted_u = np.sort(R_MW * activation, axis=1)
        started = time.perf_counter()
        row = conservative_enclosure(sorted_u, 45, 0.94)
        row.update(
            case=file.stem,
            source="Great Britain frequency transformation",
            k=45,
            eta=0.94,
            amplitude=1.0,
            hours=len(sorted_u) * DELTA_H,
            width_kw=1000.0 * float(row["gap_mwh"]) / (len(sorted_u) * DELTA_H),
            seconds=time.perf_counter() - started,
        )
        out.append(row)
        print(f"GB enclosure: {file.stem}, K=45, width={row['width_kw']:.6g} kW", flush=True)
    return out


def decision_grid(base: np.ndarray) -> list[dict[str, object]]:
    """Run a preregistered-in-script discrete sensitivity grid, not a contour fit."""
    h0 = len(base) / 3600.0 * S_MW
    rows: list[dict[str, object]] = []
    for eta in (0.90, 0.92, 0.94, 0.96, 0.98):
        for amplitude in (0.8, 1.0, 1.2):
            activation = np.clip(np.asarray(base) * amplitude, -1.0, 1.0)
            sorted_u = np.sort(R_MW * activation.reshape(-1, 900), axis=1)
            started = time.perf_counter()
            if eta == 1.0:
                native_upper = float(h0 - np.sum(sorted_u) / 3600.0)
            else:
                mean_weights = np.full_like(sorted_u, 1.0 / 900.0)
                dual_cost, _, _, multiplier = _best_scalar_dual_choice(sorted_u, mean_weights, eta)
                native_upper = float(S_MW * len(sorted_u) * DELTA_H - dual_cost + OUTWARD_MARGIN_MWH)
            reach_result = reach(activation, E_MWH, R_MW, eta, S_MW, 0.0, E_MWH / 2.0, E_MWH / 2.0)
            feasible = bool(reach_result[0] and reach_result[2][-1] - 1e-9 <= E_MWH / 2.0 <= reach_result[3][-1] + 1e-9)
            lower = None
            witness_error = None
            if feasible:
                baselines, _ = reconstruct(activation, E_MWH, R_MW, eta, *reach_result[2:], E_MWH / 2.0)
                audit = audit_schedule(activation, baselines, E_MWH / 2.0, E_MWH, R_MW, eta, S_MW, 0.0)
                witness_error = float(max(audit[-1], abs(audit[0] - E_MWH / 2.0)))
                lower = float(audit[3])
            quarter = optimize(activation.reshape(-1, 900).mean(axis=1), E_MWH, R_MW, S_MW, eta)
            quarter_feasible = bool(quarter["success"])
            quarter_value = float(quarter["hydrogen_input_mwh"]) if quarter_feasible else None
            if not feasible or not quarter_feasible:
                classification = "infeasible"
            elif quarter_value > h0 and native_upper < h0:
                classification = "aggregation_false_positive"
            elif lower is not None and lower > h0:
                classification = "native_gain_verified"
            elif quarter_value <= h0 and native_upper < h0:
                classification = "consistent_loss"
            else:
                classification = "indeterminate"
            row = {
                "eta_one_way": eta,
                "activation_multiplier": amplitude,
                "no_reserve_mwh": h0,
                "quarter_exact_mwh": quarter_value,
                "native_feasible_lower_mwh": lower,
                "native_capacity_free_dual_upper_mwh": native_upper,
                "native_feasible": feasible,
                "quarter_feasible": quarter_feasible,
                "witness_error_mwh": witness_error,
                "classification": classification,
                "seconds": time.perf_counter() - started,
            }
            rows.append(row)
            print(f"Decision grid: eta={eta:.2f}, amp={amplitude:.1f}, {classification}", flush=True)
    return rows


def mechanism_figure(base: np.ndarray) -> dict[str, float]:
    """Create a criterion-selected real 15-minute mechanism illustration."""
    q = 11272
    start, stop = q * 900, (q + 1) * 900
    baseline_record = np.load(INPUT_ROOT / "reference_quarter_solution.npz")
    baseline = float(baseline_record["baseline_mw"][q])
    initial = float(baseline_record["inventory_mwh"][q])
    activation = np.asarray(base[start:stop])
    mean_activation = float(activation.mean())
    power = R_MW * activation - baseline
    inventory = initial + np.r_[0.0, np.cumsum(np.where(power >= 0.0, -power / 0.94, -power * 0.94) / 3600.0)]
    coarse_power = R_MW * mean_activation - baseline
    coarse_increment = 0.25 * (-coarse_power / 0.94 if coarse_power >= 0.0 else -coarse_power * 0.94)

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "pdf.fonttype": 42})
    fig, axes = plt.subplots(3, 1, figsize=(7.0, 5.8), sharex=True)
    seconds = np.arange(900)
    axes[0].plot(seconds, activation, color="#3b6f8f", linewidth=0.75, label="1-s activation")
    axes[0].axhline(mean_activation, color="#b65a56", linestyle="--", linewidth=1.1, label="15-min mean")
    axes[0].set_ylabel("Normalized\nactivation")
    axes[0].legend(loc="upper right", frameon=False, ncol=2, fontsize=7.5)
    axes[0].set_title("Criterion-selected within-quarter discrepancy", loc="left", fontsize=10)
    axes[1].plot(seconds, power, color="#72558b", linewidth=0.75)
    axes[1].axhline(0.0, color="0.35", linewidth=0.7)
    axes[1].axhline(coarse_power, color="#b65a56", linestyle="--", linewidth=1.0)
    axes[1].set_ylabel("Battery power\n(MW; + discharge)")
    axes[2].plot(np.arange(901), inventory, color="#276b50", linewidth=1.1, label="Native replay")
    axes[2].axhline(initial, color="#b65a56", linestyle="--", linewidth=1.0, label="Quarter-mean prediction")
    axes[2].set_ylabel("Inventory\n(MWh)")
    axes[2].set_xlabel("Seconds from 2026-04-28 09:00 UTC")
    axes[2].legend(loc="lower left", frameon=False, fontsize=7.5)
    for axis in axes:
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.grid(axis="y", alpha=0.18)
    fig.tight_layout(h_pad=0.4)
    fig.savefig(FIGURES / "mechanism_time_window.pdf", bbox_inches="tight")
    fig.savefig(FIGURES / "mechanism_time_window.png", dpi=1200, bbox_inches="tight")
    plt.close(fig)
    return {
        "quarter_index_zero_based": q,
        "start_utc": "2026-04-28 09:00:00",
        "mean_activation": mean_activation,
        "quarter_baseline_mw": baseline,
        "initial_inventory_mwh": initial,
        "native_end_inventory_mwh": float(inventory[-1]),
        "native_minimum_inventory_mwh": float(inventory.min()),
        "native_increment_mwh": float(inventory[-1] - initial),
        "quarter_mean_increment_mwh": float(coarse_increment),
        "positive_discharge_seconds": int((power >= 0.0).sum()),
    }


def system_diagram() -> None:
    """Draw an equation-faithful architecture diagram for the main manuscript."""
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "pdf.fonttype": 42})
    fig, ax = plt.subplots(figsize=(7.0, 3.7))
    ax.set_axis_off()

    def box(x: float, y: float, width: float, height: float, text: str, face: str) -> None:
        patch = FancyBboxPatch((x, y), width, height, boxstyle="round,pad=0.015,rounding_size=0.025", linewidth=1.0, edgecolor="#3f4a52", facecolor=face)
        ax.add_patch(patch)
        ax.text(x + width / 2.0, y + height / 2.0, text, ha="center", va="center", wrap=True)

    def arrow(x1: float, y1: float, x2: float, y2: float, label: str, color: str = "#3f4a52") -> None:
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=13, linewidth=1.2, color=color))
        ax.text((x1 + x2) / 2.0, (y1 + y2) / 2.0 + 0.055, label, ha="center", va="bottom", color=color)

    box(0.04, 0.58, 0.19, 0.20, "Scheduled\nsupply $S$", "#dbeaf2")
    box(0.33, 0.54, 0.22, 0.28, "Allocation\nbalance", "#f3edd5")
    box(0.69, 0.58, 0.24, 0.20, "Electrolyzer\nelectrical input $h_q$", "#e4efe4")
    box(0.35, 0.14, 0.23, 0.20, "Battery\n$p_t=Ra_t-b_q$", "#ece3f3")
    box(0.72, 0.14, 0.20, 0.20, "Reserve\nactivation $Ra_t$", "#f3e2e1")
    arrow(0.23, 0.68, 0.33, 0.68, "fixed input")
    arrow(0.55, 0.68, 0.69, 0.68, "$h_q=S-b_q$")
    arrow(0.44, 0.54, 0.47, 0.34, "$b_q$ (recovery)", "#72558b")
    arrow(0.72, 0.24, 0.58, 0.24, "$Ra_t$", "#b65a56")
    ax.text(0.5, 0.91, r"Power balance: $S+p_t=h_q+Ra_t$", ha="center", va="center", fontsize=11, fontweight="bold")
    ax.text(0.5, 0.02, "Negative $b_q$ can draw battery energy to the electrolyzer; downward activation can import additional grid electricity.", ha="center", va="bottom", fontsize=8)
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    fig.tight_layout(pad=0.4)
    fig.savefig(FIGURES / "system_energy_flow.pdf", bbox_inches="tight")
    fig.savefig(FIGURES / "system_energy_flow.png", dpi=1200, bbox_inches="tight")
    plt.close(fig)


def decision_map_figure(rows: list[dict[str, object]]) -> None:
    eta_values = sorted({float(row["eta_one_way"]) for row in rows})
    amplitude_values = sorted({float(row["activation_multiplier"]) for row in rows})
    lookup = {(float(row["eta_one_way"]), float(row["activation_multiplier"])): str(row["classification"]) for row in rows}
    color = {
        "consistent_loss": "#9ea7ad",
        "aggregation_false_positive": "#c65b58",
        "native_gain_verified": "#4d8d69",
        "indeterminate": "#d5aa3d",
        "infeasible": "#4f4f4f",
    }
    label = {
        "consistent_loss": "consistent\nloss",
        "aggregation_false_positive": "aggregation\nfalse positive",
        "native_gain_verified": "native gain\nverified",
        "indeterminate": "indeterminate",
        "infeasible": "infeasible",
    }
    fig, ax = plt.subplots(figsize=(7.1, 3.7))
    for row_index, eta in enumerate(eta_values):
        for col_index, amplitude in enumerate(amplitude_values):
            status = lookup[(eta, amplitude)]
            rect = plt.Rectangle((col_index, row_index), 1.0, 1.0, facecolor=color[status], edgecolor="white", linewidth=1.7)
            ax.add_patch(rect)
            ax.text(col_index + 0.5, row_index + 0.5, label[status], ha="center", va="center", color="white" if status != "consistent_loss" else "black", fontsize=8.2, fontweight="bold")
    ax.set_xlim(0, len(amplitude_values))
    ax.set_ylim(0, len(eta_values))
    ax.set_xticks(np.arange(len(amplitude_values)) + 0.5, [f"{value:.1f}" for value in amplitude_values])
    ax.set_yticks(np.arange(len(eta_values)) + 0.5, [f"{value:.2f}" for value in eta_values])
    ax.set_xlabel("Activation multiplier")
    ax.set_ylabel("One-way efficiency")
    ax.set_title("Discrete sign-decision grid ($E=2$ MWh, $S=0.1$ MW, $R=0.75$ MW)", loc="left", fontsize=10)
    ax.spines[:].set_visible(False)
    legend = [
        Patch(color=color["aggregation_false_positive"], label="Quarter gain; native dual upper below $H_0$"),
        Patch(color=color["native_gain_verified"], label="Native feasible lower above $H_0$"),
        Patch(color=color["consistent_loss"], label="Both representations below $H_0$"),
        Patch(color=color["infeasible"], label="At least one cyclic problem infeasible"),
    ]
    ax.legend(handles=legend, loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2, frameon=False, fontsize=7.5)
    fig.subplots_adjust(bottom=0.31, left=0.13, right=0.98, top=0.86)
    fig.savefig(FIGURES / "parameter_decision_grid.pdf", bbox_inches="tight")
    fig.savefig(FIGURES / "parameter_decision_grid.png", dpi=1200, bbox_inches="tight")
    plt.close(fig)


def write_csv(rows: list[dict[str, object]], path: Path) -> None:
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    base_path = INPUT_ROOT / "native_evaluation.npy"
    base = np.load(base_path, mmap_mode="r")
    if len(base) != 18_313_200:
        raise RuntimeError(f"Unexpected native sample count: {len(base)}")
    system_diagram()
    mechanism = mechanism_figure(base)
    enclosures = selected_enclosures(base)
    grid = decision_grid(base)
    decision_map_figure(grid)
    write_csv(grid, RESULTS / "parameter_decision_grid.csv")
    manifest = {
        "status": "PASS",
        "input": {
            "native_evaluation_path": _portable_path(base_path),
            "native_evaluation_sha256": _sha256(base_path),
            "native_samples": int(len(base)),
            "quarters": int(len(base) // 900),
            "reference_quarter_solution": _portable_path(INPUT_ROOT / "reference_quarter_solution.npz"),
            "monthly_result_table": _portable_path(INPUT_ROOT / "monthly_energy_results.json"),
            "gb_frequency_directory": _portable_path(INPUT_ROOT / "gb_frequency"),
        },
        "method": {
            "endpoint_lower": "Cyclic primal endpoint-mixture witness after a common clipped baseline shift.",
            "mean_upper": "Evaluated scalar dual bound at the best stored multiplier; valid even without an exact dual maximizer.",
            "outward_margin_mwh": OUTWARD_MARGIN_MWH,
        },
        "mechanism_window": mechanism,
        "selected_primal_dual_enclosures": enclosures,
        "decision_grid": grid,
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "matplotlib": matplotlib.__version__,
        },
    }
    (RESULTS / "revision_evidence_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Revision evidence outputs written.", flush=True)


if __name__ == "__main__":
    main()
