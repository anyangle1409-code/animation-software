#!/usr/bin/env python3
"""Validate development-only real-human evidence and full movement coverage for ORIGINAL-v1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json"
DEFAULT_COVERAGE = ROOT / "ORIGINAL_V1_HUMAN_EVIDENCE_COVERAGE.json"
DEFAULT_ENVELOPE = ROOT / "ORIGINAL_V1_MOVEMENT_ENVELOPE.json"

REQUIRED_VISUAL_PRIMITIVES = (
    "shoulder_flexion",
    "shoulder_abduction",
    "shoulder_axial_rotation",
)
VISUAL_SOURCE_TYPES = {"photo_series", "figure_series", "supplementary_video", "clinical_video"}
SOURCE_TYPES = VISUAL_SOURCE_TYPES | {"primary_study", "anatomy_article", "normative_dataset"}

# Controlled vocabulary. It is intentionally explicit: new biomechanical claims must
# be added here rather than silently passing because they happen to be non-empty.
PERMITTED_CONCLUSIONS = {
    "ankle_knee_hip_coupling",
    "anti_rotation_loading",
    "asymmetric_trunk_coupling",
    "bilateral_alignment",
    "bilateral_load_variation",
    "bone_motion",
    "closed_chain_shoulder_motion",
    "compensatory_coupling",
    "configuration_dependence",
    "diameter_dependence",
    "elbow_flexion_extension",
    "elbow_kinematics",
    "elbow_shoulder_coupling",
    "exercise_specific_upper_limb_kinematics",
    "finger_joint_flexion",
    "fold_boundaries",
    "foot_position_effect",
    "force_path",
    "forearm_rotation",
    "frontal_plane_alignment",
    "grasp_synergy",
    "grip_load_path",
    "grip_orientation",
    "hip_hinge_pattern",
    "horizontal_push_kinematics",
    "inter_digit_variation",
    "inter_subject_variation",
    "joint_coupling",
    "joint_interaction",
    "load_response",
    "loaded_calf_raise_timing",
    "loaded_upper_limb_coupling",
    "loaded_wrist_alignment",
    "lower_limb_kinematics",
    "motion_continuity",
    "movement_coupling",
    "movement_stability",
    "movement_timing",
    "multi_plane_rotation",
    "object_position_adaptation",
    "object_size_adaptation",
    "pelvis_leg_coupling",
    "plantarflexion_kinematics",
    "posterior_chain_coupling",
    "pronation_supination_effect",
    "push_pull_effect",
    "shoulder_forearm_coupling",
    "squat_timing",
    "surface_contour",
    "thumb_flexion",
    "thumb_opposition",
    "trunk_kinematics",
    "unilateral_lunge_kinematics",
    "volume_continuity",
    "wrist_alignment",
    "wrist_forearm_coupling",
}
REVIEW_STATES = {"verified", "needs_review", "rejected"}
COVERAGE_STATES = {"COVERED", "COVERED_WITH_LIMITATIONS"}
REQUIRED_FIELDS = (
    "id", "region", "movement_primitive", "source_type", "source",
    "movement_phase", "view", "diversity", "observable_landmarks",
    "permissible_conclusions", "uncertainty", "development_only",
    "review_status",
)


def _nonempty_strings(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(x, str) and x.strip() for x in value)


def _load(path_or_record: Path | dict[str, Any]) -> dict[str, Any]:
    if isinstance(path_or_record, Path):
        value = json.loads(path_or_record.read_text(encoding="utf-8-sig"))
    else:
        value = path_or_record
    if not isinstance(value, dict):
        raise ValueError("expected a JSON object")
    return value


def validate_manifest(path_or_manifest: Path | dict[str, Any]) -> list[str]:
    manifest = _load(path_or_manifest)
    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if manifest.get("asset") != "HomeGymPT_Male_ORIGINAL_v1":
        errors.append("asset identity mismatch")
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        return errors + ["entries must be a non-empty list"]

    seen: set[str] = set()
    visual_primitives: set[str] = set()
    for index, row in enumerate(entries):
        label = str(row.get("id") or f"entry[{index}]") if isinstance(row, dict) else f"entry[{index}]"
        if not isinstance(row, dict):
            errors.append(label + ": entry must be an object")
            continue
        for field in REQUIRED_FIELDS:
            if field not in row:
                errors.append(label + ": missing " + field)
        evidence_id = row.get("id")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            errors.append(label + ": id must be non-empty")
        elif evidence_id in seen:
            errors.append(label + ": duplicate evidence id")
        else:
            seen.add(evidence_id)
        for field in ("region", "movement_primitive", "movement_phase", "uncertainty"):
            if not isinstance(row.get(field), str) or not row.get(field, "").strip():
                errors.append(label + ": " + field + " must be non-empty")
        source_type = row.get("source_type")
        if source_type not in SOURCE_TYPES:
            errors.append(label + ": unsupported source_type")
        source = row.get("source")
        if not isinstance(source, dict):
            errors.append(label + ": source must be an object")
        else:
            if not any(isinstance(source.get(key), str) and source[key].strip() for key in ("url", "capture_id")):
                errors.append(label + ": source requires URL or capture_id")
            if not isinstance(source.get("license_use_note"), str) or not source["license_use_note"].strip():
                errors.append(label + ": source.license_use_note must be non-empty")
            if not isinstance(source.get("citation"), str) or not source["citation"].strip():
                errors.append(label + ": source.citation must be non-empty")
        diversity = row.get("diversity")
        if not isinstance(diversity, dict) or not isinstance(diversity.get("notes"), str) or not diversity.get("notes", "").strip():
            errors.append(label + ": diversity.notes must be non-empty")
        elif diversity.get("subject_count") is not None:
            count = diversity.get("subject_count")
            if not isinstance(count, int) or count <= 0:
                errors.append(label + ": diversity.subject_count must be null or a positive integer")
        if not _nonempty_strings(row.get("view")):
            errors.append(label + ": view must be a non-empty string list")
        if not _nonempty_strings(row.get("observable_landmarks")):
            errors.append(label + ": observable_landmarks must be a non-empty string list")
        conclusions = row.get("permissible_conclusions")
        if not _nonempty_strings(conclusions):
            errors.append(label + ": permissible_conclusions must be a non-empty string list")
        else:
            for conclusion in conclusions:
                if conclusion not in PERMITTED_CONCLUSIONS:
                    errors.append(label + ": unsupported permissible conclusion " + conclusion)
        if row.get("development_only") is not True:
            errors.append(label + ": development_only must be true")
        if row.get("review_status") not in REVIEW_STATES:
            errors.append(label + ": invalid review_status")
        if source_type in VISUAL_SOURCE_TYPES and row.get("review_status") == "verified":
            visual_primitives.add(row.get("movement_primitive"))

    for primitive in REQUIRED_VISUAL_PRIMITIVES:
        if primitive not in visual_primitives:
            errors.append("no visual source for required movement primitive " + primitive)
    return errors


def validate_coverage(
    path_or_coverage: Path | dict[str, Any],
    path_or_manifest: Path | dict[str, Any],
    path_or_envelope: Path | dict[str, Any],
) -> list[str]:
    """Cross-check movement-envelope coverage against verified evidence identities."""
    coverage = _load(path_or_coverage)
    manifest = _load(path_or_manifest)
    envelope = _load(path_or_envelope)
    errors: list[str] = []

    if coverage.get("schema_version") != 1:
        errors.append("coverage schema_version must be 1")
    if coverage.get("asset") != "HomeGymPT_Male_ORIGINAL_v1":
        errors.append("coverage asset identity mismatch")
    if coverage.get("production_approved") is not False:
        errors.append("coverage must not claim production approval")

    evidence_rows = manifest.get("entries", [])
    evidence_by_id = {
        row.get("id"): row for row in evidence_rows
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    }
    required_rows = envelope.get("required_categories")
    if not isinstance(required_rows, list) or not required_rows:
        return errors + ["movement envelope required_categories missing"]
    required_ids = []
    for row in required_rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"].strip():
            errors.append("movement envelope category id invalid")
        else:
            required_ids.append(row["id"])
    if len(required_ids) != len(set(required_ids)):
        errors.append("movement envelope contains duplicate category ids")

    rows = coverage.get("categories")
    if not isinstance(rows, list) or not rows:
        return errors + ["coverage categories must be a non-empty list"]
    seen: set[str] = set()
    for index, row in enumerate(rows):
        label = f"coverage[{index}]"
        if not isinstance(row, dict):
            errors.append(label + ": row must be an object")
            continue
        category_id = row.get("id")
        if not isinstance(category_id, str) or not category_id.strip():
            errors.append(label + ": id invalid")
            continue
        label = category_id
        if category_id in seen:
            errors.append(label + ": duplicate coverage category")
        seen.add(category_id)
        if category_id not in set(required_ids):
            errors.append(label + ": category is not in movement envelope")
        if row.get("status") not in COVERAGE_STATES:
            errors.append(label + ": invalid coverage status")
        if not isinstance(row.get("notes"), str) or not row["notes"].strip():
            errors.append(label + ": notes must be non-empty")
        ids = row.get("evidence_ids")
        if not _nonempty_strings(ids):
            errors.append(label + ": evidence_ids must be a non-empty string list")
            continue
        if len(ids) != len(set(ids)):
            errors.append(label + ": duplicate evidence id")
        for evidence_id in ids:
            evidence = evidence_by_id.get(evidence_id)
            if evidence is None:
                errors.append(label + ": unknown evidence id " + evidence_id)
            elif evidence.get("review_status") != "verified":
                errors.append(label + ": evidence not verified " + evidence_id)
            elif evidence.get("development_only") is not True:
                errors.append(label + ": evidence is not development-only " + evidence_id)

    missing = sorted(set(required_ids) - seen)
    if missing:
        errors.append("movement categories without evidence coverage: " + ", ".join(missing))
    return list(dict.fromkeys(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path, nargs="?", default=DEFAULT_MANIFEST)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--movement-envelope", type=Path, default=DEFAULT_ENVELOPE)
    parser.add_argument("--manifest-only", action="store_true")
    args = parser.parse_args()
    try:
        errors = validate_manifest(args.manifest)
        if not args.manifest_only:
            errors += validate_coverage(args.coverage, args.manifest, args.movement_envelope)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print("HUMAN EVIDENCE INVALID: " + str(exc))
        return 2
    if errors:
        print("HUMAN EVIDENCE INVALID")
        for error in list(dict.fromkeys(errors)):
            print("- " + error)
        return 1
    print("HUMAN EVIDENCE VERIFIED WITH MOVEMENT-ENVELOPE COVERAGE" if not args.manifest_only else "HUMAN EVIDENCE MANIFEST VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
