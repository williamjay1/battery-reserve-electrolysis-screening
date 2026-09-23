"""Rebuild the German normalized native cache from a checked local raw inventory.

This consolidates the Version 1 downloader, local-clock daily cache, and
evaluation-cache steps into one auditable command. Existing raw files are
only opened for reading. Network retrieval is disabled unless
--allow-download is supplied; if used, it can create only missing expected
archive names by exclusive creation.

All derived artifacts are written under --output-dir (normally D:). The script
rejects C: and E: output/report targets, so an E: raw directory cannot
accidentally become a derived-output destination.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import tempfile
import zipfile
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]


def preferred_path(*candidates: Path) -> Path:
    """Use the release-top-level location first, with a local staging fallback."""
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


# Raw source records are deliberately not bundled. Pass --raw-dir or place
# locally authorized source ZIPs under PROJECT/raw; existing files are read only.
DEFAULT_RAW_DIR = PROJECT / "raw"
DEFAULT_OUTPUT_DIR = PROJECT / "results" / "rebuild_german"
DEFAULT_REPORT = PROJECT / "results" / "rebuild_report.json"
DEFAULT_SUMMARY = PROJECT / "results" / "rebuild_summary.csv"
DEFAULT_HASH_INVENTORY = preferred_path(
    PROJECT.parent / "provenance" / "germany_raw_files.json",
    PROJECT / "public_repository" / "provenance" / "germany_raw_files.json",
)
DEFAULT_EXPECTED_CACHE_SHA256 = (
    "0a664312a5bdbb5b7bf3b12dc8e203c932f1b07b7e029abf887e9599efc91163"
)
OFFICIAL_DOWNLOAD_PAGE = (
    "https://www.netztransparenz.de/en/Balancing-Capacity/"
    "Balancing-Capacity-data/Data-in-second-resolution"
)
FORBIDDEN_OUTPUT_DRIVES = {"C:", "E:"}
SOURCE_NAME_RE = re.compile(r"SRL_Soll_\d{8}_\d{8}\.csv\.zip\Z")


@dataclass(frozen=True)
class ExpectedRaw:
    name: str
    byte_count: int
    sha256: str


@dataclass
class DayAudit:
    day: str
    source: str
    rows: int
    expected_seconds: int
    missing_seconds: int
    duplicate_seconds: int
    ordered: bool
    complete: bool
    error: str | None = None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_derived_output(path: Path) -> Path:
    """Reject C:/E: output paths before any directory or file is created."""
    resolved = path.expanduser().resolve(strict=False)
    if resolved.drive.upper() in FORBIDDEN_OUTPUT_DRIVES:
        raise ValueError(
            f"Refusing derived output under {resolved.drive}; select a D: "
            "(or other non-C/E) path."
        )
    return resolved


def atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path = require_derived_output(path)
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


def write_summary_csv(path: Path, report: dict[str, Any]) -> None:
    """Write a compact, redistribution-safe D: summary of a rebuild report."""
    path = require_derived_output(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    reconstruction = report.get("reconstruction", {})
    raw_inventory = report.get("raw_inventory", [])
    rows = [
        ("status", report.get("status", "UNKNOWN")),
        ("raw_files_expected", report.get("expected", {}).get("raw_files", "")),
        ("raw_files_verified", sum(item.get("status") == "verified" for item in raw_inventory)),
        ("downloaded_missing_files", len(report.get("downloaded_missing_files", []))),
        ("calibration_complete_days", reconstruction.get("calibration_complete_days", "")),
        ("calibration_samples", reconstruction.get("calibration_samples", "")),
        ("evaluation_complete_days", reconstruction.get("evaluation_complete_days", "")),
        ("samples", reconstruction.get("samples", "")),
        ("quarters", reconstruction.get("quarters", "")),
        ("hours", reconstruction.get("hours", "")),
        ("scale_mw", reconstruction.get("scale_mw", "")),
        ("cache_sha256", reconstruction.get("cache_sha256", "")),
        ("cache_hash_matches_expected", reconstruction.get("cache_hash_matches_expected", "")),
    ]
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix=f".{path.stem}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            writer = csv.writer(handle)
            writer.writerow(["metric", "value"])
            writer.writerows(rows)
        os.replace(temporary_name, path)
        temporary_name = None
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)


def load_expected_inventory(path: Path) -> list[ExpectedRaw]:
    parsed = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, list):
        raise ValueError(f"Expected a JSON list in {path}.")
    records: list[ExpectedRaw] = []
    names: set[str] = set()
    for item in parsed:
        if not isinstance(item, dict):
            raise ValueError("Hash inventory contains a non-object record.")
        name = str(item.get("file", ""))
        digest = str(item.get("sha256", "")).lower()
        byte_count = item.get("bytes")
        if not SOURCE_NAME_RE.fullmatch(name):
            raise ValueError(f"Unsafe or unexpected raw file name in inventory: {name!r}")
        if name in names:
            raise ValueError(f"Duplicate raw inventory name: {name}")
        if not isinstance(byte_count, int) or byte_count < 1:
            raise ValueError(f"Invalid byte count for {name}.")
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"Invalid SHA-256 for {name}.")
        names.add(name)
        records.append(ExpectedRaw(name, byte_count, digest))
    if len(records) != 19:
        raise ValueError(
            f"Expected the authorized 19-file inventory, found {len(records)} records."
        )
    return records


def check_raw_inventory(
    raw_dir: Path, expected: Iterable[ExpectedRaw]
) -> tuple[list[dict[str, Any]], list[ExpectedRaw]]:
    """Hash expected raw archives without changing the raw directory."""
    checks: list[dict[str, Any]] = []
    missing: list[ExpectedRaw] = []
    for item in expected:
        path = raw_dir / item.name
        if not path.is_file():
            checks.append(
                {
                    "file": item.name,
                    "status": "missing",
                    "expected_bytes": item.byte_count,
                    "expected_sha256": item.sha256,
                }
            )
            missing.append(item)
            continue
        actual_bytes = path.stat().st_size
        actual_hash = sha256_file(path)
        status = (
            "verified"
            if actual_bytes == item.byte_count and actual_hash == item.sha256
            else "mismatch"
        )
        checks.append(
            {
                "file": item.name,
                "status": status,
                "expected_bytes": item.byte_count,
                "actual_bytes": actual_bytes,
                "expected_sha256": item.sha256,
                "actual_sha256": actual_hash,
            }
        )
    return checks, missing


def download_missing_archives(
    raw_dir: Path, missing: Iterable[ExpectedRaw], page_url: str
) -> list[str]:
    """Explicit opt-in retrieval of missing files, never overwrite raw files."""
    missing = list(missing)
    if not missing:
        return []
    inventory_path = raw_dir / "germany_file_inventory.csv"
    if not inventory_path.is_file():
        raise FileNotFoundError(
            "Explicit download needs the provider inventory already saved at "
            f"{inventory_path}; no raw file was changed."
        )

    with inventory_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle, delimiter=";"))
    provider_ids = {
        row[0]: row[4]
        for row in rows
        if len(row) >= 5 and SOURCE_NAME_RE.fullmatch(row[0]) and row[4]
    }
    absent_ids = [item.name for item in missing if item.name not in provider_ids]
    if absent_ids:
        raise ValueError(
            "Provider inventory lacks IDs for: " + ", ".join(absent_ids)
        )

    # Imports occur only after the caller explicitly requests network retrieval.
    import requests
    from bs4 import BeautifulSoup

    downloaded: list[str] = []
    for item in missing:
        target = raw_dir / item.name
        if target.exists():
            raise FileExistsError(
                f"Refusing to overwrite existing raw path during download: {target}"
            )
        session = requests.Session()
        response = session.get(page_url, timeout=60)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        form_data = {
            tag["name"]: tag.get("value", "")
            for tag in soup.select('input[type="hidden"][name]')
        }
        form_data.update(
            {
                "__EVENTTARGET": (
                    "dnn$ctr3321$View$btnHiddenNrvSecondlyValueFileDownload"
                ),
                "__EVENTARGUMENT": "",
                "dnn$ctr3321$View$hFNrvSecondlyValueDownloadFileId": (
                    provider_ids[item.name]
                ),
                "dnn$ctr3321$View$hFNrvSecondlyValueDownloadFileName": item.name,
            }
        )
        archive = session.post(page_url, data=form_data, timeout=240)
        archive.raise_for_status()
        if archive.content[:2] != b"PK":
            raise ValueError(
                f"Provider response for {item.name} was not a ZIP archive; "
                "no file was created."
            )
        # xb is deliberate: repeated invocations cannot overwrite raw data.
        with target.open("xb") as handle:
            handle.write(archive.content)
        downloaded.append(item.name)
    return downloaded


def audit_day(frame: pd.DataFrame, source: str) -> tuple[DayAudit, np.ndarray | None]:
    """Reconstruct a complete local Berlin day exactly as the historical cache did."""
    try:
        if frame.empty:
            raise ValueError("empty day group")
        date_labels = frame.iloc[:, 0].astype(str)
        if date_labels.nunique(dropna=False) != 1:
            raise ValueError("CSV group contains more than one local date")
        naive = pd.DatetimeIndex(
            pd.to_datetime(
                frame.iloc[:, 0].astype(str) + " " + frame.iloc[:, 1].astype(str),
                format="%d.%m.%Y %H:%M:%S",
                errors="raise",
            )
        )
        day = naive[0].normalize()
        if (naive.normalize() != day).any():
            raise ValueError("timestamp group contains more than one local date")
        start = day.tz_localize("Europe/Berlin")
        end = (day + pd.Timedelta(days=1)).tz_localize("Europe/Berlin")
        expected_seconds = int((end - start).total_seconds())
        utc = (
            naive.tz_localize(
                "Europe/Berlin", ambiguous="infer", nonexistent="raise"
            ).tz_convert("UTC")
        )
        offsets = (
            utc - start.tz_convert("UTC")
        ).total_seconds().astype(np.int64)
        values = pd.to_numeric(frame.iloc[:, 2], errors="coerce").to_numpy(
            dtype=np.float64
        )
        duplicate_seconds = int(pd.Index(offsets).duplicated().sum())
        valid = (
            (offsets >= 0)
            & (offsets < expected_seconds)
            & np.isfinite(values)
        )
        values_by_second = np.full(expected_seconds, np.nan, dtype=np.float64)
        values_by_second[offsets[valid]] = values[valid]
        missing_seconds = int(np.isnan(values_by_second).sum())
        ordered = bool(np.all(np.diff(offsets) > 0))
        complete = (
            missing_seconds == 0 and duplicate_seconds == 0 and ordered
        )
        audit = DayAudit(
            day=str(day.date()),
            source=source,
            rows=int(len(frame)),
            expected_seconds=expected_seconds,
            missing_seconds=missing_seconds,
            duplicate_seconds=duplicate_seconds,
            ordered=ordered,
            complete=complete,
        )
        return audit, values_by_second if complete else None
    except Exception as exc:
        label = str(frame.iloc[0, 0]) if not frame.empty else "unknown"
        return (
            DayAudit(
                day=label,
                source=source,
                rows=int(len(frame)),
                expected_seconds=0,
                missing_seconds=0,
                duplicate_seconds=0,
                ordered=False,
                complete=False,
                error=str(exc),
            ),
            None,
        )


def stream_archive_days(
    path: Path, consume_complete_day: Callable[[DayAudit, np.ndarray], None]
) -> list[DayAudit]:
    """Read a source ZIP without extraction and pass only validated daily arrays."""
    audits: list[DayAudit] = []
    with zipfile.ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(members) != 1:
            raise ValueError(
                f"{path.name} must contain exactly one CSV member; found {members}"
            )
        carry: pd.DataFrame | None = None
        with archive.open(members[0]) as handle:
            for chunk in pd.read_csv(
                handle,
                sep=";",
                decimal=",",
                chunksize=500_000,
            ):
                if chunk.shape[1] < 3:
                    raise ValueError(f"{path.name} has fewer than three CSV columns.")
                if carry is not None:
                    chunk = pd.concat([carry, chunk], ignore_index=True)
                last_label = chunk.iloc[-1, 0]
                carry = chunk.loc[chunk.iloc[:, 0] == last_label].copy()
                closed = chunk.loc[chunk.iloc[:, 0] != last_label]
                for _, group in closed.groupby(closed.columns[0], sort=False):
                    audit, values = audit_day(group, path.name)
                    audits.append(audit)
                    if values is not None:
                        consume_complete_day(audit, values)
        if carry is not None and not carry.empty:
            audit, values = audit_day(carry, path.name)
            audits.append(audit)
            if values is not None:
                consume_complete_day(audit, values)
    return audits


def date_strings(first: str, last: str) -> list[str]:
    return pd.date_range(first, last, freq="D").strftime("%Y-%m-%d").tolist()


def cache_input_dates() -> tuple[set[str], set[str], set[str]]:
    calibration = set(date_strings("2025-01-01", "2025-06-30"))
    evaluation = set(date_strings("2026-01-01", "2026-07-31"))
    required = set(date_strings("2025-01-01", "2026-07-31"))
    return calibration, evaluation, required


def safe_unlink(path: Path) -> None:
    """Delete only a generated work file already proven to be below D output."""
    resolved = require_derived_output(path)
    if resolved.exists():
        resolved.unlink()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify 19 authorized German aFRR raw ZIPs, reconstruct complete "
            "Berlin-local days, normalize 2026 Jan-Jul, and check the cache hash."
        )
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=DEFAULT_RAW_DIR,
        help="Read-only directory holding the 19 checked SRL_Soll_*.csv.zip files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="D: directory for generated normalized cache and temporary work files.",
    )
    parser.add_argument(
        "--expected-hashes",
        type=Path,
        default=DEFAULT_HASH_INVENTORY,
        help="JSON inventory of approved raw archive bytes and SHA-256 values.",
    )
    parser.add_argument(
        "--expected-cache-hash",
        default=DEFAULT_EXPECTED_CACHE_SHA256,
        help="Expected SHA-256 of native_evaluation.npy.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT,
        help="D: JSON report path.",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=DEFAULT_SUMMARY,
        help="D: compact CSV summary path for the rebuild report.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Check input inventory and an already-built native_evaluation.npy; do not rebuild.",
    )
    parser.add_argument(
        "--allow-download",
        action="store_true",
        help=(
            "Explicitly allow retrieval of missing expected archives using the "
            "saved provider inventory. Existing raw files are never overwritten."
        ),
    )
    parser.add_argument(
        "--download-page",
        default=OFFICIAL_DOWNLOAD_PAGE,
        help="Official provider page used only together with --allow-download.",
    )
    parser.add_argument(
        "--keep-intermediates",
        action="store_true",
        help="Retain generated D: binary staging files after a successful rebuild.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = require_derived_output(args.output_dir)
    report_path = require_derived_output(args.report)
    summary_path = require_derived_output(args.summary)
    raw_dir = args.raw_dir.expanduser().resolve(strict=True)
    inventory_path = args.expected_hashes.expanduser().resolve(strict=True)
    expected = load_expected_inventory(inventory_path)
    if not re.fullmatch(r"[0-9a-fA-F]{64}", args.expected_cache_hash):
        raise ValueError("--expected-cache-hash must be a 64-character SHA-256.")
    expected_cache_hash = args.expected_cache_hash.lower()

    report: dict[str, Any] = {
        "schema_version": "1.0",
        "status": "RUNNING",
        "scope": (
            "Checked local reconstruction of the German one-second input cache. "
            "It is a source-data transformation, not an observed asset-dispatch "
            "record or a redistribution package."
        ),
        "reproducibility": {
            "script": str(Path(__file__).resolve()),
            "script_sha256": sha256_file(Path(__file__).resolve()),
            "raw_dir": str(raw_dir),
            "raw_input_policy": (
                "Existing raw files are opened read-only. Missing archives are "
                "downloaded only if --allow-download was explicitly supplied, "
                "using exclusive file creation."
            ),
            "output_dir": str(output_dir),
            "report": str(report_path),
            "summary": str(summary_path),
            "expected_hash_inventory": str(inventory_path),
            "expected_hash_inventory_sha256": sha256_file(inventory_path),
            "network_download_opt_in": bool(args.allow_download),
        },
        "expected": {
            "raw_files": len(expected),
            "cache_sha256": expected_cache_hash,
            "calibration_period": "2025-01-01 through 2025-06-30",
            "evaluation_period": "2026-01-01 through 2026-07-31",
            "normalization": (
                "99.5th percentile of absolute calibration MW; evaluation "
                "setpoints divided by it and clipped to [-1, 1]."
            ),
        },
    }

    staging: list[Path] = []
    try:
        raw_checks, missing = check_raw_inventory(raw_dir, expected)
        downloaded: list[str] = []
        if missing and args.allow_download:
            downloaded = download_missing_archives(
                raw_dir, missing, args.download_page
            )
            raw_checks, missing = check_raw_inventory(raw_dir, expected)
        report["raw_inventory"] = raw_checks
        report["downloaded_missing_files"] = downloaded
        mismatches = [
            item["file"] for item in raw_checks if item["status"] == "mismatch"
        ]
        if missing or mismatches:
            problems = []
            if missing:
                problems.append("missing=" + ",".join(item.name for item in missing))
            if mismatches:
                problems.append("mismatched=" + ",".join(mismatches))
            raise RuntimeError(
                "Raw inventory verification failed: " + "; ".join(problems)
            )

        output_dir.mkdir(parents=True, exist_ok=True)
        target_cache = output_dir / "native_evaluation.npy"
        if args.check_only:
            if not target_cache.is_file():
                raise FileNotFoundError(
                    f"--check-only requires an existing reconstructed cache: {target_cache}"
                )
            actual_hash = sha256_file(target_cache)
            with np.load(target_cache, mmap_mode="r", allow_pickle=False) as data:
                sample_count = int(data.shape[0])
                finite = bool(np.isfinite(data).all())
                min_value = float(np.min(data))
                max_value = float(np.max(data))
            report["reconstruction"] = {
                "mode": "check-only",
                "cache": str(target_cache),
                "cache_sha256": actual_hash,
                "cache_hash_matches_expected": actual_hash == expected_cache_hash,
                "samples": sample_count,
                "finite": finite,
                "minimum": min_value,
                "maximum": max_value,
            }
            if (
                actual_hash != expected_cache_hash
                or sample_count != 18_313_200
                or not finite
                or min_value < -1.0
                or max_value > 1.0
            ):
                raise RuntimeError("Existing cache failed the requested check-only gate.")
            report["status"] = "PASS"
            atomic_json_write(report_path, report)
            write_summary_csv(summary_path, report)
            print(json.dumps({"status": "PASS", "cache": str(target_cache)}))
            return 0

        work_dir = output_dir / ".rebuild_work"
        require_derived_output(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)
        calibration_bin = work_dir / "calibration_values.float64.bin"
        evaluation_bin = work_dir / "evaluation_values.float64.bin"
        for work_file in (calibration_bin, evaluation_bin):
            safe_unlink(work_file)
            staging.append(work_file)

        calibration_dates, evaluation_dates, required_dates = cache_input_dates()
        seen_dates: list[str] = []
        day_audits: list[DayAudit] = []
        calibration_samples = 0
        evaluation_samples = 0

        with calibration_bin.open("xb") as calibration_handle, evaluation_bin.open(
            "xb"
        ) as evaluation_handle:

            def consume(day: DayAudit, values: np.ndarray) -> None:
                nonlocal calibration_samples, evaluation_samples
                if day.day in seen_dates:
                    raise ValueError(f"Duplicate complete local day: {day.day}")
                seen_dates.append(day.day)
                if day.day in calibration_dates:
                    np.ascontiguousarray(values, dtype="<f8").tofile(calibration_handle)
                    calibration_samples += int(values.size)
                elif day.day in evaluation_dates:
                    np.ascontiguousarray(values, dtype="<f8").tofile(evaluation_handle)
                    evaluation_samples += int(values.size)

            for item in expected:
                day_audits.extend(stream_archive_days(raw_dir / item.name, consume))

        incomplete_days = [audit.day for audit in day_audits if not audit.complete]
        seen_set = set(seen_dates)
        missing_days = sorted(required_dates - seen_set)
        unexpected_days = sorted(seen_set - required_dates)
        if incomplete_days or missing_days or unexpected_days:
            raise RuntimeError(
                "Daily reconstruction gate failed: "
                f"incomplete={len(incomplete_days)}, "
                f"missing={len(missing_days)}, unexpected={len(unexpected_days)}."
            )

        expected_calibration_samples = sum(
            82_800 if day == "2025-03-30" else 86_400 for day in calibration_dates
        )
        expected_evaluation_samples = 18_313_200
        if calibration_samples != expected_calibration_samples:
            raise RuntimeError(
                f"Calibration sample count {calibration_samples} differs from "
                f"expected {expected_calibration_samples}."
            )
        if evaluation_samples != expected_evaluation_samples:
            raise RuntimeError(
                f"Evaluation sample count {evaluation_samples} differs from "
                f"expected {expected_evaluation_samples}."
            )

        calibration = np.memmap(
            calibration_bin, mode="r", dtype="<f8", shape=(calibration_samples,)
        )
        scale_mw = float(np.quantile(np.abs(calibration), 0.995))
        if not np.isfinite(scale_mw) or scale_mw <= 0.0:
            raise RuntimeError(f"Invalid calibration scale: {scale_mw}")
        del calibration

        evaluation = np.memmap(
            evaluation_bin, mode="r", dtype="<f8", shape=(evaluation_samples,)
        )
        temporary_cache = output_dir / ".native_evaluation.npy.tmp"
        safe_unlink(temporary_cache)
        staging.append(temporary_cache)
        normalized = np.lib.format.open_memmap(
            temporary_cache, mode="w+", dtype=np.float64, shape=(evaluation_samples,)
        )
        block = 1_000_000
        for start in range(0, evaluation_samples, block):
            stop = min(start + block, evaluation_samples)
            normalized[start:stop] = np.clip(
                evaluation[start:stop] / scale_mw, -1.0, 1.0
            )
        normalized.flush()
        del normalized
        del evaluation
        os.replace(temporary_cache, target_cache)
        staging.remove(temporary_cache)

        actual_hash = sha256_file(target_cache)
        native = np.load(target_cache, mmap_mode="r", allow_pickle=False)
        native_stats = {
            "samples": int(native.shape[0]),
            "quarters": int(native.shape[0] // 900),
            "hours": float(native.shape[0] / 3600.0),
            "finite": bool(np.isfinite(native).all()),
            "minimum": float(np.min(native)),
            "maximum": float(np.max(native)),
            "clipped_samples": int(np.count_nonzero(np.abs(native) >= 1.0)),
        }
        del native
        cache_ok = (
            actual_hash == expected_cache_hash
            and native_stats["samples"] == expected_evaluation_samples
            and native_stats["finite"]
            and native_stats["minimum"] >= -1.0
            and native_stats["maximum"] <= 1.0
        )
        if not cache_ok:
            raise RuntimeError(
                "Reconstructed cache did not meet the hash/sample/value gate."
            )

        report["reconstruction"] = {
            "mode": "rebuild",
            "cache": str(target_cache),
            "cache_sha256": actual_hash,
            "cache_hash_matches_expected": actual_hash == expected_cache_hash,
            "scale_mw": scale_mw,
            "calibration_complete_days": len(calibration_dates),
            "calibration_samples": calibration_samples,
            "evaluation_complete_days": len(evaluation_dates),
            **native_stats,
            "daily_audit": {
                "total_days": len(day_audits),
                "complete_days": sum(audit.complete for audit in day_audits),
                "incomplete_days": incomplete_days,
                "missing_days": missing_days,
                "unexpected_days": unexpected_days,
                "dst_short_days": [
                    audit.day
                    for audit in day_audits
                    if audit.expected_seconds == 82_800
                ],
            },
        }
        report["status"] = "PASS"
    except Exception as exc:
        report["status"] = "FAIL"
        report["error"] = f"{type(exc).__name__}: {exc}"
        atomic_json_write(report_path, report)
        write_summary_csv(summary_path, report)
        print(json.dumps({"status": "FAIL", "error": report["error"]}), file=sys.stderr)
        return 1
    finally:
        if not args.keep_intermediates:
            for work_file in staging:
                try:
                    safe_unlink(work_file)
                except OSError:
                    pass
            work_dir = output_dir / ".rebuild_work"
            try:
                if work_dir.exists() and not any(work_dir.iterdir()):
                    work_dir.rmdir()
            except OSError:
                pass

    atomic_json_write(report_path, report)
    write_summary_csv(summary_path, report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "cache": report["reconstruction"]["cache"],
                "cache_sha256": report["reconstruction"]["cache_sha256"],
                "scale_mw": report["reconstruction"]["scale_mw"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


