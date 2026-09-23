"""Check the saved, public main-result ledger without source-data access.

This audit verifies arithmetic relationships among the deposited derived outputs.
It does not recreate provider-data quality checks or establish external validity.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def close(left: float, right: float, tolerance: float = 1e-8) -> bool:
    return abs(left - right) <= tolerance


def main() -> None:
    certificate = json.loads((RESULTS / "dual_certificate_2.0_0.1_0.94_17_20348.json").read_text(encoding="utf-8"))
    challenge = json.loads((RESULTS / "energy_challenge.json").read_text(encoding="utf-8"))
    manifest = json.loads((RESULTS / "revision_evidence_manifest.json").read_text(encoding="utf-8"))
    grid = list(csv.DictReader((RESULTS / "parameter_decision_grid.csv").open(encoding="utf-8", newline="")))

    reference = next(row for row in challenge if close(float(row["eta"]), 0.94) and close(float(row["amplitude"]), 1.0))
    assert reference["quarter_feasible"] and reference["native_cyclic_feasible"]
    assert float(reference["quarter_optimum_mwh"]) > float(reference["no_reserve_mwh"])
    assert float(certificate["hydrogen_upper_mwh"]) < float(reference["no_reserve_mwh"])
    assert close(float(certificate["hydrogen_upper_mwh"]), 502.97258481639153)
    assert close(float(reference["native_feasible_input_mwh"]), 496.72539079811526)
    assert close(float(reference["quarter_optimum_mwh"]), 512.8566778258428)
    assert manifest["status"] == "PASS"
    assert len(grid) == 15
    assert {row["classification"] for row in grid} >= {
        "aggregation_false_positive",
        "consistent_loss",
        "indeterminate",
        "native_gain_verified",
    }
    print(json.dumps({
        "status": "PASS",
        "finite_capacity_upper_mwh": certificate["hydrogen_upper_mwh"],
        "native_feasible_lower_mwh": reference["native_feasible_input_mwh"],
        "quarter_mean_exact_mwh": reference["quarter_optimum_mwh"],
        "grid_rows": len(grid),
        "scope": "Arithmetic and sign consistency among deposited derived results only.",
    }, indent=2))


if __name__ == "__main__":
    main()
