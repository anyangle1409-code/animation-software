#!/usr/bin/env python3
"""Noncanonical, source-locked rib-plane orientation diagnostic.

Holcombe et al. 2017 (J Anat, doi:10.1111/joa.12632) describe three
successive source rib rotations: pump handle, lateral swing, bucket handle.
These are RESTING shape/orientation descriptors, NOT breathing ROM or exercise
angles. This module proposes a reversible orientation-frame HYPOTHESIS in the
HGPT frame (+X anatomical left, -Y anterior, +Z superior). It does not map any
actual thoracic vertebrae, identify rib heads, or solve the full rib spiral.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "ORIGINAL_V1_WORK/anatomy/rib_demographic_model_holcombe2017_v1.json"
# Exact Git blob identity checked against the audit branch; rejects later edits.
SOURCE_GIT_BLOB = "044da0b1896c342328b54d410db46f8139b673db"
SOURCE_DOI = "10.1111/joa.12632"
SOURCE_URL = "https://onlinelibrary.wiley.com/doi/full/10.1111/joa.12632"


def _finite_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _length(a):
    return math.sqrt(_dot(a, a))


def _positive_source_angle(value, name, upper):
    if not _finite_number(value) or not 0 <= value <= upper:
        raise ValueError(f"{name}: finite angle between 0 and {upper} degrees required")
    return math.radians(value)


def load_source(path=MODEL):
    raw = Path(path).read_bytes()
    blob_input = b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    sha = hashlib.sha1(blob_input).hexdigest()
    if sha != SOURCE_GIT_BLOB:
        raise ValueError("original rib model changed: do not silently replace pinned published values")
    model = json.loads(raw)
    if model.get("schema_version") != 1 or set(model.get("levels", {})) != {str(i) for i in range(1, 13)}:
        raise ValueError("rib model missing original 12-level source inventory")
    if model.get("source", {}).get("doi") != SOURCE_DOI:
        raise ValueError("unexpected source DOI")
    return model, hashlib.sha256(raw).hexdigest()


def orientation_hypothesis(alpha_ph_deg, alpha_ls_deg, alpha_bh_deg, side):
    """Diagnostic sequential rotations of a neutral, inferior-hanging rib.

    This translation of the published rotation ORDER assumes the source's
    neutrally hanging x-axis is -Z and the neutral local y-axis is lateral,
    in the HGPT coordinate convention. The source-to-body 3D FRAME MUST be
    independently checked before these axes are used to build bones.

    Local x is first pitched anteriorly with PH, then yawed laterally with LS.
    The local lateral y-axis rotates around the new x-axis by signed BH:
    positive on left and negative on right (source convention).
    """
    if side not in ("left", "right"):
        raise ValueError("side must be explicitly left or right")
    p = _positive_source_angle(alpha_ph_deg, "alpha_PH", 90)
    l = _positive_source_angle(alpha_ls_deg, "alpha_LS", 180)
    if not _finite_number(alpha_bh_deg) or abs(alpha_bh_deg) > 180:
        raise ValueError("alpha_BH must be finite and within signed 180 degrees")
    b = math.radians(alpha_bh_deg)
    s = 1 if side == "left" else -1
    # Rz(side*LS) * Rx(-PH) * (0,0,-1) in canonical HGPT axes
    x = (s*math.sin(p)*math.sin(l), -math.sin(p)*math.cos(l), -math.cos(p))
    # Rz(side*LS) * (side,0,0), perpendicular to x.
    y0 = (s*math.cos(l), math.sin(l), 0.0)
    v = _cross(x, y0)
    # Rodrigues around x; the side signedness is part of the 2017 convention.
    y = tuple(y0[i]*math.cos(s*b) + v[i]*math.sin(s*b) for i in range(3))
    z = _cross(x, y)
    if any(abs(_length(q)-1) > 1e-12 for q in (x, y, z)) or any(
        abs(_dot(a, c)) > 1e-12 for a, c in ((x, y), (x, z), (y, z))
    ) or _dot(x, _cross(y, z)) < 1-1e-12:
        raise AssertionError("orientation hypothesis not a proper orthonormal frame")
    return {"longitudinal_x": list(x), "rib_plane_y": list(y), "normal_z": list(z)}


def naive_independent_plane_angle_test(alpha_ph_deg, alpha_ls_deg):
    """Counterexample check ONLY, NOT the Holcombe sequential-rotation model.

    If someone independently interprets PH and LS as final acute line-to-
    coronal and line-to-sagittal angles, then |Y|=sin(PH), |X|=sin(LS).
    Any unit vector requires X^2+Y^2 <= 1. This deliberately tests and
    identifies an UNSAFE shortcut, not a defect in Holcombe et al.
    """
    ph = _positive_source_angle(alpha_ph_deg, "alpha_PH", 90)
    ls = _positive_source_angle(alpha_ls_deg, "alpha_LS", 180)
    raw = math.sin(ph)**2 + math.sin(ls)**2
    return {
        "sum_squared_assumed_components": raw,
        "independent_final_plane_angle_interpretation_possible": raw <= 1+1e-12,
        "not_an_evaluation_of_published_sequential_rotation_model": True,
    }


def bernstein_deviation_mm(fraction, z_a_mm, z_b_mm):
    """An optional 3D out-of-plane basis, strictly NOT an HGPT bone surface.

    Later source: Holcombe et al. 2018/2022 thoracic rib-geometry methodology,
    z(u)=Z_A * 3u(1-u)^2 + Z_B * 3u^2(1-u) along NORMALIZED FULL RIB ARC LENGTH.
    The pinned 2017 source table does NOT supply ZA/ZB values. Call only
    with externally obtained, independently source-verified millimetre values.
    """
    if not all(_finite_number(v) for v in (fraction, z_a_mm, z_b_mm)):
        raise ValueError("finite arc fraction and source-verified z coefficients required")
    if not 0 <= fraction <= 1:
        raise ValueError("full-rib normalized arc fraction must be in [0,1]")
    u = fraction
    return 3*z_a_mm*u*(1-u)**2 + 3*z_b_mm*u*u*(1-u)


def build_report(model, sha256):
    if set(model["levels"]) != {str(i) for i in range(1, 13)}:
        raise ValueError("exactly 12 source rib levels required")
    levels = {}
    unsafe = []
    for n in range(1, 13):
        p = model["levels"][str(n)]["population_mean"]
        ph, ls, bh = [p[k] for k in ("alpha_PH_deg", "alpha_LS_deg", "alpha_BH_deg")]
        check = naive_independent_plane_angle_test(ph, ls)
        if not check["independent_final_plane_angle_interpretation_possible"]:
            unsafe.append(n)
        levels[str(n)] = {
            "source_population_mean_deg": {"alpha_PH": ph, "alpha_LS": ls, "alpha_BH": bh},
            "naive_independent_angles_counterexample": check,
            "hypothesis_left": orientation_hypothesis(ph, ls, bh, "left"),
            "hypothesis_right": orientation_hypothesis(ph, ls, bh, "right"),
            "source_curve_proximal": None,
            "actual_3d_bone_surface": None,
            "out_of_plane_z_a_z_b_mm": None,
            "bone_head_tubercle_contact": None,
            "orientation_frame_independently_verified": False,
        }
    return {
        "schema_version": 1,
        "purpose": "NONCANONICAL diagnostic only: not a 3D rib mesh, breathing ROM or approved orientation",
        "source_doi": SOURCE_DOI, "source_url": SOURCE_URL,
        "source_git_blob_sha1": SOURCE_GIT_BLOB,
        "source_model_sha256": sha256,
        "reference_frame": "+X anatomical left, -Y anterior, +Z superior (HGPT)",
        "angular_convention": "sequential PH then LS then side-signed BH, as a source-frame HYPOTHESIS",
        "level_population_means_are_not_a_jointly_observed_individual": True,
        "naive_independent_angle_shortcut_invalid_levels": unsafe,
        "naive_shortcut_counterexamples_are_not_source_errors": True,
        "zero_verified_rib_bone_surfaces": True,
        "canonical_promotion_allowed": False,
        "blender_independent_visual_verification_required": True,
        "missing": [
            "verified published convention-to-HGPT frame transform",
            "proximal spiral branch rule (2016 Eq 2.18 unresolved)",
            "age/sex/stature/weight selected and individual multivariate parameter correlation",
            "3D out-of-plane ZA/ZB source for the target demographic",
            "patient-specific thoracic orientation and rib head/tubercle/cartilage surfaces",
        ],
        "levels": levels,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, help="new private JSON OUTSIDE repository (default: stdout)")
    args = ap.parse_args()
    model, sha = load_source()
    output = json.dumps(build_report(model, sha), indent=2, allow_nan=False) + "\n"
    if args.out is None:
        print(output, end="")
        return
    target = args.out.resolve()
    if target.is_relative_to(ROOT.resolve()):
        raise ValueError("refuse to write source-only diagnostic inside Git worktree")
    if not args.out.parent.is_dir():
        raise ValueError("private output directory does not exist")
    with target.open("x", encoding="utf8") as stream:
        stream.write(output)
    print(f"Noncanonical source diagnostic: {target}")


if __name__ == "__main__":
    main()
