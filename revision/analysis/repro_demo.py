"""Source-data-free synthetic reproduction demonstration.

This program is intentionally independent of the German, Belgian, and Great
Britain inputs used by the manuscript.  It generates one small fixed-seed
activation fixture and checks the central mathematical relationships on that
fixture only:

* a finite-capacity native optimum is obtained by exhaustive enumeration of
  the piecewise-linear battery-power sign regions;
* a capacity-free native optimum is independently enumerated;
* evaluated scalar-dual upper bounds from the native values and rank-group
  means bound the capacity-free optimum; and
* an endpoint-mixture cyclic construction gives a primal lower witness for
  the capacity-free native problem.

The code reimplements, rather than imports, the public MIT-licensed model
logic in ``battery-reserve-electrolysis-screening`` so it can be run without
provider data, Numba caches, or repository-specific paths.  It is a software
verification fixture, not an empirical result or a replication of any
reported MWh value.

Run from the manuscript-revision directory:

    python -B analysis/repro_demo.py --write-results

Only ``results/repro_demo_report.json`` and
``results/repro_demo_summary.csv`` are written when ``--write-results`` is
requested.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.optimize import linprog


SEED = 20260923
DELTA_HOURS = 0.25
TOL = 2.0e-8


@dataclass
class ExactResult:
    """A globally enumerated optimum for the deliberately small fixture."""

    hydrogen_mwh: float
    baseline_mw: np.ndarray
    charging_mwh: float
    discharging_mwh: float
    signed_reserve_mwh: float
    maximum_state_violation_mwh: float
    regions_examined: int


def baseline_bounds(supply_mw: float, reserve_mw: float) -> tuple[float, float]:
    """Return the baseline bounds from inverter and load headroom."""

    return max(-(1.0 - reserve_mw), supply_mw - 1.0), min(1.0 - reserve_mw, supply_mw)


def increment_affine(
    u_mw: np.ndarray, baseline_mw: float, eta: float, dt_hours: float
) -> tuple[float, float]:
    """Return f(b)=coefficient*b+intercept inside one fixed sign region."""

    coefficient = 0.0
    intercept = 0.0
    for u in u_mw:
        if baseline_mw >= u:  # charging, p=u-b <= 0
            coefficient += eta * dt_hours
            intercept -= eta * float(u) * dt_hours
        else:  # discharging, p=u-b > 0
            coefficient += dt_hours / eta
            intercept -= float(u) * dt_hours / eta
    return coefficient, intercept


def sign_regions(values_mw: np.ndarray, lower: float, upper: float) -> list[tuple[float, float]]:
    """Enumerate closed baseline intervals on which every sample sign is fixed."""

    cuts = [lower]
    cuts.extend(sorted({float(v) for v in values_mw if lower < v < upper}))
    cuts.append(upper)
    return list(zip(cuts[:-1], cuts[1:]))


def exact_by_enumeration(
    activation: np.ndarray,
    capacity_mwh: float,
    supply_mw: float,
    reserve_mw: float,
    eta: float,
    finite_capacity: bool,
) -> ExactResult:
    """Solve the small native or capacity-free problem by sign-region LPs.

    The fixture is intentionally only three quarters by six samples.  Within a
    baseline sign region the inventory is affine in the quarter baseline, so
    enumeration plus linear programming is globally exact for this fixture.
    """

    activation = np.asarray(activation, dtype=float)
    if activation.ndim != 2:
        raise ValueError("activation must have shape (quarters, samples_per_quarter)")
    quarters, samples = activation.shape
    if quarters == 0 or samples == 0:
        raise ValueError("activation must be nonempty")
    dt_hours = DELTA_HOURS / samples
    lower, upper = baseline_bounds(supply_mw, reserve_mw)
    u = reserve_mw * activation
    region_lists = [sign_regions(row, lower, upper) for row in u]
    region_count = int(np.prod([len(regions) for regions in region_lists]))
    if region_count > 20_000:
        raise ValueError("synthetic exact enumeration is deliberately bounded")

    best: tuple[float, np.ndarray] | None = None
    examined = 0
    for regions in itertools.product(*region_lists):
        examined += 1
        midpoints = np.asarray([(lo + hi) / 2.0 for lo, hi in regions])
        coefficients = np.empty(quarters)
        intercepts = np.empty(quarters)
        for q in range(quarters):
            coefficients[q], intercepts[q] = increment_affine(u[q], midpoints[q], eta, dt_hours)

        # Cyclic inventory is the terminal equality sum_q f_q(b_q)=0.
        equality = coefficients.reshape(1, -1)
        rhs_equal = np.asarray([-float(intercepts.sum())])
        ineq_rows: list[np.ndarray] = []
        ineq_rhs: list[float] = []
        if finite_capacity:
            cumulative_coeff = np.zeros(quarters)
            cumulative_intercept = 0.0
            initial = capacity_mwh / 2.0
            for q in range(quarters):
                # Add every within-quarter prefix to retain physical chronology.
                for value in u[q]:
                    c, d = increment_affine(np.asarray([value]), midpoints[q], eta, dt_hours)
                    cumulative_coeff[q] += c
                    cumulative_intercept += d
                    ineq_rows.append(cumulative_coeff.copy())
                    ineq_rhs.append(capacity_mwh - initial - cumulative_intercept)
                    ineq_rows.append(-cumulative_coeff.copy())
                    ineq_rhs.append(initial + cumulative_intercept)

        solution = linprog(
            c=np.full(quarters, DELTA_HOURS),
            A_ub=np.asarray(ineq_rows) if ineq_rows else None,
            b_ub=np.asarray(ineq_rhs) if ineq_rhs else None,
            A_eq=equality,
            b_eq=rhs_equal,
            bounds=list(regions),
            method="highs",
        )
        if solution.success and (best is None or float(solution.fun) < best[0] - TOL):
            best = float(solution.fun), np.asarray(solution.x, dtype=float)

    if best is None:
        raise AssertionError("The fixed synthetic fixture should be cyclically feasible")
    charging, discharging, signed, max_violation = audit_native_schedule(
        activation, best[1], capacity_mwh, reserve_mw, eta, finite_capacity
    )
    h0 = supply_mw * quarters * DELTA_HOURS
    return ExactResult(
        hydrogen_mwh=h0 - best[0],
        baseline_mw=best[1],
        charging_mwh=charging,
        discharging_mwh=discharging,
        signed_reserve_mwh=signed,
        maximum_state_violation_mwh=max_violation,
        regions_examined=examined,
    )


def audit_native_schedule(
    activation: np.ndarray,
    baseline_mw: np.ndarray,
    capacity_mwh: float,
    reserve_mw: float,
    eta: float,
    finite_capacity: bool,
) -> tuple[float, float, float, float]:
    """Replay a candidate and report throughput, signed energy, and state error."""

    activation = np.asarray(activation, dtype=float)
    quarters, samples = activation.shape
    dt_hours = DELTA_HOURS / samples
    state = capacity_mwh / 2.0
    low = state
    high = state
    charging = 0.0
    discharging = 0.0
    signed = 0.0
    for q in range(quarters):
        for a in activation[q]:
            p = reserve_mw * float(a) - float(baseline_mw[q])
            signed += reserve_mw * float(a) * dt_hours
            charging += max(-p, 0.0) * dt_hours
            discharging += max(p, 0.0) * dt_hours
            state += eta * max(-p, 0.0) * dt_hours - max(p, 0.0) * dt_hours / eta
            low = min(low, state)
            high = max(high, state)
    if finite_capacity:
        violation = max(0.0, -low, high - capacity_mwh, abs(state - capacity_mwh / 2.0))
    else:
        violation = abs(state - capacity_mwh / 2.0)
    return charging, discharging, signed, violation


def inventory_increment(values_mw: np.ndarray, weights: np.ndarray, baseline_mw: float, eta: float) -> float:
    """Compute an interval inventory increment for weighted support values."""

    return DELTA_HOURS * float(
        np.sum(weights * (eta * np.maximum(baseline_mw - values_mw, 0.0)
                          - np.maximum(values_mw - baseline_mw, 0.0) / eta))
    )


def best_dual_upper(
    values_mw: np.ndarray, weights: np.ndarray, supply_mw: float, reserve_mw: float, eta: float
) -> tuple[float, float, np.ndarray]:
    """Return a valid evaluated capacity-free dual upper bound and its baseline.

    Each scalar multiplier produces a valid upper bound; the fixed grid merely
    improves tightness.  This intentionally does not claim an exact dual
    maximizer.
    """

    values_mw = np.asarray(values_mw, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if values_mw.shape != weights.shape or values_mw.ndim != 2:
        raise ValueError("values and weights must have the same two-dimensional shape")
    if not np.allclose(weights.sum(axis=1), 1.0):
        raise ValueError("weights must sum to one in each interval")
    lower, upper = baseline_bounds(supply_mw, reserve_mw)
    candidates = np.clip(np.concatenate((np.full((len(values_mw), 1), lower), values_mw,
                                          np.full((len(values_mw), 1), upper)), axis=1), lower, upper)
    h0 = supply_mw * len(values_mw) * DELTA_HOURS
    best_cost = -np.inf
    best_lambda = None
    best_baseline = None
    for multiplier in np.linspace(eta, 1.0 / eta, 4097):
        increments = np.empty_like(candidates)
        for q in range(len(values_mw)):
            increments[q] = [inventory_increment(values_mw[q], weights[q], b, eta) for b in candidates[q]]
        costs = candidates * DELTA_HOURS - multiplier * increments
        indices = np.argmin(costs, axis=1)
        cost = float(costs[np.arange(len(values_mw)), indices].sum())
        if cost > best_cost:
            best_cost = cost
            best_lambda = float(multiplier)
            best_baseline = candidates[np.arange(len(values_mw)), indices]
    assert best_lambda is not None and best_baseline is not None
    return h0 - best_cost, best_lambda, np.asarray(best_baseline, dtype=float)


def rank_group_means(values_mw: np.ndarray, groups: int) -> np.ndarray:
    """Return equal-size rank-group means for one fixed synthetic fixture."""

    values_mw = np.sort(np.asarray(values_mw, dtype=float), axis=1)
    if values_mw.shape[1] % groups:
        raise ValueError("group count must divide the samples per interval")
    return values_mw.reshape(len(values_mw), groups, values_mw.shape[1] // groups).mean(axis=2)


def cyclic_common_shift(
    values_mw: np.ndarray,
    weights: np.ndarray,
    baseline_start: np.ndarray,
    supply_mw: float,
    reserve_mw: float,
    eta: float,
) -> tuple[np.ndarray, float]:
    """Find the cyclic common clipped-baseline shift for a weighted model."""

    lower, upper = baseline_bounds(supply_mw, reserve_mw)

    def total(shift: float) -> tuple[float, np.ndarray]:
        b = np.clip(baseline_start + shift, lower, upper)
        return float(sum(inventory_increment(values_mw[q], weights[q], b[q], eta) for q in range(len(b)))), b

    lo = lower - float(np.max(baseline_start))
    hi = upper - float(np.min(baseline_start))
    g_lo, _ = total(lo)
    g_hi, _ = total(hi)
    if g_lo > TOL or g_hi < -TOL:
        raise AssertionError("The synthetic endpoint construction did not bracket a cyclic root")
    for _ in range(90):
        mid = (lo + hi) / 2.0
        g_mid, _ = total(mid)
        if g_mid < 0.0:
            lo = mid
        else:
            hi = mid
    residual, baseline = total(hi)
    return baseline, residual


def endpoint_enclosure_lower(
    native_values_mw: np.ndarray,
    groups: int,
    mean_dual_baseline: np.ndarray,
    supply_mw: float,
    reserve_mw: float,
    eta: float,
) -> tuple[float, float, float]:
    """Build the endpoint-mixture primal lower side and native root witness."""

    native_values_mw = np.sort(np.asarray(native_values_mw, dtype=float), axis=1)
    quarters, samples = native_values_mw.shape
    grouped = native_values_mw.reshape(quarters, groups, samples // groups)
    low = grouped[:, :, 0]
    high = grouped[:, :, -1]
    mean = grouped.mean(axis=2)
    theta = np.divide(high - mean, high - low, out=np.ones_like(mean), where=high > low)
    endpoint_values = np.stack((low, high), axis=2).reshape(quarters, 2 * groups)
    endpoint_weights = np.stack((theta, 1.0 - theta), axis=2).reshape(quarters, 2 * groups) / groups
    endpoint_baseline, endpoint_residual = cyclic_common_shift(
        endpoint_values, endpoint_weights, mean_dual_baseline, supply_mw, reserve_mw, eta
    )
    native_weights = np.full_like(native_values_mw, 1.0 / samples)
    native_baseline, native_residual = cyclic_common_shift(
        native_values_mw, native_weights, mean_dual_baseline, supply_mw, reserve_mw, eta
    )
    h0 = supply_mw * quarters * DELTA_HOURS
    return h0 - float(endpoint_baseline.sum() * DELTA_HOURS), endpoint_residual, h0 - float(native_baseline.sum() * DELTA_HOURS)


def fixed_synthetic_fixture() -> np.ndarray:
    """Create one deterministic, non-empirical 3-by-6 activation fixture."""

    rng = np.random.default_rng(SEED)
    return np.clip(rng.normal(loc=-0.03, scale=0.58, size=(3, 6)), -1.0, 1.0)


def build_report() -> dict[str, object]:
    """Run every independent check and return JSON-safe synthetic results."""

    activation = fixed_synthetic_fixture()
    capacity = 0.55
    supply = 0.10
    reserve = 0.75
    eta = 0.94
    groups = 3
    h0 = supply * len(activation) * DELTA_HOURS
    native_exact = exact_by_enumeration(activation, capacity, supply, reserve, eta, finite_capacity=True)
    capacity_free_exact = exact_by_enumeration(activation, capacity, supply, reserve, eta, finite_capacity=False)
    coarse_exact = exact_by_enumeration(activation.mean(axis=1, keepdims=True), capacity, supply, reserve, eta, finite_capacity=True)

    native_values = reserve * activation
    native_weights = np.full_like(native_values, 1.0 / native_values.shape[1])
    native_dual_upper, native_lambda, _ = best_dual_upper(native_values, native_weights, supply, reserve, eta)
    means = rank_group_means(native_values, groups)
    mean_weights = np.full_like(means, 1.0 / groups)
    screen_upper, screen_lambda, mean_baseline = best_dual_upper(means, mean_weights, supply, reserve, eta)
    endpoint_lower, endpoint_residual, native_endpoint_witness = endpoint_enclosure_lower(
        native_values, groups, mean_baseline, supply, reserve, eta
    )

    throughput = native_exact.charging_mwh + native_exact.discharging_mwh
    kappa = (1.0 - eta**2) / (1.0 + eta**2)
    identity_residual = (native_exact.hydrogen_mwh - h0) - (-native_exact.signed_reserve_mwh - kappa * throughput)
    checks = {
        "native_finite_not_above_capacity_free_exact": native_exact.hydrogen_mwh <= capacity_free_exact.hydrogen_mwh + TOL,
        "capacity_free_exact_not_above_native_dual_upper": capacity_free_exact.hydrogen_mwh <= native_dual_upper + TOL,
        "native_dual_not_above_rank_mean_screen_upper": native_dual_upper <= screen_upper + TOL,
        "endpoint_lower_not_above_native_endpoint_witness": endpoint_lower <= native_endpoint_witness + TOL,
        "endpoint_witness_not_above_capacity_free_exact": native_endpoint_witness <= capacity_free_exact.hydrogen_mwh + TOL,
        "endpoint_lower_not_above_screen_upper": endpoint_lower <= screen_upper + TOL,
        "finite_exact_state_replay": native_exact.maximum_state_violation_mwh <= TOL,
        "capacity_free_terminal_replay": capacity_free_exact.maximum_state_violation_mwh <= TOL,
        "cyclic_throughput_identity": abs(identity_residual) <= TOL,
        "cyclic_loss_relation": abs(native_exact.discharging_mwh - eta**2 * native_exact.charging_mwh) <= TOL,
        "endpoint_cyclic_residual": abs(endpoint_residual) <= TOL,
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise AssertionError(f"synthetic verification failure: {failed}")

    def exact_dict(result: ExactResult) -> dict[str, object]:
        return {
            "hydrogen_input_mwh": result.hydrogen_mwh,
            "baseline_mw": result.baseline_mw.tolist(),
            "charging_mwh": result.charging_mwh,
            "discharging_mwh": result.discharging_mwh,
            "signed_reserve_mwh": result.signed_reserve_mwh,
            "maximum_state_violation_mwh": result.maximum_state_violation_mwh,
            "regions_examined": result.regions_examined,
        }

    return {
        "status": "PASS",
        "scope": "Synthetic software-verification fixture only; it contains no provider observation and no manuscript result.",
        "seed": SEED,
        "fixture": {
            "quarters": int(activation.shape[0]),
            "samples_per_quarter": int(activation.shape[1]),
            "activation": activation.tolist(),
            "capacity_mwh": capacity,
            "supply_mw": supply,
            "reserve_mw": reserve,
            "one_way_efficiency": eta,
            "no_reserve_mwh": h0,
            "rank_groups": groups,
        },
        "finite_native_exact": exact_dict(native_exact),
        "capacity_free_native_exact": exact_dict(capacity_free_exact),
        "quarter_mean_exact": exact_dict(coarse_exact),
        "evaluated_upper_bounds": {
            "native_capacity_free_mwh": native_dual_upper,
            "native_multiplier": native_lambda,
            "rank_mean_screen_mwh": screen_upper,
            "rank_mean_multiplier": screen_lambda,
        },
        "endpoint_mixture_primal": {
            "endpoint_lower_mwh": endpoint_lower,
            "endpoint_cyclic_residual_mwh": endpoint_residual,
            "native_capacity_free_witness_mwh": native_endpoint_witness,
        },
        "throughput_identity": {
            "kappa": kappa,
            "identity_residual_mwh": identity_residual,
            "loss_relation_residual_mwh": native_exact.discharging_mwh - eta**2 * native_exact.charging_mwh,
        },
        "checks": checks,
    }


def write_results(report: dict[str, object], directory: Path) -> None:
    """Write the two explicit synthetic artifacts requested by the parent task."""

    directory.mkdir(parents=True, exist_ok=True)
    (directory / "repro_demo_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    rows = [
        ("finite_native_exact", report["finite_native_exact"]["hydrogen_input_mwh"]),
        ("capacity_free_native_exact", report["capacity_free_native_exact"]["hydrogen_input_mwh"]),
        ("quarter_mean_exact", report["quarter_mean_exact"]["hydrogen_input_mwh"]),
        ("native_capacity_free_evaluated_upper", report["evaluated_upper_bounds"]["native_capacity_free_mwh"]),
        ("rank_mean_screen_evaluated_upper", report["evaluated_upper_bounds"]["rank_mean_screen_mwh"]),
        ("endpoint_mixture_primal_lower", report["endpoint_mixture_primal"]["endpoint_lower_mwh"]),
        ("native_endpoint_root_witness", report["endpoint_mixture_primal"]["native_capacity_free_witness_mwh"]),
    ]
    with (directory / "repro_demo_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["quantity", "mwh", "scope"])
        for label, value in rows:
            writer.writerow([label, value, "synthetic verification fixture only"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a source-data-free synthetic screening verification fixture.")
    parser.add_argument("--write-results", action="store_true", help="write results/repro_demo_* artifacts")
    parser.add_argument("--output-dir", type=Path, default=Path("results"), help="output directory when --write-results is used")
    args = parser.parse_args()
    report = build_report()
    if args.write_results:
        write_results(report, args.output_dir)
    print(json.dumps({"status": report["status"], "checks": report["checks"], "scope": report["scope"]}, indent=2))


if __name__ == "__main__":
    main()
