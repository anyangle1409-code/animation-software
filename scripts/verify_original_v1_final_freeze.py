#!/usr/bin/env python3
"""Fail-closed Phase 12 final-freeze eligibility verifier.

A successful receipt means every declared prerequisite is coherently bound to the
same final candidate/assets/runtime and explicit owner authorization exists. This
tool never changes production flags, allowlists, branches, assets or baselines.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess

from original_v1_production_control import ROOT, build, digest, ensure_finite, evaluate
from verify_original_v1_phase_exit import verify_exit
from verify_original_v1_production_promotion import (
    asset_inventory,
    safe_path,
    timestamp,
    verify_packet,
    verified_report,
)

CONTRACT = "ORIGINAL_V1_FINAL_FREEZE_CONTRACT.json"
HELPER = "scripts/verify_original_v1_final_freeze.py"
PHASES = tuple(str(n) for n in range(4, 12))


def report_ref(root: Path, ref: dict, label: str) -> tuple[Path, dict]:
    if not isinstance(ref, dict) or not ref.get("path") or not ref.get("sha256"):
        raise ValueError(f"{label} requires path and SHA-256")
    path = safe_path(root, ref["path"])
    if not path.is_file() or digest(path) != ref["sha256"]:
        raise ValueError(f"{label} hash/path differs")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    ensure_finite(data)
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a JSON object")
    return path, data


def exact_ref(ref: dict, path: Path, root: Path) -> bool:
    return (
        isinstance(ref, dict)
        and ref.get("path") == path.relative_to(root.resolve()).as_posix()
        and ref.get("sha256") == digest(path)
    )


def verify_freeze_authorization(
    root: Path,
    auth: dict,
    candidate_sha: str,
    runtime_commit: str,
    inventory,
    promotion_packet_path: Path,
    promotion_receipt_path: Path,
) -> None:
    if auth.get("decision") != "OWNER AUTHORISED PRODUCTION FREEZE":
        raise ValueError("explicit OWNER AUTHORISED PRODUCTION FREEZE decision required")
    if auth.get("actor") != "owner" or auth.get("candidate_sha256") != candidate_sha:
        raise ValueError("freeze authorization owner/candidate identity differs")
    if auth.get("target_runtime_commit") != runtime_commit:
        raise ValueError("freeze authorization runtime commit differs")
    if auth.get("production_approved") is not False:
        raise ValueError("authorization record cannot itself claim production approval")
    if not isinstance(auth.get("decision_source"), str) or not auth["decision_source"].strip():
        raise ValueError("freeze authorization decision source required")
    timestamp(auth.get("evidence_timestamp"))
    if asset_inventory(root, auth.get("assets"), candidate_sha) != inventory:
        raise ValueError("freeze authorization asset inventory differs")
    if not exact_ref(auth.get("promotion_packet"), promotion_packet_path, root):
        raise ValueError("freeze authorization promotion packet identity differs")
    if not exact_ref(auth.get("promotion_receipt"), promotion_receipt_path, root):
        raise ValueError("freeze authorization promotion receipt identity differs")


def latest_production_report(state: dict) -> str:
    for row in state.get("latest_evidence", []):
        path = row.get("path", "")
        if path.endswith("_merged_pose_report.json"):
            return path
    raise ValueError("latest merged pose report missing")


def make_template(state: dict) -> dict:
    sha = state["last_known_candidate_sha256"]
    assets = [
        {"role": role, "path": None, "sha256": None, "candidate_sha256": sha}
        for role in ("bare", "dressed")
    ]
    null_ref = {"path": None, "sha256": None}
    return {
        "schema_version": 1,
        "status": "INCOMPLETE",
        "production_approved": False,
        "candidate_sha256": sha,
        "model_source_commit": None,
        "target_runtime_commit": None,
        "assets": assets,
        "promotion_packet": dict(null_ref),
        "promotion_receipt": dict(null_ref),
        "phase_exit_reports": {phase: dict(null_ref) for phase in PHASES},
        "freeze_authorization": dict(null_ref),
        "freeze_authorization_template": {
            "decision": "pending",
            "actor": None,
            "candidate_sha256": sha,
            "target_runtime_commit": None,
            "production_approved": False,
            "decision_source": None,
            "evidence_timestamp": None,
            "assets": assets,
            "promotion_packet": dict(null_ref),
            "promotion_receipt": dict(null_ref),
        },
        "source_context": {
            "candidate": state["current_candidate"],
            "candidate_state": state["candidate_state"],
            "development_failure_count": state["development_failure_count"],
            "production_failure_count": state["production_failure_count"],
            "phase_12_state": state["phases"]["12"]["state"],
            "active_epoch_baseline": state.get("pinned_baseline"),
            "next_action": state.get("next_action"),
        },
        "note": "INCOMPLETE template only. No gate executed, no owner decision inferred, no production state changed.",
    }


def verify_final_freeze(root: Path, packet: dict) -> list[str]:
    issues = []
    if not isinstance(packet, dict):
        return ["final freeze packet must be an object"]
    try:
        ensure_finite(packet)
    except ValueError as exc:
        issues.append(str(exc))

    sha = packet.get("candidate_sha256")
    runtime_commit = packet.get("target_runtime_commit")
    model_commit = packet.get("model_source_commit")
    if packet.get("schema_version") != 1:
        issues.append("final freeze schema_version must be 1")
    if packet.get("status") != "FINAL_FREEZE_PACKET":
        issues.append("final freeze packet status must be FINAL_FREEZE_PACKET")
    if packet.get("production_approved") is not False:
        issues.append("final freeze verifier input cannot claim production approval")
    if not re.fullmatch(r"[0-9a-f]{64}", str(sha or "")):
        issues.append("invalid final candidate SHA-256")
    if not re.fullmatch(r"[0-9a-f]{40}", str(runtime_commit or "")):
        issues.append("exact standalone runtime commit required")
    if not re.fullmatch(r"[0-9a-f]{40}", str(model_commit or "")):
        issues.append("exact final model source commit required")

    inventory = None
    try:
        inventory = asset_inventory(root, packet.get("assets"), sha)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        issues.append("assets: " + str(exc))

    promotion_packet_path = promotion_receipt_path = None
    promotion_packet = promotion_receipt = None
    try:
        promotion_packet_path, promotion_packet = report_ref(
            root, packet.get("promotion_packet"), "promotion packet"
        )
        promotion_issues = verify_packet(root, promotion_packet)
        if promotion_issues:
            raise ValueError("promotion packet gate contract fails: " + "; ".join(promotion_issues))
        if promotion_packet.get("candidate_sha256") != sha:
            raise ValueError("promotion packet candidate differs")
        if promotion_packet.get("target_runtime_commit") != runtime_commit:
            raise ValueError("promotion packet runtime commit differs")
        if asset_inventory(root, promotion_packet.get("assets"), sha) != inventory:
            raise ValueError("promotion packet assets differ")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        issues.append("promotion packet: " + str(exc))

    try:
        promotion_receipt_path, promotion_receipt = report_ref(
            root, packet.get("promotion_receipt"), "promotion receipt"
        )
        if promotion_receipt.get("eligibility") != "ALL_REQUIRED_GATES_SATISFIED":
            raise ValueError("promotion eligibility receipt is not satisfied")
        if promotion_receipt.get("production_approved") is not False:
            raise ValueError("promotion receipt must remain non-mutating")
        if promotion_receipt.get("issues") != []:
            raise ValueError("promotion receipt contains issues")
        if promotion_receipt.get("candidate_sha256") != sha:
            raise ValueError("promotion receipt candidate differs")
        if promotion_receipt.get("target_runtime_commit") != runtime_commit:
            raise ValueError("promotion receipt runtime commit differs")
        if promotion_packet_path is None or not exact_ref(
            promotion_receipt.get("promotion_packet"), promotion_packet_path, root
        ):
            raise ValueError("promotion receipt does not bind exact promotion packet bytes")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        issues.append("promotion receipt: " + str(exc))

    phase_refs = packet.get("phase_exit_reports")
    if not isinstance(phase_refs, dict) or set(phase_refs) != set(PHASES):
        issues.append("exact Phase 4-11 exit report references required")
    else:
        for phase in PHASES:
            try:
                _path, report = report_ref(root, phase_refs[phase], f"Phase {phase} exit report")
                phase_issues = verify_exit(root, phase, report, sha)
                if phase_issues:
                    raise ValueError("; ".join(phase_issues))
                if phase in ("10", "11") and report.get("target_runtime_commit") != runtime_commit:
                    raise ValueError("target runtime commit differs")
                if phase == "9" and report.get("source_git_commit") != model_commit:
                    raise ValueError("Phase 9 final model source commit differs")
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
                issues.append(f"Phase {phase}: {exc}")

    try:
        _auth_path, auth = report_ref(
            root, packet.get("freeze_authorization"), "freeze authorization"
        )
        if promotion_packet_path is None or promotion_receipt_path is None or inventory is None:
            raise ValueError("promotion/assets must verify before freeze authorization can bind them")
        verify_freeze_authorization(
            root,
            auth,
            sha,
            runtime_commit,
            inventory,
            promotion_packet_path,
            promotion_receipt_path,
        )
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        issues.append("freeze authorization: " + str(exc))

    try:
        state, _ = build(root)
        if state["last_known_candidate_sha256"] != sha:
            issues.append("freeze packet is not for latest complete candidate")
        if state["candidate_state"] == "rejected":
            issues.append("candidate is rejected")
        if state["development_failure_count"] or state["unresolved_regressions"]:
            issues.append("development failures or unresolved strict active-epoch regressions remain")
        if state["incomplete_candidates"]:
            issues.append("newer incomplete candidate evidence remains")
        for n in range(0, 12):
            if state["phases"][str(n)]["state"] != "complete":
                issues.append(f"Phase {n} is incomplete")
        report = latest_production_report(state)
        if evaluate(root, report, "production_target")["failure_count"]:
            issues.append("recomputed production deformation gate fails")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        issues.append("current state: " + str(exc))

    return list(dict.fromkeys(issues))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("packet", type=Path, nargs="?")
    ap.add_argument("--template", action="store_true")
    ap.add_argument("--json-out", type=Path, required=True)
    args = ap.parse_args()
    try:
        if args.json_out.exists():
            raise ValueError("final freeze output collision; preserve existing evidence")
        if args.template:
            if args.packet is not None:
                raise ValueError("template mode takes no packet")
            state, _ = build(ROOT)
            result = make_template(state)
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            print("INCOMPLETE FINAL FREEZE TEMPLATE — no approval or release mutation")
            return 0
        if args.packet is None:
            raise ValueError("final freeze packet required unless --template")
        packet_path = args.packet.resolve()
        if not packet_path.is_relative_to(ROOT.resolve()):
            raise ValueError("final freeze packet must remain inside repository")
        packet = json.loads(packet_path.read_text(encoding="utf-8-sig"))
        issues = verify_final_freeze(ROOT, packet)
        result = {
            "schema_version": 1,
            "freeze_eligibility": "REFUSED" if issues else "ALL_FREEZE_PREREQUISITES_SATISFIED",
            "production_approved": False,
            "issues": issues,
            "freeze_packet": {
                "path": packet_path.relative_to(ROOT).as_posix(),
                "sha256": digest(packet_path),
            },
            "candidate_sha256": packet.get("candidate_sha256") if isinstance(packet, dict) else None,
            "model_source_commit": packet.get("model_source_commit") if isinstance(packet, dict) else None,
            "target_runtime_commit": packet.get("target_runtime_commit") if isinstance(packet, dict) else None,
            "source_git_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "note": "Eligibility evidence only. A separate controlled owner-authorised release operation must record the actual production freeze; this verifier mutates nothing.",
        }
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 1 if issues else 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print("STOP — " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
