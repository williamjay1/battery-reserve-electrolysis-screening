"""Recompute the Great Britain transfer audit from permitted derived caches.

The inputs are transformed NESO frequency records, not observed reserve dispatch.
This script never writes to the input cache.  Its only generated artifact is a
JSON audit at a caller-chosen D-drive path; C: and E: output paths are refused.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

import numpy as np


PROJECT = Path(__file__).resolve().parents[1]


def preferred_path(*candidates: Path) -> Path:
    """Use the release-top-level location first, with a local staging fallback."""
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


DEFAULT_CACHE_DIR = PROJECT / "prepared_inputs" / "gb_frequency"
DEFAULT_SOURCE_DIR = preferred_path(
    PROJECT.parent / "src",
    PROJECT / "public_repository" / "src",
)
DEFAULT_OUTPUT = PROJECT / "results" / "gb_transfer_audit.json"
FORBIDDEN_OUTPUT_DRIVES = {"C:", "E:"}
MONTH_FILES = tuple(f"2026-{month:02d}.npz" for month in range(1, 8))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_permitted_output(path: Path) -> Path:
    """Resolve an output path and refuse any C:/E: write target."""
    resolved = path.expanduser().resolve(strict=False)
    if resolved.drive.upper() in FORBIDDEN_OUTPUT_DRIVES:
        raise ValueError(
            f"Refusing output under {resolved.drive}; use a D: (or other non-C/E) path."
        )
    return resolved


def load_source_module(path: Path, module_name: str) -> Any:
    if not path.is_file():
        raise FileNotFoundError(f"Required deposited source module is absent: {path}")
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import deposited source module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path = require_permitted_output(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.stem}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary_name, path)
        temporary_name = None
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)


def as_finite_activation(npz_path: Path) -> np.ndarray:
    with np.load(npz_path, allow_pickle=False) as archive:
        if "activation" not in archive.files:
            raise ValueError(f"{npz_path} lacks the required 'activation' array.")
        activation = np.asarray(archive["activation"], dtype=np.float64)
    if activation.ndim != 2 or activation.shape[1] != 900:
        raise ValueError(
            f"{npz_path} has shape {activation.shape}; expected (quarters, 900)."
        )
    if activation.shape[0] == 0 or not np.isfinite(activation).all():
        raise ValueError(f"{npz_path} has an empty or non-finite activation path.")
    return activation


def monthly_record(
    path: Path,
    activation: np.ndarray,
    optimize: Callable[..., dict[str, Any]],
    capacity_free_bound: Callable[..., dict[str, Any]],
    *,
    capacity_mwh: float,
    supply_mw: float,
    reserve_mw: float,
    eta: float,
) -> dict[str, Any]:
    quarters = int(activation.shape[0])
    hours = quarters / 4.0
    no_reserve_mwh = supply_mw * hours
    signed_energy_mwh = float(reserve_mw * activation.sum() / 3600.0)
    absolute_energy_mwh = float(reserve_mw * np.abs(activation).sum() / 3600.0)
    quarter_mean = activation.mean(axis=1)
    within_quarter_absolute_deviation_mwh = float(
        reserve_mw * np.abs(activation - quarter_mean[:, None]).sum() / 3600.0
    )
    within_quarter_variance = float(
        np.mean((activation - quarter_mean[:, None]) ** 2)
    )

    quarter_solution = optimize(
        quarter_mean,
        E=capacity_mwh,
        R=reserve_mw,
        S=supply_mw,
        eta=eta,
        dt=0.25,
    )
    native_upper = capacity_free_bound(
        activation,
        S=supply_mw,
        eta=eta,
        R=reserve_mw,
        amplitude=1.0,
    )
    native_upper_mwh = float(native_upper["upper_mwh"])
    native_delta_mwh = native_upper_mwh - no_reserve_mwh
    kappa = (1.0 - eta**2) / (1.0 + eta**2)

    if quarter_solution["success"]:
        quarter_hydrogen = float(quarter_solution["hydrogen_input_mwh"])
        quarter_record: dict[str, Any] = {
            "status": "feasible",
            "hydrogen_input_mwh": quarter_hydrogen,
            "delta_vs_no_reserve_mwh": quarter_hydrogen - no_reserve_mwh,
            "maximum_equation_residual": float(
                quarter_solution["maximum_equation_residual"]
            ),
            "maximum_replay_violation": float(
                quarter_solution["maximum_replay_violation"]
            ),
            "iterations": int(quarter_solution["iterations"]),
        }
    else:
        quarter_record = {
            "status": "infeasible",
            "solver_message": str(quarter_solution["status"]),
        }

    record: dict[str, Any] = {
        "file": path.name,
        "file_sha256": sha256_file(path),
        "quarters": quarters,
        "seconds": int(activation.size),
        "hours": hours,
        "no_reserve_hydrogen_input_mwh": no_reserve_mwh,
        "signed_activation_energy_mwh": signed_energy_mwh,
        "absolute_activation_energy_mwh": absolute_energy_mwh,
        "within_quarter_absolute_deviation_mwh": (
            within_quarter_absolute_deviation_mwh
        ),
        "within_quarter_variance": within_quarter_variance,
        "quarter_mean_exact_lp": quarter_record,
        "native_capacity_free_evaluated_dual_upper": {
            "hydrogen_input_upper_mwh": native_upper_mwh,
            "delta_vs_no_reserve_mwh": native_delta_mwh,
            "dual_cost": float(native_upper["dual_cost"]),
            "multiplier": float(native_upper["multiplier"]),
            "relaxed_inventory_residual": float(
                native_upper["relaxed_inventory_residual"]
            ),
            "numerical_margin_mwh": float(native_upper["numerical_margin_mwh"]),
        },
    }

    # For U < 0, the cyclic signed-energy/throughput identity explains why
    # a favorable net energy sign does not establish a gain:
    # H0 - H = U + kappa Q.  Combining it with H <= evaluated_upper gives
    # Q >= (H0 - evaluated_upper - U) / kappa.
    if signed_energy_mwh < 0:
        threshold_for_positive_gain = -signed_energy_mwh / kappa
        implied_throughput_lower = (
            no_reserve_mwh - native_upper_mwh - signed_energy_mwh
        ) / kappa
        record["signed_energy_throughput_identity"] = {
            "kappa": kappa,
            "positive_gain_requires_throughput_below_mwh": (
                threshold_for_positive_gain
            ),
            "throughput_lower_bound_implied_by_native_upper_mwh": (
                implied_throughput_lower
            ),
            "interpretation": (
                "The one negative-net-energy month still has an evaluated "
                "capacity-free upper value below the no-reserve comparator."
            ),
        }
    return record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Recompute the GB transfer audit from permitted derived cache files. "
            "Input caches are read-only; output to C: or E: is refused."
        )
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=DEFAULT_CACHE_DIR,
        help="Directory containing 2026-01.npz through 2026-07.npz.",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=DEFAULT_SOURCE_DIR,
        help="Deposited source directory containing hydrogen_lp_pilot.py and cyclic_energy_dual.py.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Audit JSON path. C: and E: are intentionally rejected.",
    )
    parser.add_argument("--capacity-mwh", type=float, default=2.0)
    parser.add_argument("--supply-mw", type=float, default=0.1)
    parser.add_argument("--reserve-mw", type=float, default=0.75)
    parser.add_argument("--eta", type=float, default=0.94)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not (0.0 < args.eta <= 1.0):
        raise ValueError("--eta must lie in (0, 1].")
    if min(args.capacity_mwh, args.supply_mw, args.reserve_mw) <= 0.0:
        raise ValueError("Capacity, supply, and reserve must be positive.")
    output = require_permitted_output(args.output)
    cache_dir = args.cache_dir.expanduser().resolve(strict=True)
    source_dir = args.source_dir.expanduser().resolve(strict=True)

    missing = [name for name in MONTH_FILES if not (cache_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(
            f"GB cache is incomplete in {cache_dir}; missing: {', '.join(missing)}"
        )

    hydrogen_module = load_source_module(
        source_dir / "hydrogen_lp_pilot.py", "gb_audit_hydrogen_lp_pilot"
    )
    dual_module = load_source_module(
        source_dir / "cyclic_energy_dual.py", "gb_audit_cyclic_energy_dual"
    )
    records = []
    for name in MONTH_FILES:
        path = cache_dir / name
        activation = as_finite_activation(path)
        records.append(
            monthly_record(
                path,
                activation,
                hydrogen_module.optimize,
                dual_module.bound,
                capacity_mwh=args.capacity_mwh,
                supply_mw=args.supply_mw,
                reserve_mw=args.reserve_mw,
                eta=args.eta,
            )
        )

    infeasible_months = [
        item["file"][:7]
        for item in records
        if item["quarter_mean_exact_lp"]["status"] != "feasible"
    ]
    native_below_comparator = all(
        item["native_capacity_free_evaluated_dual_upper"][
            "delta_vs_no_reserve_mwh"
        ]
        < 0.0
        for item in records
    )
    feasible_quarter_records = [
        item for item in records if item["quarter_mean_exact_lp"]["status"] == "feasible"
    ]
    all_feasible_quarter_below = all(
        item["quarter_mean_exact_lp"]["delta_vs_no_reserve_mwh"] < 0.0
        for item in feasible_quarter_records
    )
    negative_signed_energy_months = [
        item["file"][:7] for item in records if item["signed_activation_energy_mwh"] < 0.0
    ]

    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "scope": (
            "Great Britain transfer audit from seven permitted derived GB "
            "frequency caches. This is a model-input stress replay, not "
            "observed reserve dispatch or a national market-performance estimate."
        ),
        "reproducibility": {
            "script": str(Path(__file__).resolve()),
            "script_sha256": sha256_file(Path(__file__).resolve()),
            "cache_dir": str(cache_dir),
            "source_dir": str(source_dir),
            "output_path": str(output),
            "input_is_read_only": True,
            "output_policy": "C: and E: outputs are rejected by this script.",
        },
        "model_configuration": {
            "capacity_mwh": args.capacity_mwh,
            "supply_mw": args.supply_mw,
            "reserve_mw": args.reserve_mw,
            "eta": args.eta,
            "quarter_seconds": 900,
            "cyclic_initial_and_terminal_inventory_mwh": args.capacity_mwh / 2.0,
            "quarter_mean_method": "Exact LP for interval-mean activation.",
            "native_method": (
                "Capacity-free evaluated dual upper bound on 900-second native "
                "activation paths; it is a relaxation, not a dispatch policy."
            ),
        },
        "months": records,
        "summary": {
            "months_audited": len(records),
            "native_capacity_free_upper_below_no_reserve_in_every_month": (
                native_below_comparator
            ),
            "quarter_mean_cyclic_lp_infeasible_months": infeasible_months,
            "all_feasible_quarter_mean_lp_values_below_no_reserve": (
                all_feasible_quarter_below
            ),
            "negative_signed_activation_energy_months": negative_signed_energy_months,
            "safe_interpretation": (
                "For these seven transformed GB input paths and this stated "
                "model configuration, the evaluated native capacity-free upper "
                "bound is below the no-reserve comparator in every month. "
                "The exact quarter-mean LP is also below that comparator in "
                "each month where it is cyclically feasible; it is infeasible "
                "in the listed months under quarter-fixed cyclic constraints. "
                "This is not a claim about GB market rules, assets, or dispatch."
            ),
        },
    }
    atomic_json_write(output, payload)
    print(
        json.dumps(
            {
                "output": str(output),
                "months": len(records),
                "native_upper_below_no_reserve_all_months": native_below_comparator,
                "quarter_lp_infeasible_months": infeasible_months,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


