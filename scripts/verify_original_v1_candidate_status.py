#!/usr/bin/env python3
"""Verify ORIGINAL_V1_CANDIDATE_STATUS.json against repository evidence.

The status file is intentionally conservative. This verifier fails if it claims
more progress than the underlying provenance, candidate manifests, GLB audit or
deformation reports support.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = ROOT / "ORIGINAL_V1_CANDIDATE_STATUS.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


deval = load_module(
    "deformation_eval",
    ROOT / "scripts/evaluate_original_v1_deformation_report.py",
)
queue_mod = load_module(
    "repair_queue",
    ROOT / "scripts/build_original_v1_repair_queue.py",
)
glb_audit = load_module(
    "candidate_glb_audit",
    ROOT / "scripts/audit_original_v1_candidate_glbs.py",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def find_pose(report: list[dict[str, Any]], name: str) -> dict[str, Any]:
    matches = [item for item in report if item.get("pose") == name]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one pose {name!r}, got {len(matches)}")
    return matches[0]


def verify_status(status_path: Path = STATUS_PATH) -> dict[str, Any]:
    errors: list[str] = []
    status = load_json(status_path)

    def expect(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    expect(status.get("overall_status") == "candidate_not_production", "overall status must remain candidate_not_production")
    expect(status.get("production_approved") is False, "production_approved must be false")
    expect(status.get("asset") == "HomeGymPT_Male_ORIGINAL_v1", "asset identity mismatch")
    expect(status.get("rig") == "hgpt_canonical_v4_original", "rig identity mismatch")

    boundary = status.get("first_party_boundary", {})
    expect(
        boundary.get("historical_v_series_role") == "reference_only_lessons_and_failure_cases",
        "historical V-series role must remain reference-only",
    )
    expect(
        boundary.get("implementation_copying_from_v8_v15f_or_makehuman") == "prohibited",
        "legacy/reference implementation copying must remain prohibited",
    )

    gates = status.get("gates", {})

    o1 = load_json(ROOT / "ORIGINAL_V1_WORK/ORIGINAL_V1_PROVENANCE.json")
    expect(o1.get("asset_id") == status.get("asset"), "O1 provenance asset identity mismatch")
    expect(o1.get("clean_room") is True, "O1 provenance no longer says clean_room=true")
    expect(o1.get("starting_geometry") == "blank", "O1 starting geometry must remain blank")
    expect(o1.get("legacy_geometry_imported") is False, "O1 provenance reports legacy geometry")
    scaffold = o1.get("scaffold", {})
    expect(scaffold.get("third_party_geometry_imported") is False, "scaffold reports third-party geometry")
    expect(scaffold.get("legacy_projection_used") is False, "scaffold reports legacy projection")
    expect(gates.get("o1_clean_scaffold_provenance", {}).get("status") == "verified", "status file must mark O1 provenance verified")

    rigprov = load_json(ROOT / "ORIGINAL_V1_WORK/O2_RIG_PROVENANCE.json")
    expect(rigprov.get("rig_identity") == status.get("rig"), "O2 rig provenance identity mismatch")
    expect(rigprov.get("legacy_geometry_imported") is False, "O2 rig provenance reports legacy geometry")
    expect(
        rigprov.get("historical_53_bone_rig") == "reference_only_unbound",
        "historical rig must remain reference-only and unbound",
    )

    rig_payload = load_json(ROOT / "ORIGINAL_V1_WORK/hgpt_canonical_v4_original.json")
    expected_bones = int(gates.get("canonical_v4_structure", {}).get("expected_bones", -1))
    expect(len(rig_payload.get("bones", [])) == expected_bones == 63, "canonical v4 bone count/status mismatch")

    o4 = load_json(ROOT / "ORIGINAL_V1_WORK/candidates/O4_CANDIDATE_BUILD.json")
    expect(o4.get("stage") == "O4 candidate (not production)", "O4 build lost candidate/not-production marker")
    expect(int(o4.get("fallback_vertices", -1)) == 0, "O4 build used fallback vertices")
    not_used = set(o4.get("not_used", []))
    for prohibited in (
        "legacy/third-party weights",
        "data transfer from other meshes",
        "imported bind matrices",
    ):
        expect(prohibited in not_used, f"O4 build no longer records {prohibited!r} as not used")
    status_o4 = gates.get("o4_binding", {})
    expect(status_o4.get("status") == "candidate_built", "O4 status must remain candidate_built")
    expect(status_o4.get("candidate_sha256") == o4.get("candidate_sha256"), "O4 candidate SHA-256 mismatch")
    expect(status_o4.get("third_party_weight_transfer_used") is False, "status file claims third-party weight transfer")

    shorts = load_json(ROOT / "ORIGINAL_V1_WORK/candidates/O7_SHORTS_CANDIDATE.json")
    expect(shorts.get("stage") == "O7 candidate (not production)", "shorts lost candidate/not-production marker")
    shorts_not_used = set(shorts.get("not_used", []))
    for prohibited in ("legacy/third-party garments", "textures", "external materials"):
        expect(prohibited in shorts_not_used, f"shorts candidate no longer records {prohibited!r} as not used")
    expect(
        gates.get("shorts", {}).get("status") == "candidate_exists_not_approved",
        "shorts status must remain candidate_exists_not_approved",
    )

    glb_result = glb_audit.audit_candidate_set(
        ROOT / "ORIGINAL_V1_WORK/candidates/CANDIDATE_GLB_EXPORT.json",
        ROOT / "ORIGINAL_V1_WORK/hgpt_canonical_v4_original.json",
    )
    expect(glb_result.get("pass") is True, "candidate GLB structural audit does not pass")
    by_variant = {item["variant"]: item for item in glb_result.get("variants", [])}
    glb_status = gates.get("candidate_glb_structure", {})
    expect(glb_status.get("status") == "passed_candidate_only", "GLB status must remain passed_candidate_only")
    if "bare" in by_variant:
        expect(glb_status.get("bare_sha256") == by_variant["bare"].get("sha256"), "bare GLB SHA-256 mismatch")
    else:
        errors.append("bare GLB audit result missing")
    if "dressed" in by_variant:
        expect(glb_status.get("dressed_sha256") == by_variant["dressed"].get("sha256"), "dressed GLB SHA-256 mismatch")
    else:
        errors.append("dressed GLB audit result missing")
    expect(int(glb_status.get("images", -1)) == 0, "status GLB image count must be zero")
    expect(int(glb_status.get("textures", -1)) == 0, "status GLB texture count must be zero")
    expect(int(glb_status.get("animations", -1)) == 0, "status GLB animation count must be zero")
    expect(int(glb_status.get("legacy_token_hits", -1)) == 0, "status GLB legacy-token count must be zero")

    spec = load_json(ROOT / "ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json")
    poses = load_json(ROOT / "ORIGINAL_V1_WORK/candidates/pose_test_report_r2.json")
    dev = deval.make_summary(poses, poses, spec, "development_blocker", None)
    prod = deval.make_summary(poses, poses, spec, "production_target", None)
    repair = queue_mod.build_queue(poses, poses, spec, "development_blocker")

    dev_status = gates.get("deformation_development", {})
    expect(dev_status.get("status") == "blocked", "development deformation must remain blocked")
    expect(int(dev_status.get("failed_checks", -1)) == int(dev["failure_count"]) == 54, "development failure count mismatch")
    expect(int(dev_status.get("next_repair_priority", -1)) == int(repair["next_priority"]) == 1, "next repair priority mismatch")
    expect(int(dev_status.get("unmapped_failures", -1)) == int(repair["unmapped_failure_count"]) == 0, "unmapped failure count mismatch")

    prod_status = gates.get("deformation_production", {})
    expect(prod_status.get("status") == "blocked", "production deformation must remain blocked")
    expect(int(prod_status.get("failed_checks", -1)) == int(prod["failure_count"]) == 133, "production failure count mismatch")

    grip_status = gates.get("equipment_grip", {})
    curl = find_pose(poses, "curl_handle")
    pullup = find_pose(poses, "pullup_bar")
    curl_pen = max(float(curl["grip_l"]["max_penetration_mm"]), float(curl["grip_r"]["max_penetration_mm"]))
    pullup_pen = max(float(pullup["grip_l"]["max_penetration_mm"]), float(pullup["grip_r"]["max_penetration_mm"]))
    expect(grip_status.get("status") == "blocked", "equipment grip must remain blocked")
    expect(float(grip_status.get("curl_handle_max_penetration_mm", -1)) == curl_pen == 5.93, "curl handle penetration mismatch")
    expect(float(grip_status.get("pullup_bar_max_penetration_mm", -1)) == pullup_pen == 5.93, "pull-up bar penetration mismatch")
    expect(float(grip_status.get("development_limit_mm", -1)) == float(spec["profiles"]["development_blocker"]["grip_max_penetration_mm"]), "development grip limit mismatch")
    expect(float(grip_status.get("production_limit_mm", -1)) == float(spec["profiles"]["production_target"]["grip_max_penetration_mm"]), "production grip limit mismatch")

    expect(
        gates.get("owner_neutral_anatomy_review", {}).get("status") == "pending",
        "owner neutral-anatomy review must remain pending until explicit approval evidence exists",
    )
    expect(gates.get("runtime_integration", {}).get("status") == "pending", "runtime integration must remain pending")
    expect(gates.get("release_promotion", {}).get("status") == "blocked", "release promotion must remain blocked")

    next_action = status.get("next_action", {})
    expect(int(next_action.get("priority", -1)) == int(repair["next_priority"]) == 1, "status next_action priority mismatch")
    expect(next_action.get("group") == "shoulder", "current next_action group must be shoulder")

    return {
        "schema_version": 1,
        "pass": not errors,
        "status_file": str(status_path.relative_to(ROOT)).replace("\\", "/"),
        "overall_status": status.get("overall_status"),
        "production_approved": status.get("production_approved"),
        "development_failures": dev["failure_count"],
        "production_failures": prod["failure_count"],
        "next_repair_priority": repair["next_priority"],
        "unmapped_failures": repair["unmapped_failure_count"],
        "candidate_glb_structural_pass": glb_result.get("pass"),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", type=Path, default=STATUS_PATH)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    try:
        result = verify_status(args.status)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
