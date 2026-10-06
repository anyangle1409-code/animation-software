"""Compare continuous shoulder-arc audits for r96 Task 7 without inventing new gates.

The comparison reuses the repository's existing severity-drift tolerances for
volume and edge-ratio metrics. Metrics that do not already have a sanctioned
tolerance (for example torso drift) are reported but never auto-passed as
anatomy. Visual arc continuity remains an explicit Task 7 review requirement.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

DEFAULT_REQUIRED_POSES = (
    "press_top",
    "press_top_rhythm",
    "pullup_hang",
    "pullup_hang_rhythm",
)

REQUIRED_SAMPLE_KEYS = (
    "fraction",
    "torso_drift_max_m",
    "torso_edge_max",
    "torso_edge_min",
    "shoulder_edge_max",
    "shoulder_edge_min",
    "edge_p99",
    "volume_ratio",
)


def _finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def validate_arc(record: dict, required_poses=DEFAULT_REQUIRED_POSES) -> list[str]:
    issues: list[str] = []
    if record.get("schema_version") != 1:
        issues.append("arc_schema_invalid")
    if not isinstance(record.get("source_candidate_sha256"), str) or len(record["source_candidate_sha256"]) != 64:
        issues.append("arc_candidate_sha_invalid")
    poses = record.get("poses")
    if not isinstance(poses, dict):
        return issues + ["arc_poses_missing"]
    for pose in required_poses:
        rows = poses.get(pose)
        if not isinstance(rows, list) or len(rows) < 2:
            issues.append("arc_pose_missing_or_short:" + pose)
            continue
        fractions = []
        for row in rows:
            if not isinstance(row, dict):
                issues.append("arc_row_invalid:" + pose)
                continue
            for key in REQUIRED_SAMPLE_KEYS:
                if not _finite_number(row.get(key)):
                    issues.append(f"arc_metric_invalid:{pose}:{key}")
            if _finite_number(row.get("fraction")):
                fractions.append(float(row["fraction"]))
        if fractions:
            if abs(fractions[0]) > 1e-9 or abs(fractions[-1] - 1.0) > 1e-9:
                issues.append("arc_fraction_endpoints_invalid:" + pose)
            if any(b <= a for a, b in zip(fractions, fractions[1:])):
                issues.append("arc_fractions_not_strictly_increasing:" + pose)
    return list(dict.fromkeys(issues))


def compare_arcs(
    baseline: dict,
    candidate: dict,
    tolerances: dict,
    *,
    required_poses=DEFAULT_REQUIRED_POSES,
) -> dict:
    issues = validate_arc(baseline, required_poses) + validate_arc(candidate, required_poses)
    regressions: list[dict] = []
    measurements: list[dict] = []

    tol_volume = float(tolerances["volume_deviation_from_1_rise"])
    tol_p99 = float(tolerances["edge_ratio_p99_rise"])
    tol_min = float(tolerances["region_min_ratio_drop"])
    tol_max = float(tolerances["region_max_ratio_rise"])

    for pose in required_poses:
        brows = (baseline.get("poses") or {}).get(pose)
        crows = (candidate.get("poses") or {}).get(pose)
        if not isinstance(brows, list) or not isinstance(crows, list):
            continue
        if len(brows) != len(crows):
            issues.append("arc_sample_count_mismatch:" + pose)
            continue
        max_drift_rise = -math.inf
        max_abs_step = {key: 0.0 for key in ("torso_drift_max_m", "torso_edge_max", "shoulder_edge_max", "edge_p99", "volume_ratio")}
        prev = None
        for index, (base, cand) in enumerate(zip(brows, crows)):
            bf = base.get("fraction")
            cf = cand.get("fraction")
            if not (_finite_number(bf) and _finite_number(cf)) or abs(float(bf) - float(cf)) > 1e-8:
                issues.append(f"arc_fraction_mismatch:{pose}:{index}")
                continue

            checks = (
                ("volume_deviation_from_1", abs(float(cand["volume_ratio"]) - 1.0), abs(float(base["volume_ratio"]) - 1.0), tol_volume, "rise"),
                ("edge_p99", float(cand["edge_p99"]), float(base["edge_p99"]), tol_p99, "rise"),
                ("torso_edge_min", float(cand["torso_edge_min"]), float(base["torso_edge_min"]), tol_min, "drop"),
                ("torso_edge_max", float(cand["torso_edge_max"]), float(base["torso_edge_max"]), tol_max, "rise"),
                ("shoulder_edge_min", float(cand["shoulder_edge_min"]), float(base["shoulder_edge_min"]), tol_min, "drop"),
                ("shoulder_edge_max", float(cand["shoulder_edge_max"]), float(base["shoulder_edge_max"]), tol_max, "rise"),
            )
            for metric, cv, bv, tol, direction in checks:
                delta = cv - bv
                failed = delta > tol if direction == "rise" else delta < -tol
                if failed:
                    regressions.append({
                        "pose": pose,
                        "sample_index": index,
                        "fraction": float(cf),
                        "metric": metric,
                        "baseline": bv,
                        "candidate": cv,
                        "delta": delta,
                        "tolerance": tol,
                        "direction": direction,
                    })

            drift_rise = float(cand["torso_drift_max_m"]) - float(base["torso_drift_max_m"])
            max_drift_rise = max(max_drift_rise, drift_rise)
            if prev is not None:
                for key in max_abs_step:
                    max_abs_step[key] = max(max_abs_step[key], abs(float(cand[key]) - float(prev[key])))
            prev = cand

        if max_drift_rise != -math.inf:
            measurements.append({
                "pose": pose,
                "torso_drift_max_rise_m": max_drift_rise,
                "candidate_max_adjacent_sample_steps": max_abs_step,
                "note": "Measured only. No new anatomy/continuity threshold is inferred from these values.",
            })

    issues = list(dict.fromkeys(issues))
    return {
        "schema_version": 1,
        "status": "PASS" if not issues and not regressions else "BLOCKED",
        "production_approved": False,
        "arc_numeric_regression_pass": not issues and not regressions,
        "baseline_candidate_sha256": baseline.get("source_candidate_sha256"),
        "candidate_sha256": candidate.get("source_candidate_sha256"),
        "required_poses": list(required_poses),
        "issues": issues,
        "regression_count": len(regressions),
        "regressions": regressions,
        "measurements": measurements,
        "rule": "Only existing repository drift tolerances are blocking here. Visual/anatomical arc continuity remains separately mandatory.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("baseline_arc")
    ap.add_argument("candidate_arc")
    ap.add_argument("--acceptance", default="ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json")
    ap.add_argument("--out")
    ap.add_argument("--poses", default=",".join(DEFAULT_REQUIRED_POSES))
    args = ap.parse_args()

    baseline = json.loads(Path(args.baseline_arc).read_text(encoding="utf-8"))
    candidate = json.loads(Path(args.candidate_arc).read_text(encoding="utf-8"))
    acceptance = json.loads(Path(args.acceptance).read_text(encoding="utf-8"))
    tolerances = acceptance["comparison_tolerances"]
    poses = tuple(x.strip() for x in args.poses.split(",") if x.strip())
    result = compare_arcs(baseline, candidate, tolerances, required_poses=poses)
    payload = json.dumps(result, indent=2) + "\n"
    if args.out:
        out = Path(args.out)
        if out.exists():
            raise SystemExit("STOP — output collision; preserve existing evidence")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if result["arc_numeric_regression_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
