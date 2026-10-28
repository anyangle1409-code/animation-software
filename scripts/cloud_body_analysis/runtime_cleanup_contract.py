#!/usr/bin/env python3
"""Build a fail-closed runtime cleanup contract from verified W8 pose evidence."""
import argparse
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path

PROBE_PATH = Path(__file__).resolve().parents[1] / "phone_blender" / "pose_state_probe.py"
PROBE_SPEC = importlib.util.spec_from_file_location("runtime_cleanup_pose_probe", PROBE_PATH)
probe = importlib.util.module_from_spec(PROBE_SPEC)
PROBE_SPEC.loader.exec_module(probe)

STATUS = "MEASURED_W8_RUNTIME_CORRECTIVE_CLEANUP_CONTRACT_NOT_MODEL_REPAIR"
EXPECTED_TERMINAL_KEYS = {
    "HGPT_S1_SHOULDER": (
        "HGPT_S1_SHOULDER_l_145", "HGPT_S1_SHOULDER_l_160",
        "HGPT_S1_SHOULDER_r_145", "HGPT_S1_SHOULDER_r_160"),
    "HGPT_S3_SHAPE": (
        "HGPT_S3_SHAPE_l_125", "HGPT_S3_SHAPE_r_125"),
    "HGPT_S5_BAKE": (
        "HGPT_S5_BAKE_l_145", "HGPT_S5_BAKE_l_160",
        "HGPT_S5_BAKE_r_145", "HGPT_S5_BAKE_r_160"),
    "HGPT_S7_DELT": (
        "HGPT_S7_DELT_l_156", "HGPT_S7_DELT_l_166",
        "HGPT_S7_DELT_r_156", "HGPT_S7_DELT_r_166"),
}
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def digest(path):
    return hash_bytes(Path(path).read_bytes())


def hash_bytes(data):
    if not isinstance(data, bytes):
        raise TypeError("hash_bytes requires bytes")
    return hashlib.sha256(data).hexdigest()


def _validate_evidence(evidence):
    if not isinstance(evidence, dict):
        raise ValueError("invalid evidence metadata")
    for field in ("workflow_run_id", "artifact_id"):
        value = evidence.get(field)
        if type(value) is not int or value <= 0:
            raise ValueError("invalid evidence metadata: " + field)
    for field in ("artifact_sha256", "report_sha256"):
        value = evidence.get(field)
        if not isinstance(value, str) or SHA256.fullmatch(value) is None:
            raise ValueError("invalid evidence metadata: " + field)


def _terminal_partition(report):
    trials = report["terminal_corrective_key_clear_attribution"]["trials"]
    return {trial["family"]: list(trial["cleared_key_names"]) for trial in trials}


def _zero_residual(residual):
    return (
        residual.get("max_vertex_displacement_m") == 0.0
        and residual.get("rms_vertex_displacement_m") == 0.0
        and residual.get("vertices_moved_gt_1e_9_m") == 0)


def _paths_alias(first, second):
    first = Path(first)
    second = Path(second)
    if first.resolve(strict=False) == second.resolve(strict=False):
        return True
    try:
        return first.exists() and second.exists() and os.path.samefile(first, second)
    except OSError:
        return False


