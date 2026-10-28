#!/usr/bin/env python3
"""Validate and render the prospective symmetric grip evidence contract."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


STATUS = "PROSPECTIVE_SYMMETRIC_GRIP_CAPTURE_CONTRACT_NOT_ACCEPTANCE"
OBJECT_FIELDS = {
    "object_id", "mesh_sha256", "length_unit_m", "object_frame_4x4",
    "surface_triangle_sha256",
}
TRIAL_FIELDS = {
    "trial_id", "object_id", "search_cell_id", "runtime_suffix",
    "thumb_01_euler_rad", "self_intersection_pairs",
    "body_object_intersection_pairs", "digit_object_contact_samples",
    "returned_state_residual",
}
CONTACT_FIELDS = {
    "digit_label", "body_triangle_id", "object_triangle_id",
    "signed_surface_separation_m", "body_point_xyz_m", "object_point_xyz_m",
    "object_surface_normal_xyz",
}
RETURN_FIELDS = {
    "moved_vertex_count", "maximum_m", "rms_m",
    "active_nonbasis_key_count", "skeletal_pose_equal",
}


def _exact_fields(actual, expected):
    return isinstance(actual, list) and len(actual) == len(expected) and set(actual) == expected


def validate_contract(contract):
    if (not isinstance(contract, dict) or contract.get("schema_version") != 1
            or contract.get("status") != STATUS):
        raise ValueError("invalid grip capture contract identity")
    coverage = contract.get("coverage", {})
    if coverage.get("required_authored_runtime_suffixes") != ["l", "r"]:
        raise ValueError("exact authored suffix coverage l/r required")
    if coverage.get("authored_suffix_is_anatomical_side") is not False:
        raise ValueError("authored suffix cannot claim anatomical side")
    if coverage.get("pairing_key_fields") != ["object_id", "search_cell_id"]:
        raise ValueError("exact symmetric pairing keys required")

    schema = contract.get("evidence_schema", {})
    checks = (
        (schema.get("object_evidence_fields"), OBJECT_FIELDS),
        (schema.get("per_trial_observation_fields"), TRIAL_FIELDS),
        (schema.get("contact_sample_fields"), CONTACT_FIELDS),
        (schema.get("returned_state_residual_fields"), RETURN_FIELDS),
    )
    if not all(_exact_fields(actual, expected) for actual, expected in checks):
        raise ValueError("exact required evidence fields missing or changed")

    thresholds = contract.get("acceptance_thresholds", {})
    if (set(thresholds) != {"self_intersection", "body_object_contact",
                            "hand_collapse", "return_residual"}
            or any(value != "NOT_DEFINED" for value in thresholds.values())):
        raise ValueError("acceptance thresholds must remain undefined")
    limits = contract.get("limitations", {})
    if limits.get("force_or_pressure_measurement") != "NOT_MEASURED_BY_GEOMETRIC_CAPTURE":
        raise ValueError("geometric capture cannot claim force or pressure measurement")
    if limits.get("contact_acceptance") is not False:
        raise ValueError("contact acceptance must remain false")
    if (limits.get("grip_acceptance") is not False
            or limits.get("anatomical_approval") != "NOT_GRANTED"
            or limits.get("native_search_executed") is not False):
        raise ValueError("grip/anatomy/search nonapproval metadata required")
    research = contract.get("research_basis")
    if (not isinstance(research, list) or len(research) < 4
            or any(not isinstance(row, dict) or not row.get("doi") for row in research)):
        raise ValueError("primary research basis required")
    return {
        "status": STATUS,
        "schema_version": 1,
        "required_authored_runtime_suffixes": ["l", "r"],
        "pairing_key_fields": ["object_id", "search_cell_id"],
        "authored_suffix_is_anatomical_side": False,
        "required_object_evidence_fields": sorted(OBJECT_FIELDS),
        "required_per_trial_observation_fields": sorted(TRIAL_FIELDS),
        "required_contact_sample_fields": sorted(CONTACT_FIELDS),
        "required_return_residual_fields": sorted(RETURN_FIELDS),
        "acceptance_thresholds": dict(thresholds),
        "force_or_pressure_measurement": limits["force_or_pressure_measurement"],
        "native_search_executed": False,
        "contact_acceptance": False,
        "grip_acceptance": False,
        "anatomical_approval": "NOT_GRANTED",
        "research_basis": research,
    }


def markdown(report):
    return "\n".join([
        "# Prospective symmetric grip capture contract",
        "",
        "**No native grip search executed. No grip, contact or anatomy approval.**",
        "",
        "## Symmetric finite coverage required",
        "",
        "Every `(object_id, search_cell_id)` must be captured independently for authored "
        "runtime suffixes `l` and `r`. These suffixes are not verified anatomical sides, and "
        "their observed Euler values are not assumed to mirror.",
        "",
        "## Object/contact evidence required",
        "",
        "The contract requires a hash-pinned object surface and frame, separate self- and "
        "body/object-intersection counts, per-digit triangle/point/normal/separation samples, "
        "and a return-state residual for every trial.",
        "",
        "Force, pressure, friction and slip are not measured by geometric capture. All "
        "acceptance thresholds remain `NOT_DEFINED`; research measurements and population "
        "averages are not converted into hard limits.",
        "",
    ])


def write_report(contract, out):
    report = validate_contract(contract)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "grip_capture_contract.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (out / "grip_capture_contract.md").write_text(markdown(report), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    write_report(json.loads(args.contract.read_text(encoding="utf-8")), args.out)


if __name__ == "__main__":
    main()
