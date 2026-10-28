#!/usr/bin/env python3
"""Validate and render the prospective symmetric grip evidence contract."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import tempfile


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
MANIFEST_FIELDS = {
    "manifest_id", "manifest_sha256", "declared_before_capture", "object_id",
    "search_cells", "expected_unique_trial_keys",
}
SEARCH_CELL_FIELDS = {"search_cell_id", "control_parameters"}
PAIRING_RULE = ("Each finite search cell must be captured once for each authored runtime "
                "suffix; suffix-specific Euler observations are recorded independently and "
                "are not assumed mirrored.")
COMPLETENESS_RULE = ("Observed unique keys must equal the exact Cartesian product of the "
                     "predeclared manifest (object_id, search_cell_id) and authored suffixes "
                     "[l, r], with no missing or duplicate records.")
MEASUREMENT_SEMANTICS = {
    "required_authored_digit_labels_NOT_anatomical_ids":
        ["thumb", "index", "middle", "ring", "little"],
    "minimum_samples_per_required_digit": 1,
    "point_coordinate_frame": "object_frame_4x4",
    "triangle_indexing": "zero_based_pinned_source_topology",
    "signed_separation_convention":
        "positive_separated_zero_touching_negative_penetration",
    "object_surface_normal_convention": "unit_outward_in_object_frame",
}


def _exact_fields(actual, expected):
    return isinstance(actual, list) and len(actual) == len(expected) and set(actual) == expected


def validate_contract(contract):
    if (not isinstance(contract, dict)
            or type(contract.get("schema_version")) is not int
            or contract.get("schema_version") != 1
            or contract.get("status") != STATUS):
        raise ValueError("invalid grip capture contract identity")
    coverage = contract.get("coverage", {})
    if coverage.get("required_authored_runtime_suffixes") != ["l", "r"]:
        raise ValueError("exact authored suffix coverage l/r required")
    if coverage.get("authored_suffix_is_anatomical_side") is not False:
        raise ValueError("authored suffix cannot claim anatomical side")
    if coverage.get("pairing_key_fields") != ["object_id", "search_cell_id"]:
        raise ValueError("exact symmetric pairing keys required")
    if coverage.get("pairing_rule") != PAIRING_RULE:
        raise ValueError("independent suffix observations without mirroring required")
    if coverage.get("completeness_rule") != COMPLETENESS_RULE:
        raise ValueError("exact predeclared finite search completeness rule required")

    schema = contract.get("evidence_schema", {})
    checks = (
        (schema.get("search_manifest_fields"), MANIFEST_FIELDS),
        (schema.get("search_cell_fields"), SEARCH_CELL_FIELDS),
        (schema.get("object_evidence_fields"), OBJECT_FIELDS),
        (schema.get("per_trial_observation_fields"), TRIAL_FIELDS),
        (schema.get("contact_sample_fields"), CONTACT_FIELDS),
        (schema.get("returned_state_residual_fields"), RETURN_FIELDS),
    )
    if not _exact_fields(schema.get("search_manifest_fields"), MANIFEST_FIELDS):
        raise ValueError("exact predeclared search manifest fields required")
    if not all(_exact_fields(actual, expected) for actual, expected in checks[1:]):
        raise ValueError("exact required evidence fields missing or changed")
    semantics = contract.get("measurement_semantics")
    if not isinstance(semantics, dict):
        raise ValueError("contact geometry semantics required")
    if semantics.get("minimum_samples_per_required_digit") != 1:
        raise ValueError("at least one per-digit contact geometry sample required")
    if semantics != MEASUREMENT_SEMANTICS:
        raise ValueError("exact contact geometry semantics required")

    thresholds = contract.get("acceptance_thresholds", {})
    if (set(thresholds) != {"self_intersection", "body_object_contact",
                            "hand_collapse", "return_residual"}
            or any(value != "NOT_DEFINED" for value in thresholds.values())):
        raise ValueError("acceptance thresholds must remain undefined")
    limits = contract.get("limitations", {})
    if limits.get("force_or_pressure_measurement") != "NOT_MEASURED_BY_GEOMETRIC_CAPTURE":
        raise ValueError("geometric capture cannot claim force or pressure measurement")
    if limits.get("friction_or_slip_validation") != "NOT_RUN":
        raise ValueError("geometric capture cannot claim friction or slip validation")
    if limits.get("contact_acceptance") is not False:
        raise ValueError("contact acceptance must remain false")
    if (limits.get("grip_acceptance") is not False
            or limits.get("anatomical_approval") != "NOT_GRANTED"
            or limits.get("native_search_executed") is not False):
        raise ValueError("grip/anatomy/search nonapproval metadata required")
    research = contract.get("research_basis")
    if (not isinstance(research, list) or len(research) < 4
            or any(not isinstance(row, dict)
                   or set(row) != {"title", "doi", "use"}
                   or any(not isinstance(row[key], str) or not row[key].strip()
                          for key in ("title", "doi", "use"))
                   or re.fullmatch(r"10\.[0-9]{4,9}/\S+", row["doi"]) is None
                   for row in research)):
        raise ValueError("primary research basis required")
    return {
        "status": STATUS,
        "schema_version": 1,
        "required_authored_runtime_suffixes": ["l", "r"],
        "pairing_key_fields": ["object_id", "search_cell_id"],
        "pairing_rule": PAIRING_RULE,
        "completeness_rule": COMPLETENESS_RULE,
        "authored_suffix_is_anatomical_side": False,
        "required_search_manifest_fields": sorted(MANIFEST_FIELDS),
        "required_search_cell_fields": sorted(SEARCH_CELL_FIELDS),
        "required_object_evidence_fields": sorted(OBJECT_FIELDS),
        "required_per_trial_observation_fields": sorted(TRIAL_FIELDS),
        "required_contact_sample_fields": sorted(CONTACT_FIELDS),
        "required_return_residual_fields": sorted(RETURN_FIELDS),
        "measurement_semantics": dict(semantics),
        "acceptance_thresholds": dict(thresholds),
        "force_or_pressure_measurement": limits["force_or_pressure_measurement"],
        "friction_or_slip_validation": limits["friction_or_slip_validation"],
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


def _aliases(first, second):
    first = Path(first)
    second = Path(second)
    if first.resolve(strict=False) == second.resolve(strict=False):
        return True
    try:
        return first.exists() and second.exists() and os.path.samefile(first, second)
    except OSError:
        return False


def write_report(contract, out, evidence_paths=()):
    report = validate_contract(contract)
    out = Path(out)
    json_path = out / "grip_capture_contract.json"
    markdown_path = out / "grip_capture_contract.md"
    outputs = (json_path, markdown_path)
    if _aliases(*outputs):
        raise ValueError("outputs must be outside and distinct from evidence")
    out_resolved = out.resolve(strict=False)
    for evidence_path in map(Path, evidence_paths):
        evidence_resolved = evidence_path.resolve(strict=False)
        if evidence_path.is_dir() and (
                out_resolved == evidence_resolved
                or out_resolved.is_relative_to(evidence_resolved)):
            raise ValueError("outputs must be outside and distinct from evidence")
        if any(_aliases(output, evidence_path) for output in outputs):
            raise ValueError("outputs must be outside and distinct from evidence")
        if evidence_path.is_dir():
            members = (member for member in evidence_path.rglob("*") if member.is_file())
            if any(_aliases(output, member)
                   for member in members for output in outputs):
                raise ValueError("outputs must be outside and distinct from evidence")
    out.mkdir(parents=True, exist_ok=True)
    for path, content in ((json_path, json.dumps(report, indent=2) + "\n"),
                          (markdown_path, markdown(report))):
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", dir=out,
                    prefix=f".{path.name}.", delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    write_report(json.loads(args.contract.read_text(encoding="utf-8")), args.out,
                 [args.contract])


if __name__ == "__main__":
    main()
