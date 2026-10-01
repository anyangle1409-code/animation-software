#!/usr/bin/env python3
"""Validate ORIGINAL-v1 execution orchestration and print the current critical path.

Read-only. This tool never launches Blender, edits evidence, records phase completion,
chooses owner acceptance, or changes production state.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

from original_v1_production_control import ROOT, build, digest, ensure_finite

PLAN = "ORIGINAL_V1_EXECUTION_ORCHESTRATION.json"
HELPER = "scripts/original_v1_execution_orchestration.py"


def validate_plan(root: Path, plan: dict) -> dict:
    if plan.get("schema_version") != 1 or plan.get("status") != "PREPARED_EXECUTION_ORCHESTRATION":
        raise ValueError("unexpected orchestration contract")
    if plan.get("production_approved") is not False or plan.get("phase_complete") is not False:
        raise ValueError("orchestration plan cannot claim approval or phase completion")
    if plan.get("branch") != "claude/original-v1-blender-o2-20260929":
        raise ValueError("orchestration branch identity differs")

    stages = plan.get("prepared_support_stages")
    if not isinstance(stages, list) or not stages:
        raise ValueError("prepared support stages missing")
    stage_ids = [row.get("stage") for row in stages]
    if stage_ids != list(range(1, 13)):
        raise ValueError("prepared support stages must cover ordered Stage 1-12 exactly")
    checked_artifacts = []
    for row in stages:
        artifacts = row.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise ValueError(f"Stage {row.get('stage')} artifacts missing")
        for rel in artifacts:
            if not isinstance(rel, str) or not rel:
                raise ValueError("invalid orchestration artifact path")
            path = (root / rel).resolve()
            if not path.is_relative_to(root.resolve()) or not path.exists():
                raise ValueError(f"prepared support artifact missing: {rel}")
            checked_artifacts.append({"path": rel, "sha256": digest(path)})

    path = plan.get("critical_path")
    if not isinstance(path, list) or not path:
        raise ValueError("critical path missing")
    ids = [row.get("id") for row in path]
    if len(ids) != len(set(ids)) or any(not isinstance(x, str) or not x for x in ids):
        raise ValueError("critical path IDs invalid or duplicated")
    if ids[0] != "3B_r30" or ids[-1] != "controlled_release":
        raise ValueError("critical path endpoints differ")
    valid_stage_ids = set(stage_ids)
    for row in path:
        support = row.get("support_stages", [])
        if not isinstance(support, list) or any(x not in valid_stage_ids for x in support):
            raise ValueError(f"{row.get('id')} references unknown support stage")
        if row.get("next_on_pass") is not None and row["next_on_pass"] not in ids:
            raise ValueError(f"{row.get('id')} next_on_pass target missing")
    return {
        "prepared_stage_count": len(stages),
        "critical_path_count": len(path),
        "artifact_count": len(checked_artifacts),
        "artifacts": checked_artifacts,
    }


def select_node(plan: dict, state: dict) -> dict:
    nodes = {row["id"]: row for row in plan["critical_path"]}
    phases = state.get("phases", {})
    if phases.get("3", {}).get("state") != "complete":
        sub = state.get("current_subphase")
        if sub == "3B":
            node = nodes["3B_r30"]
            expected = state.get("next_action", {})
            if expected.get("command") != node.get("action"):
                raise ValueError("current selector command differs from orchestration r30 action")
            return node
        if sub == "3C":
            return nodes["3C_grip_thumb"]
        if sub == "3D":
            return nodes["3D_wrist"]
        if sub == "3E":
            return nodes["3E_lunge"]
        raise ValueError(f"unsupported active Phase 3 subphase: {sub}")

    mapping = {
        "4": "4_freeze",
        "5": "5_anatomy",
        "6": "6_topology",
        "7": "7_clothing",
        "8": "8_materials",
        "9": "9_production_deformation",
        "10": "10_runtime",
        "11": "11_visual_qa",
        "12": "12_freeze",
    }
    for phase, node_id in mapping.items():
        if phases.get(phase, {}).get("state") != "complete":
            return nodes[node_id]
    return nodes["controlled_release"]


def current_summary(plan: dict, state: dict, plan_info: dict) -> dict:
    node = select_node(plan, state)
    support_map = {row["stage"]: row for row in plan["prepared_support_stages"]}
    support = [support_map[n] for n in node.get("support_stages", [])]
    return {
        "schema_version": 1,
        "status": "READ_ONLY_EXECUTION_GUIDANCE",
        "production_approved": False,
        "current_candidate": state.get("current_candidate"),
        "candidate_state": state.get("candidate_state"),
        "current_phase": state.get("current_phase"),
        "current_subphase": state.get("current_subphase"),
        "development_failure_count": state.get("development_failure_count"),
        "unresolved_regression_count": len(state.get("unresolved_regressions", [])),
        "selected_node": node,
        "prepared_support": support,
        "parallel_safe": node.get("parallel_safe", []),
        "status_next_action": state.get("next_action"),
        "orchestration_validation": {
            "prepared_stage_count": plan_info["prepared_stage_count"],
            "critical_path_count": plan_info["critical_path_count"],
            "artifact_count": plan_info["artifact_count"],
        },
        "rules": [
            "Run session preflight and re-read live HEAD before execution.",
            "Prepared support is not permission to skip the selected critical-path entry/exit checks.",
            "Routine review remains non-blocking unless the master plan explicitly says otherwise.",
            "This report does not launch any command.",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    try:
        plan_path = ROOT / PLAN
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        ensure_finite(plan)
        info = validate_plan(ROOT, plan)
        state, _ = build(ROOT)
        result = current_summary(plan, state, info)
        result.update({
            "orchestration_plan": {"path": PLAN, "sha256": digest(plan_path)},
            "source_git_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "generated_utc": datetime.now(timezone.utc).isoformat(),
        })
        if args.json_out:
            out = args.json_out.resolve()
            if not out.is_relative_to(ROOT.resolve()):
                raise ValueError("output must remain inside repository")
            if out.exists():
                raise ValueError("orchestration output collision; preserve existing guidance")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            node = result["selected_node"]
            print(f"CURRENT EXECUTION NODE: {node['id']} — {node['roadmap']}")
            print("ACTION:", node["action"])
            if result["prepared_support"]:
                print("PREPARED SUPPORT:")
                for row in result["prepared_support"]:
                    print(f"  Stage {row['stage']}: {row['name']}")
            if result["parallel_safe"]:
                print("PARALLEL SAFE:")
                for item in result["parallel_safe"]:
                    print("  -", item)
            print("READ-ONLY GUIDANCE — no command launched")
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print("STOP — " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
