#!/usr/bin/env python3
"""Read-only discovery/comparison for the future ORIGINAL-v1 standalone runtime handoff.

Run from the isolated model checkout and point --runtime-root at a separate checkout
of the authoritative standalone branch. This tool never edits either checkout,
never copies runtime code, never activates assets and never grants a phase PASS.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

from original_v1_contact_source_bridge import verify_bridge
from original_v1_production_control import ROOT, ensure_finite

CONTRACT = "ORIGINAL_V1_RUNTIME_DISCOVERY_CONTRACT.json"
CONTACT_SPEC = "ORIGINAL_V1_CONTACT_SOURCE_BRIDGE.json"
HELPER = "scripts/original_v1_runtime_discovery.py"
MODEL_RIG_LOCK = "ORIGINAL_V1_WORK/SKELETON_MOTION_LOCK_rev2_forearm_twist_only.json"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_git(root: Path, args: list[str]) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=root,
        text=True,
        stderr=subprocess.STDOUT,
    ).strip()


def repository_state(root: Path, expected_branch: str, check_remote: bool = True) -> dict:
    root = root.resolve()
    if not (root / ".git").exists() and not (root / ".git").is_file():
        raise ValueError(f"not a git checkout: {root}")
    branch = run_git(root, ["branch", "--show-current"])
    head = run_git(root, ["rev-parse", "HEAD"])
    dirty = run_git(root, ["status", "--porcelain", "--untracked-files=all"])
    if branch != expected_branch:
        raise ValueError(f"wrong branch: {branch}; expected {expected_branch}")
    if dirty:
        raise ValueError(f"checkout is dirty: {root}")
    remote_head = None
    if check_remote:
        rows = run_git(root, ["ls-remote", "--exit-code", "origin", f"refs/heads/{expected_branch}"])
        remote_head = rows.split()[0]
        if remote_head != head:
            raise ValueError(f"local HEAD {head} differs from remote {remote_head}")
    return {
        "root": str(root),
        "branch": branch,
        "head": head,
        "remote_head": remote_head,
        "clean": True,
    }


def compare_source_bytes(model_root: Path, runtime_root: Path, paths: list[str]) -> list[dict]:
    rows = []
    for rel in paths:
        model = (model_root / rel).resolve()
        runtime = (runtime_root / rel).resolve()
        if not model.is_relative_to(model_root.resolve()) or not runtime.is_relative_to(runtime_root.resolve()):
            raise ValueError("source path escapes checkout")
        if not model.is_file() or not runtime.is_file():
            raise ValueError(f"required source missing: {rel}")
        model_sha = digest(model)
        runtime_sha = digest(runtime)
        rows.append({
            "path": rel,
            "model_sha256": model_sha,
            "runtime_sha256": runtime_sha,
            "byte_identical": model_sha == runtime_sha,
        })
    return rows


def model_rig_state(model_root: Path) -> dict:
    lock_path = model_root / MODEL_RIG_LOCK
    if not lock_path.is_file():
        raise ValueError("model rev2c skeleton-motion lock missing")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    rig = lock.get("rig", {})
    payload_ref = rig.get("payload", {})
    payload_path = model_root / str(payload_ref.get("path", ""))
    if not payload_path.is_file() or digest(payload_path) != payload_ref.get("sha256"):
        raise ValueError("model rev2c rig payload bytes differ")
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    if (
        payload.get("identity") != rig.get("identity")
        or payload.get("bone_count") != rig.get("bone_count")
        or payload.get("rig_structure_sha256") != rig.get("rig_structure_sha256")
    ):
        raise ValueError("model rev2c rig lock/payload identity differs")
    return {
        "identity": rig.get("identity"),
        "revision": rig.get("revision"),
        "rig_structure_sha256": rig.get("rig_structure_sha256"),
        "bone_count": rig.get("bone_count"),
        "deform_bone_count": rig.get("deform_bone_count"),
        "lock_path": MODEL_RIG_LOCK,
        "lock_sha256": digest(lock_path),
        "payload_path": payload_ref.get("path"),
        "payload_sha256": payload_ref.get("sha256"),
    }


def runtime_rig_state(runtime_root: Path, expected_model_rig: dict | None = None) -> dict:
    contract_path = runtime_root / "CANONICAL_V4_RUNTIME_CONTRACT.json"
    skeleton_path = runtime_root / "src/rig/skeleton.ts"
    if not contract_path.is_file() or not skeleton_path.is_file():
        raise ValueError("runtime rig contract/source missing")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    skeleton = skeleton_path.read_text(encoding="utf-8")
    mode = contract.get("mode")
    imports_v4 = bool(re.search(
        r"import\s*\{\s*HGPT_CANONICAL_V4_ORIGINAL_BONES\s*\}\s*from\s*['\"]\.\/canonicalV4Original['\"]",
        skeleton,
    ))
    constructor_v4_default = bool(re.search(
        r"constructor\(definitions:\s*BoneDefinition\[\]\s*=\s*HGPT_CANONICAL_V4_ORIGINAL_BONES\)",
        skeleton,
    ))
    canonical_uses_default = bool(re.search(
        r"export\s+const\s+canonicalSkeleton\s*=\s*new\s+Skeleton\(\s*\)",
        skeleton,
    ))
    if mode == "v4_active" and not (imports_v4 and constructor_v4_default and canonical_uses_default):
        raise ValueError("runtime contract says v4_active but skeleton source is not v4-default")
    declared_revision = contract.get("rig_revision")
    declared_structure = contract.get("rig_structure_sha256")
    declared_bone_count = contract.get("bone_count")
    rev2c_identity_confirmed = False
    if expected_model_rig is not None:
        rev2c_identity_confirmed = (
            contract.get("rig_identity") == expected_model_rig.get("identity")
            and declared_revision == expected_model_rig.get("revision")
            and declared_structure == expected_model_rig.get("rig_structure_sha256")
            and declared_bone_count == expected_model_rig.get("bone_count")
        )
    return {
        "contract_mode": mode,
        "contract_sha256": digest(contract_path),
        "skeleton_sha256": digest(skeleton_path),
        "imports_v4": imports_v4,
        "constructor_v4_default": constructor_v4_default,
        "canonical_uses_default": canonical_uses_default,
        "v4_default_confirmed": mode == "v4_active" and imports_v4 and constructor_v4_default and canonical_uses_default,
        "declared_rig_identity": contract.get("rig_identity"),
        "declared_rig_revision": declared_revision,
        "declared_rig_structure_sha256": declared_structure,
        "declared_bone_count": declared_bone_count,
        "rev2c_identity_confirmed": rev2c_identity_confirmed,
    }


def handoff_checkpoint(runtime_root: Path) -> dict:
    path = runtime_root / "docs/CURRENT_HANDOFF.md"
    if not path.is_file():
        raise ValueError("runtime CURRENT_HANDOFF missing")
    body = path.read_text(encoding="utf-8")
    match = re.search(
        r"Latest fully verified implementation checkpoint:\s*\n?\x60?([0-9a-f]{40})",
        body,
    )
    return {
        "path": "docs/CURRENT_HANDOFF.md",
        "sha256": digest(path),
        "declared_last_fully_verified_checkpoint": match.group(1) if match else None,
        "contains_old_v3_default_text": "accepted v3 humanoid remains the live" in body,
    }


def known_ci_snapshot(contract: dict, runtime_head: str) -> dict:
    snap = contract.get("discovery_snapshot", {})
    if runtime_head != snap.get("runtime_head"):
        return {
            "head_matches_snapshot": False,
            "known_green": False,
            "status": "UNKNOWN_FOR_NEW_HEAD",
            "reason": "Runtime HEAD changed since the prepared discovery snapshot; exact-SHA CI must be re-read.",
        }
    run = snap.get("latest_standalone_run", {})
    browser = snap.get("browser_viewport_smoke", {})
    return {
        "head_matches_snapshot": True,
        "known_green": run.get("conclusion") == "success" and browser.get("conclusion") == "success",
        "status": "KNOWN_SNAPSHOT",
        "standalone_run": run,
        "browser_viewport_smoke": browser,
    }


def build_discovery(
    model_root: Path,
    runtime_root: Path,
    contract: dict,
    *,
    check_git: bool = True,
    check_remote: bool = True,
) -> dict:
    model_root = model_root.resolve()
    runtime_root = runtime_root.resolve()
    spec = json.loads((model_root / CONTACT_SPEC).read_text(encoding="utf-8"))

    if contract.get("production_approved") is not False or contract.get("phase_complete") is not False:
        raise ValueError("runtime discovery contract cannot claim approval or phase completion")

    model_state = (
        repository_state(model_root, contract["model_branch"], check_remote)
        if check_git else
        {"root": str(model_root), "branch": contract["model_branch"], "head": None, "remote_head": None, "clean": None}
    )
    runtime_state = (
        repository_state(runtime_root, contract["runtime_authority"]["active_branch"], check_remote)
        if check_git else
        {"root": str(runtime_root), "branch": contract["runtime_authority"]["active_branch"], "head": contract["discovery_snapshot"]["runtime_head"], "remote_head": None, "clean": None}
    )

    semantic = verify_bridge(runtime_root, spec)
    if semantic.get("source_bridge_status") != contract["contact_bridge"]["required_semantic_result"]:
        raise ValueError("runtime contact semantics did not satisfy Stage-9 bridge")
    byte_rows = compare_source_bytes(model_root, runtime_root, contract["contact_bridge"]["source_paths"])
    model_rig = model_rig_state(model_root)
    rig = runtime_rig_state(runtime_root, model_rig)
    handoff = handoff_checkpoint(runtime_root)
    ci = known_ci_snapshot(contract, runtime_state["head"])

    blockers = []
    if not rig["v4_default_confirmed"]:
        blockers.append("canonical v4 is not confirmed as the runtime default")
    if not rig["rev2c_identity_confirmed"]:
        blockers.append(
            "runtime canonical v4 does not declare the exact locked rev2c rig identity "
            f"({model_rig['bone_count']} bones, {model_rig['rig_structure_sha256'][:12]}...)"
        )
    if not ci["known_green"]:
        blockers.append("standalone verification and browser smoke are not green on this exact runtime HEAD")
    blockers.extend([
        "Phase 9 final production deformation evidence is not supplied to this discovery tool",
        "final bare/dressed production asset hashes are not supplied to this discovery tool",
        "real runtime exercise/contact capture has not been executed",
        "export/reimport round-trip evidence has not been executed",
    ])

    result = {
        "schema_version": 1,
        "status": "DISCOVERY_ONLY",
        "phase_complete": False,
        "production_approved": False,
        "runtime_execution_permitted": False,
        "model_checkout": model_state,
        "runtime_checkout": runtime_state,
        "model_rig": model_rig,
        "runtime_rig": rig,
        "runtime_handoff": handoff,
        "contact_semantics": {
            "verified": True,
            "runtime_executed": False,
            "source_files": semantic["source_files"],
            "scenarios": semantic["scenarios"],
        },
        "cross_branch_source_comparison": byte_rows,
        "ci": ci,
        "integration_ready": len(blockers) == 0,
        "blockers": blockers,
        "required_future_evidence": contract.get("preintegration_requirements", []),
        "limits": [
            "Read-only source discovery/comparison only.",
            "Semantic compatibility does not prove solver behaviour, contact quality, smoothness, asset suitability or export round-trip.",
            "Never merge the model branch wholesale into the runtime branch.",
        ],
    }
    ensure_finite(result)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runtime-root", type=Path, required=True)
    ap.add_argument("--json-out", type=Path, required=True)
    args = ap.parse_args()
    try:
        contract_path = ROOT / CONTRACT
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        out = args.json_out.resolve()
        if not out.is_relative_to(ROOT.resolve()):
            raise ValueError("output must remain inside model repository")
        if out.exists():
            raise ValueError("output collision; preserve existing discovery evidence")
        report = build_discovery(ROOT, args.runtime_root, contract)
        report.update({
            "discovery_contract": {"path": CONTRACT, "sha256": digest(contract_path)},
            "contact_bridge_spec": {"path": CONTACT_SPEC, "sha256": digest(ROOT / CONTACT_SPEC)},
            "verifier": {"path": HELPER, "sha256": digest(ROOT / HELPER)},
            "generated_utc": datetime.now(timezone.utc).isoformat(),
        })
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(report, indent=2) + "\n")
        print("RUNTIME DISCOVERY COMPLETE — DISCOVERY_ONLY; integration_ready:", report["integration_ready"])
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print("STOP — " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
