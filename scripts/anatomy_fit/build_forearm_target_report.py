#!/usr/bin/env python3
"""Build a stature-conditioned forearm target report from committed ANSUR II.

This script is deliberately independent of Blender. It computes the direct
male ANSUR radiale-stylion regression at the character's stature and compares
it with the a003 radius osteometric proxy. It does not infer ulna length from
radius; ulna stays independently gated.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ANSUR = ROOT / "ORIGINAL_V1_WORK/anatomy/sources/ansur2/ANSUR_II_MALE_Public.csv"
DEFAULT_SURFACE = ROOT / "ORIGINAL_V1_WORK/anatomy/audit/proportion_audit_001/surface_measurements.json"
DEFAULT_ADDENDUM = ROOT / "ORIGINAL_V1_WORK/anatomy/character_fit_r95_a003_review_addendum.json"
DEFAULT_OUT = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_forearm_target_report_v1.json"


def numeric_columns(path: Path) -> dict[str, np.ndarray]:
    rows = list(csv.DictReader(path.open(encoding="cp1252")))
    if not rows:
        raise ValueError(f"no rows in {path}")
    out = {}
    for col in rows[0]:
        vals = []
        ok = True
        for r in rows:
            try:
                vals.append(float(r[col]))
            except (TypeError, ValueError):
                ok = False
                break
        if ok:
            out[col.lower()] = np.asarray(vals, dtype=float)
    return out


def conditional(x: np.ndarray, y: np.ndarray, target_x: float) -> dict:
    slope, intercept = np.polyfit(x, y, 1)
    predicted = float(intercept + slope * target_x)
    residuals = y - (intercept + slope * x)
    sd = float(residuals.std(ddof=2))
    return {
        "predicted": predicted,
        "residual_sd": sd,
        "slope": float(slope),
        "intercept": float(intercept),
        "n": int(len(y)),
        "p5_p95_residual": [
            float(np.percentile(residuals, 5)),
            float(np.percentile(residuals, 95)),
        ],
    }


def build(ansur_path: Path, surface_path: Path, addendum_path: Path) -> dict:
    A = numeric_columns(ansur_path)
    required = ("stature", "radialestylionlength")
    for col in required:
        if col not in A:
            raise KeyError(f"ANSUR column missing: {col}")

    surface = json.loads(surface_path.read_text())
    addendum = json.loads(addendum_path.read_text())
    stature_mm = float(surface["stature_m"]["value"]) * 1000.0

    fit = conditional(A["stature"], A["radialestylionlength"], stature_mm)
    radius_proxy_mm = (
        float(addendum["trotter_gleser_corrected"]["bones"]["radius_left"]["length_m"])
        * 1000.0
    )
    delta = radius_proxy_mm - fit["predicted"]
    z = delta / fit["residual_sd"]

    return {
        "schema_version": 1,
        "created_by": "scripts/anatomy_fit/build_forearm_target_report.py",
        "purpose": "Direct stature-conditioned ANSUR radiale-stylion evidence for the skeleton-first radius target.",
        "status": "RADIUS_DIRECT_ANSUR_EVIDENCE_ULNA_STILL_OPEN",
        "stature_mm": stature_mm,
        "measurement_definition": {
            "ANSUR": "radiale-stylion length",
            "a003_proxy": "radial-head surface to radial styloid proxy from a003 review addendum",
            "compatibility": "close but must still preserve exact endpoint semantics when the canonical bone envelope is built",
        },
        "ansur_male_regression": {
            "predicted_radiale_stylion_mm": fit["predicted"],
            "residual_sd_mm": fit["residual_sd"],
            "slope_mm_per_mm_stature": fit["slope"],
            "intercept_mm": fit["intercept"],
            "n": fit["n"],
            "residual_p5_p95_mm": fit["p5_p95_residual"],
        },
        "a003": {
            "radius_osteometric_proxy_mm": radius_proxy_mm,
            "difference_from_stature_prediction_mm": delta,
            "z_vs_stature_conditioned_residuals": z,
        },
        "decision": {
            "radius": "REOPEN_AND_RETARGET_IF_DIRECT_REPORT_CONFIRMS_OUTLIER",
            "ulna": "DO_NOT_INFER_FROM_RADIUS; REQUIRE_ENDPOINT_MATCHED_ULNA_EVIDENCE",
        },
        "sources": {
            "ansur": str(ansur_path.relative_to(ROOT)),
            "a003_addendum": str(addendum_path.relative_to(ROOT)),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ansur", type=Path, default=DEFAULT_ANSUR)
    ap.add_argument("--surface", type=Path, default=DEFAULT_SURFACE)
    ap.add_argument("--addendum", type=Path, default=DEFAULT_ADDENDUM)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    report = build(args.ansur, args.surface, args.addendum)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
