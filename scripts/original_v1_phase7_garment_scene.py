#!/usr/bin/env python3
"""Verify Phase 7 garment scene state plus explicit clean-room authoring history.

Evidence-only. Does not model clothing, classify dressed contact, or complete Phase 7.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

from original_v1_production_control import ROOT, digest, ensure_finite
from original_v1_locked_rig import load_locked_rig
from verify_original_v1_production_promotion import safe_path

TEMPLATE = "ORIGINAL_V1_PHASE7_GARMENT_AUTHORING_TEMPLATE.json"
HELPER = "scripts/original_v1_phase7_garment_scene.py"
EXPECTED_BODY = "HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"
EXPECTED_GARMENT = "HGPT_ORIGINAL_V1_SHORTS_CANDIDATE"
EXPECTED_RIG = "HGPT_CANONICAL_V4_ORIGINAL"
RIG_LOCK = "ORIGINAL_V1_WORK/SKELETON_MOTION_LOCK_rev2_forearm_twist_only.json"


def locked_rig_contract() -> dict:
    """Backward-compatible Phase 7 view of the single shared rev2c lock."""
    rig = load_locked_rig(ROOT)
    return {
        "name": rig["object_name"],
        "identity": rig["identity"],
        "revision": rig["revision"],
        "rig_structure_sha256": rig["rig_structure_sha256"],
        "bone_count": rig["bone_count"],
        "deform_bone_count": rig["deform_bone_count"],
        "bones": rig["bones"],
        "lock_path": rig["lock"]["path"],
        "lock_sha256": rig["lock"]["sha256"],
        "payload_path": rig["payload"]["path"],
        "payload_sha256": rig["payload"]["sha256"],
    }

def file_ref(root: Path, ref: dict, label: str) -> Path:
    if not isinstance(ref, dict) or not ref.get("path") or not re.fullmatch(r"[0-9a-f]{64}", str(ref.get("sha256", ""))):
        raise ValueError(f"{label} path/SHA-256 required")
    p = safe_path(root, ref["path"])
    if not p.is_file() or digest(p) != ref["sha256"]:
        raise ValueError(f"{label} bytes differ")
    return p


def validate_operation_history(root: Path, record: dict, candidate_sha: str) -> list[str]:
    issues = []
    if record.get("schema_version") != 1 or record.get("status") != "AUTHORING_EVIDENCE_COMPLETE":
        issues.append("garment authoring record identity/status differs")
    if record.get("phase") != 7 or record.get("phase_complete") is not False or record.get("production_approved") is not False:
        issues.append("garment authoring record cannot claim phase/production completion")
    if record.get("candidate_sha256") != candidate_sha:
        issues.append("garment authoring record candidate differs")
    if record.get("garment_object") != EXPECTED_GARMENT:
        issues.append("garment object identity differs")

    provenance = record.get("provenance")
    required = {
        "independent_authorship": True,
        "legacy_geometry_imported": False,
        "third_party_geometry_imported": False,
        "transferred_weights_or_bind_data": False,
        "external_texture_or_material_content": False,
    }
    if not isinstance(provenance, dict):
        issues.append("garment provenance record missing")
    else:
        for key, expected in required.items():
            if provenance.get(key) is not expected:
                issues.append(f"garment provenance {key} must be {expected}")
        if not isinstance(provenance.get("starting_source"), str) or not provenance["starting_source"].strip():
            issues.append("garment provenance starting_source required")

    template = json.loads((ROOT / TEMPLATE).read_text(encoding="utf-8"))
    required_fields = template["required_operation_fields"]
    operations = record.get("operation_history")
    if not isinstance(operations, list) or not operations:
        return list(dict.fromkeys(issues + ["nonempty garment operation history required"]))
    ids = [row.get("id") for row in operations if isinstance(row, dict)]
    if len(ids) != len(operations) or any(not isinstance(x, str) or not x.strip() for x in ids) or len(ids) != len(set(ids)):
        issues.append("garment operation IDs missing/duplicated")
    previous_output = None
    for index, row in enumerate(operations):
        if not isinstance(row, dict) or any(field not in row for field in required_fields):
            issues.append(f"garment operation {index}: required fields missing")
            continue
        for field in ("description", "tool_or_method", "scope"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                issues.append(f"garment operation {row.get('id')}: {field} missing")
        inp = row.get("input_candidate_sha256")
        out = row.get("output_candidate_sha256")
        if not re.fullmatch(r"[0-9a-f]{64}", str(inp or "")) or not re.fullmatch(r"[0-9a-f]{64}", str(out or "")):
            issues.append(f"garment operation {row.get('id')}: candidate SHA invalid")
        if previous_output is not None and inp != previous_output:
            issues.append(f"garment operation {row.get('id')}: operation chain is discontinuous")
        previous_output = out
        if type(row.get("topology_changed")) is not bool or type(row.get("weights_changed")) is not bool:
            issues.append(f"garment operation {row.get('id')}: topology/weight change flags required")
        try:
            refs = row.get("evidence")
            if not isinstance(refs, list) or not refs:
                raise ValueError("operation evidence required")
            seen = set()
            for ref in refs:
                p = file_ref(root, ref, f"operation {row.get('id')} evidence")
                key = (p.relative_to(root.resolve()).as_posix(), ref["sha256"])
                if key in seen:
                    raise ValueError("duplicate operation evidence")
                seen.add(key)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            issues.append(str(exc))
    if previous_output != candidate_sha:
        issues.append("final garment operation output does not equal candidate SHA")
    return list(dict.fromkeys(issues))


def external_refs(obj: dict) -> list[str]:
    refs = []
    if obj.get("object_library"):
        refs.append("object_library:" + str(obj["object_library"]))
    if obj.get("data_library"):
        refs.append("data_library:" + str(obj["data_library"]))
    for row in obj.get("materials", []):
        if isinstance(row, dict) and row.get("library"):
            refs.append("material_library:" + str(row["library"]))
    for row in obj.get("images", []):
        if isinstance(row, dict) and row.get("library"):
            refs.append("image_library:" + str(row["library"]))
    return refs


def modifier_coverage(obj: dict) -> list[str]:
    issues = []
    mods = obj.get("modifiers")
    if not isinstance(mods, list):
        return ["modifier inventory missing"]
    for mod in mods:
        if not isinstance(mod, dict) or not mod.get("name") or not mod.get("type") or not isinstance(mod.get("properties"), dict):
            issues.append("invalid modifier receipt")
            continue
        unsupported = mod.get("unsupported_properties")
        if not isinstance(unsupported, list):
            issues.append(f"{mod.get('name')}: unsupported-property inventory missing")
        elif unsupported:
            issues.append(f"{mod.get('name')}: {len(unsupported)} modifier properties unresolved")
    return issues


def verify_scene(root: Path, scene: dict, authoring: dict, raw_pair: dict, manifest: dict) -> dict:
    candidate = manifest.get("candidate_sha256")
    if not re.fullmatch(r"[0-9a-f]{64}", str(candidate or "")):
        raise ValueError("candidate manifest SHA invalid")
    for label, obj in (("scene", scene), ("raw pair", raw_pair)):
        if obj.get("candidate_sha256") != candidate:
            raise ValueError(f"{label} candidate differs")
        if obj.get("status") != "EVIDENCE_ONLY" or obj.get("phase_complete") is not False or obj.get("production_approved") is not False:
            raise ValueError(f"{label} status differs")
    locked = locked_rig_contract()
    expected_raw_lock = {
        "revision": locked["revision"],
        "rig_structure_sha256": locked["rig_structure_sha256"],
        "bone_count": locked["bone_count"],
        "deform_bone_count": locked["deform_bone_count"],
        "lock": {"path": locked["lock_path"], "sha256": locked["lock_sha256"]},
        "payload": {"path": locked["payload_path"], "sha256": locked["payload_sha256"]},
    }
    if raw_pair.get("locked_rig") != expected_raw_lock:
        raise ValueError("raw body/garment evidence locked rev2c identity differs")

    blockers = []
    if scene.get("rig_id") != locked["identity"]:
        blockers.append("locked rev2c rig identity missing")
    scene_rig = scene.get("rig", {})
    if scene_rig.get("name") != locked["name"]:
        blockers.append("locked rev2c rig object name differs")
    if scene_rig.get("bone_count") != locked["bone_count"] or scene_rig.get("deform_bone_count") != locked["deform_bone_count"]:
        blockers.append("locked rev2c rig bone counts differ")
    if scene_rig.get("bones") != locked["bones"]:
        blockers.append("locked rev2c rig hierarchy differs")
    if scene_rig.get("lock_revision") != locked["revision"] or scene_rig.get("rig_structure_sha256") != locked["rig_structure_sha256"]:
        blockers.append("locked rev2c rig revision/structure identity differs")
    body = scene.get("body", {})
    garment = scene.get("garment", {})
    if body.get("name") != EXPECTED_BODY or garment.get("name") != EXPECTED_GARMENT:
        blockers.append("body/garment object identity differs")
    if body.get("armature") != EXPECTED_RIG or garment.get("armature") != EXPECTED_RIG:
        blockers.append("body/garment armature binding differs")
    if scene.get("scene_linked_libraries"):
        blockers.append("scene contains linked external libraries")
    for label, obj in (("body", body), ("garment", garment)):
        for item in external_refs(obj):
            blockers.append(label + " external reference: " + item)
        blockers.extend(label + " " + issue for issue in modifier_coverage(obj))
        normal_state = obj.get("has_custom_normals")
        if normal_state == "UNAVAILABLE_IN_THIS_BLENDER_API":
            blockers.append(label + " custom-normal state unavailable")
        shape = obj.get("shape_keys")
        if not isinstance(shape, dict) or not isinstance(shape.get("key_blocks"), list) or not isinstance(shape.get("drivers"), list):
            blockers.append(label + " shape-key/driver inventory incomplete")
        if not isinstance(obj.get("vertex_groups"), list) or not isinstance(obj.get("attributes"), list):
            blockers.append(label + " group/attribute inventory incomplete")

    blockers.extend(validate_operation_history(root, authoring, candidate))

    result = {
        "schema_version": 1,
        "status": "EVIDENCE_ONLY",
        "phase_complete": False,
        "production_approved": False,
        "candidate_sha256": candidate,
        "garment_scene_status": "BLOCKED" if blockers else "EVIDENCE_COMPLETE",
        "blockers": list(dict.fromkeys(blockers)),
        "scene_summary": {
            "body_vertex_count": body.get("vertex_count"),
            "garment_vertex_count": garment.get("vertex_count"),
            "garment_face_count": garment.get("face_count"),
            "body_modifier_count": len(body.get("modifiers", [])) if isinstance(body.get("modifiers"), list) else None,
            "garment_modifier_count": len(garment.get("modifiers", [])) if isinstance(garment.get("modifiers"), list) else None,
            "garment_shape_key_count": len(garment.get("shape_keys", {}).get("key_blocks", [])) if isinstance(garment.get("shape_keys"), dict) else None,
        },
        "unresolved_phase7_domains": [
            "actual garment construction/modelling quality",
            "static dressed contact classification",
            "continuous dressed motion classification",
            "bare/dressed deformation equivalence",
            "owner dressed visual review",
        ],
        "limits": "Scene/provenance contract evidence only. Dressed deformation/contact and visual quality remain separate real evidence.",
    }
    ensure_finite(result)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scene-capture", type=Path, required=True)
    ap.add_argument("--authoring-record", type=Path, required=True)
    ap.add_argument("--raw-pair", type=Path, required=True)
    ap.add_argument("--candidate-manifest", type=Path, required=True)
    ap.add_argument("--json-out", type=Path, required=True)
    args = ap.parse_args()
    try:
        if args.json_out.exists():
            raise ValueError("Phase 7 scene output collision")
        loaded = []
        for path, label in (
            (args.scene_capture, "scene capture"),
            (args.authoring_record, "authoring record"),
            (args.raw_pair, "raw pair"),
            (args.candidate_manifest, "candidate manifest"),
        ):
            p = path.resolve()
            if not p.is_relative_to(ROOT.resolve()) or not p.is_file():
                raise ValueError(label + " missing/outside repository")
            data = json.loads(p.read_text(encoding="utf-8-sig"))
            ensure_finite(data)
            loaded.append((p, data))
        result = verify_scene(ROOT, loaded[0][1], loaded[1][1], loaded[2][1], loaded[3][1])
        result["source_evidence"] = [
            {"path": p.relative_to(ROOT).as_posix(), "sha256": digest(p)} for p, _ in loaded
        ]
        result["authoring_template"] = {"path": TEMPLATE, "sha256": digest(ROOT / TEMPLATE)}
        result["verifier"] = {"path": HELPER, "sha256": digest(ROOT / HELPER)}
        result["source_git_commit"] = subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
        result["generated_utc"] = datetime.now(timezone.utc).isoformat()
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print("PHASE 7 GARMENT SCENE", result["garment_scene_status"], "— evidence only")
        return 0 if result["garment_scene_status"] == "EVIDENCE_COMPLETE" else 1
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print("STOP — " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