def build_contract(report, evidence):
    """Return the measured cleanup contract; never mutate *report*."""
    _validate_evidence(evidence)
    returned = report.get("post_benchmark_return_to_start_state", {})
    skeleton_only_failure = (
        isinstance(returned, dict)
        and returned.get("skeletal_pose_signature_restored_exactly") is True
        and returned.get("runtime_state_restored_exactly") is False
        and type(returned.get("vertices_moved_gt_1e_9_m")) is int
        and returned.get("vertices_moved_gt_1e_9_m", 0) > 0
        and type(returned.get("max_vertex_displacement_m")) in (int, float)
        and returned.get("max_vertex_displacement_m", 0.0) > 0.0
        and bool(returned.get("active_nonbasis_shape_keys")))
    if not skeleton_only_failure:
        raise ValueError("verified skeleton-only reset failure evidence required")

    errors = probe.validate_report(report)
    if errors:
        raise ValueError("pose report invalid: " + "; ".join(errors))

    partition = _terminal_partition(report)
    expected = {family: list(names) for family, names in EXPECTED_TERMINAL_KEYS.items()}
    if partition != expected:
        raise ValueError("pose report invalid: terminal active-key partition mismatch")
    active_names = [row["name"] for row in returned["active_nonbasis_shape_keys"]]
    if active_names != [name for names in expected.values() for name in names]:
        raise ValueError("pose report invalid: terminal active-key inventory mismatch")

    cleared = report["explicit_key_clear_experiment"]
    exact_clear = (
        cleared.get("runtime_state_restored_exactly") is True
        and cleared.get("skeletal_pose_signature_restored_exactly") is True
        and _zero_residual(cleared)
        and cleared.get("active_nonbasis_shape_keys") == [])
    if not exact_clear:
        raise ValueError("exact explicit cleanup evidence required")

    s3_rows = report["terminal_s3_individual_key_diagnostic"]["keys"]
    s3_numeric_noop = all(
        _zero_residual(row["stored_coordinate_delta_to_relative_key"])
        and _zero_residual(row["individual_clear_displacement_from_observed_terminal"])
        for row in s3_rows)
    if not s3_numeric_noop:
        raise ValueError("zero stored and evaluated S3 numeric-noop evidence required")
    return {
        "status": STATUS,
        "scope": {
            "model": report["model"],
            "source_sha256": report["source_sha256"],
            "path": "current W8 nine-sample shoulder-press diagnostic",
            "reference": "benchmark start state, not anatomical neutral",
        },
        "evidence": dict(evidence),
        "trigger": {
            "skeleton_reset_alone_insufficient": True,
            "skeletal_pose_signature_restored_exactly": True,
            "vertex_count": returned["vertex_count"],
            "vertices_moved_gt_1e_9_m": returned["vertices_moved_gt_1e_9_m"],
            "max_vertex_displacement_m": returned["max_vertex_displacement_m"],
            "rms_vertex_displacement_m": returned["rms_vertex_displacement_m"],
            "terminal_active_nonbasis_key_count": len(active_names),
        },
        "terminal_active_key_partition": partition,
        "tested_cleanup_operation":
            "RESET_SKELETON_AND_ZERO_ALL_NONBASIS_KEY_VALUES_IN_MEMORY",
        "runtime_requirement": {
            "lifecycle_boundary": "before reference reuse and after the exercised path",
            "operation": (
                "reset skeletal pose and clear lifecycle-owned non-Basis corrective state; "
                "an equivalent recomputation is acceptable only if every postcondition holds"),
            "selective_family_clear_is_not_sufficient_evidence": True,
            "s3_numeric_noop_endpoints_remain_in_cleanup_ownership": True,
        },
        "postconditions": {
            "skeletal_pose_signature_exact":
                cleared["skeletal_pose_signature_restored_exactly"],
            "benchmark_reference_geometry_exact":
                cleared["runtime_state_restored_exactly"],
            "max_vertex_displacement_m": cleared["max_vertex_displacement_m"],
            "rms_vertex_displacement_m": cleared["rms_vertex_displacement_m"],
            "vertices_moved_gt_1e_9_m": cleared["vertices_moved_gt_1e_9_m"],
            "active_nonbasis_shape_keys": list(cleared["active_nonbasis_shape_keys"]),
        },
        "claims": {
            "anatomical_neutral": False,
            "physiological_return": False,
            "model_repair": False,
            "source_edit_authorized": False,
            "selective_family_disable_authorized": False,
            "generic_movement_approved": False,
        },
    }


def markdown(contract):
    trigger = contract["trigger"]
    lines = [
        "# W8 runtime corrective cleanup contract — measured, non-mutating",
        "",
        f"Status: `{contract['status']}`",
        "",
        "## Measured trigger",
        "",
        ("Skeleton reset alone restored the skeletal signature but left "
         f"{trigger['vertices_moved_gt_1e_9_m']:,}/{trigger['vertex_count']:,} vertices "
         f"moved, max {trigger['max_vertex_displacement_m']:.12f} m and RMS "
         f"{trigger['rms_vertex_displacement_m']:.12f} m, with "
         f"{trigger['terminal_active_nonbasis_key_count']} active non-Basis keys."),
        "",
        "## Contract",
        "",
        ("At the tested lifecycle boundary, reset the skeleton and clear lifecycle-owned "
         "non-Basis corrective state. An equivalent recomputation is valid only when the "
         "skeletal signature, zero-active-key state and benchmark-reference geometry all "
         "match exactly."),
        "",
        "Terminal ownership remains S1, S3, S5 and S7. S3 stays included even though its "
        "verified terminal endpoint keys are numeric no-ops; this contract does not delete keys.",
        "",
        "## Claim boundary",
        "",
        "The reference is the benchmark start state, not anatomical neutral. This is not a "
        "physiological return, model repair, source-edit authorization, family-disable "
        "recommendation or generic movement approval.",
    ]
    return "\n".join(lines) + "\n"


def run(report_path, json_path, markdown_path, evidence):
    paths = (Path(report_path), Path(json_path), Path(markdown_path))
    if any(_paths_alias(paths[left], paths[right])
           for left, right in ((0, 1), (0, 2), (1, 2))):
        raise ValueError("report, JSON output and Markdown output require distinct paths")
    report_bytes = paths[0].read_bytes()
    if hash_bytes(report_bytes) != evidence.get("report_sha256"):
        raise ValueError("invalid evidence metadata: report_sha256 does not match input")
    report = json.loads(report_bytes.decode("utf-8"))
    result = build_contract(report, evidence)
    paths[1].write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    paths[2].write_text(markdown(result), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-markdown", type=Path, required=True)
    parser.add_argument("--workflow-run-id", type=int, required=True)
    parser.add_argument("--artifact-id", type=int, required=True)
    parser.add_argument("--artifact-sha256", required=True)
    parser.add_argument("--report-sha256", required=True)
    args = parser.parse_args()
    evidence = {
        "workflow_run_id": args.workflow_run_id,
        "artifact_id": args.artifact_id,
        "artifact_sha256": args.artifact_sha256,
        "report_sha256": args.report_sha256,
    }
    run(args.report, args.out_json, args.out_markdown, evidence)


if __name__ == "__main__":
    main()
