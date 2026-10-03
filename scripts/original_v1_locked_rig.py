#!/usr/bin/env python3
"""Shared fail-closed identity for the locked ORIGINAL-v1 rev2c skeleton.

Standard library only. This module does not edit Blender, assets, baselines or
production state. It verifies the committed skeleton-motion lock and payload and
returns the exact rig identity expected by later evidence tools.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = "ORIGINAL_V1_WORK/SKELETON_MOTION_LOCK_rev2_forearm_twist_only.json"
EXPECTED_OBJECT_NAME = "HGPT_CANONICAL_V4_ORIGINAL"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_locked_rig(root: Path = ROOT) -> dict:
    root = root.resolve()
    lock_path = (root / LOCK_PATH).resolve()
    if not lock_path.is_relative_to(root) or not lock_path.is_file():
        raise ValueError("locked rev2c skeleton-motion record missing")
    lock = json.loads(lock_path.read_text(encoding="utf-8-sig"))
    if lock.get("kind") != "SKELETON_MOTION_LOCK":
        raise ValueError("unexpected skeleton-motion lock kind")
    rig = lock.get("rig")
    if not isinstance(rig, dict):
        raise ValueError("skeleton-motion lock rig record missing")
    payload_ref = rig.get("payload")
    if not isinstance(payload_ref, dict) or not payload_ref.get("path") or not payload_ref.get("sha256"):
        raise ValueError("locked rig payload reference missing")
    payload_path = (root / payload_ref["path"]).resolve()
    if not payload_path.is_relative_to(root) or not payload_path.is_file():
        raise ValueError("locked rev2c payload missing/outside repository")
    if digest(payload_path) != payload_ref["sha256"]:
        raise ValueError("locked rev2c payload bytes differ")
    payload = json.loads(payload_path.read_text(encoding="utf-8-sig"))
    bones = payload.get("bones")
    if not isinstance(bones, list) or not bones:
        raise ValueError("locked rev2c payload bone list missing")
    hierarchy = sorted(
        [{"name": str(row["name"]), "parent": row.get("parent")} for row in bones],
        key=lambda row: row["name"],
    )
    names = [row["name"] for row in hierarchy]
    if len(names) != len(set(names)):
        raise ValueError("locked rev2c payload has duplicate bone names")
    if payload.get("identity") != rig.get("identity"):
        raise ValueError("locked rig/payload identity differs")
    if payload.get("rig_structure_sha256") != rig.get("rig_structure_sha256"):
        raise ValueError("locked rig/payload structure SHA differs")
    if payload.get("bone_count") != rig.get("bone_count") or len(bones) != rig.get("bone_count"):
        raise ValueError("locked rig/payload bone count differs")
    if not isinstance(rig.get("deform_bone_count"), int):
        raise ValueError("locked rig deform-bone count missing")
    return {
        "object_name": EXPECTED_OBJECT_NAME,
        "identity": rig["identity"],
        "revision": rig["revision"],
        "rig_structure_sha256": rig["rig_structure_sha256"],
        "bone_count": rig["bone_count"],
        "deform_bone_count": rig["deform_bone_count"],
        "bones": hierarchy,
        "lock": {"path": LOCK_PATH, "sha256": digest(lock_path)},
        "payload": {"path": payload_ref["path"], "sha256": payload_ref["sha256"]},
    }


def blender_armature_issues(armature, contract: dict) -> list[str]:
    """Inspect a Blender-like armature object without importing bpy."""
    issues: list[str] = []
    if armature is None or getattr(armature, "type", None) != "ARMATURE":
        return ["locked rev2c armature object missing"]
    if getattr(armature, "name", None) != contract["object_name"]:
        issues.append("locked rev2c armature object name differs")
    bones = list(getattr(getattr(armature, "data", None), "bones", []))
    if len(bones) != contract["bone_count"]:
        issues.append(
            f"locked rev2c bone count differs: {len(bones)} != {contract['bone_count']}"
        )
        return issues
    hierarchy = sorted(
        [
            {
                "name": str(getattr(bone, "name", "")),
                "parent": getattr(getattr(bone, "parent", None), "name", None),
            }
            for bone in bones
        ],
        key=lambda row: row["name"],
    )
    if hierarchy != contract["bones"]:
        issues.append("locked rev2c bone hierarchy differs")
    deform = sum(bool(getattr(bone, "use_deform", True)) for bone in bones)
    if deform != contract["deform_bone_count"]:
        issues.append(
            f"locked rev2c deform-bone count differs: {deform} != {contract['deform_bone_count']}"
        )
    return issues


if __name__ == "__main__":
    print(json.dumps(load_locked_rig(), indent=2))
