#!/usr/bin/env python3
"""Conservative whole-body Blender QA evidence intake, not anatomy certification.

Accept source-ID-grounded geometry and multi-pose measurements produced by
Blender. Inspect against the complete immutable 206 bone / 427 joint inventory,
flag incomplete coverage and negative surface clearances, and REFUSE automatic
canonical freeze or mesh-driven skeleton changes.

This is intentionally a read-only auditor of measured evidence. A local
Blender session must provide the real geometry and independent expert review.
It cannot establish bone surface correctness from labelled objects or JSON.
"""
import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ANATOMY = REPO / "ORIGINAL_V1_WORK" / "anatomy"
SOURCE_BONES = ANATOMY / "adult_bone_inventory_206.json"
SOURCE_JOINTS = ANATOMY / "adult_articulation_inventory.json"
FREEZE = ANATOMY / "canonical_freeze_readiness_v1.json"
BLOCKERS = ANATOMY / "audit" / "claude_anatomical_development_20261009" / "blocker_matrix_v1.json"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
ID = re.compile(r"^[A-Za-z0-9_.:-]{2,96}$")
MAX_POSES = 1000
MAX_MEASUREMENTS = 100_000

# Reviewed *technical* observation types; no declaration proves anatomy.
SURFACE_KINDS = {"blender_evaluated_mesh", "reference_mesh", "simplified_proxy"}
CLEARANCE_METHODS = {"mesh_bvh_signed", "mesh_bvh_unsigned", "control_stick_distance"}
FIT_FAMILIES = {
    "neutral", "overhead_push", "horizontal_push", "horizontal_pull",
    "vertical_pull", "squat", "hinge", "lunge", "carry", "rotation",
    "elbow_wrist", "gait", "ankle_foot", "neck_spine",
}


def _object(value, description):
    if not isinstance(value, dict):
        raise ValueError(description + " must be a JSON object")
    return value


def _sha(value, name, length=64):
    if not isinstance(value, str) or not (HEX64 if length == 64 else SHA40).fullmatch(value):
        raise ValueError(name + " requires an exact lowercase hex SHA")
    return value


def _num(value, name, *, lower=None, upper=None):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(name + " must be a finite real measurement")
    if lower is not None and value < lower:
        raise ValueError(name + " is below the physical review bound")
    if upper is not None and value > upper:
        raise ValueError(name + " is above the physical review bound")
    return float(value)


def _identity(raw, name):
    if not isinstance(raw, str) or ID.fullmatch(raw) is None:
        raise ValueError(name + " is invalid")
    return raw


def _bounds(bounds):
    if not isinstance(bounds, dict) or set(bounds) != {"min", "max"}:
        raise ValueError("3D world bounds require exact min/max positions")
    start, end = bounds["min"], bounds["max"]
    if not (isinstance(start, list) and isinstance(end, list) and
            len(start) == len(end) == 3):
        raise ValueError("3D bounds require three axes in metres")
    for k in range(3):
        a = _num(start[k], "world bounds", lower=-10, upper=10)
        b = _num(end[k], "world bounds", lower=-10, upper=10)
        if b < a:
            raise ValueError("mesh world bounds are reversed")


def source_context(bones, joints, freeze, blockers):
    ids = [b["id"] for b in bones["bones"]]
    js = [j["id"] for j in joints["articulations"]]
    if (len(ids) != 206 or len(set(ids)) != 206 or
            len(js) != 427 or len(set(js)) != 427):
        raise ValueError("canonical 206/427 source inventory has changed")
    bs = set(ids)
    ancillary = set(joints["additional_structures"])
    if len(ancillary) != 46 or bs & ancillary:
        raise ValueError("original non-206 cartilage/subcomponent inventory changed")
    for j in joints["articulations"]:
        if any(p not in bs and p not in ancillary for p in j["participants"]):
            raise ValueError("articulation inventory refers to unknown bone or ancillary cartilage")
    if freeze["region_counts"] != {"READY": 0, "PARTIAL": 9, "BLOCKED": 3}:
        raise ValueError("expected no-promoted baseline anatomy readiness changed")
    if not isinstance(blockers.get("blockers"), list) or len(blockers["blockers"]) != 11:
        raise ValueError("expected canonical blocker matrix changed; review required")
    return bs, set(js), {b["id"]: b["region"] for b in bones["bones"]}


def audit_measurements(report, bones, joints, freeze, blockers):
    """Fail closed for incorrect provenance and labels; never infer bone approval."""
    _object(report, "Blender QA report")
    all_bones, all_joints, regions = source_context(bones, joints, freeze, blockers)
    if report.get("schema_version") != 1 or report.get("kind") != "HGPT_BLENDER_206_BONE_QA_EXPORT":
        raise ValueError("unknown Blender anatomical measurement contract")
    src = _object(report.get("provenance"), "Blender source provenance")
    _sha(src.get("git_commit_sha"), "exact source git commit", 40)
    _sha(src.get("blender_scene_sha256"), "private Blender scene hash")
    _sha(src.get("bone_inventory_sha256"), "206-bone inventory provenance")
    _sha(src.get("joint_inventory_sha256"), "427-articulation inventory provenance")
    if (src["bone_inventory_sha256"] !=
            hashlib.sha256(json.dumps(bones, sort_keys=True, separators=(",", ":")).encode()).hexdigest() or
            src["joint_inventory_sha256"] !=
            hashlib.sha256(json.dumps(joints, sort_keys=True, separators=(",", ":")).encode()).hexdigest()):
        raise ValueError("Blender report inventories do not match live 206/427 original sources")
    if (src.get("world_unit") != "metres" or
            src.get("anatomical_label_basis") != "source_anatomical_bone_id" or
            src.get("scene_was_evaluated_by_bpy") is not True):
        raise ValueError("Blender world units, source-side semantics or bpy evaluation missing")
    if report.get("anatomical_identity_approved") is not False or report.get("canonical_promotion_allowed") is not False:
        raise ValueError("Blender measurement data cannot approve anatomical geometry")
    recorded = report.get("bone_surfaces")
    poses = report.get("poses")
    if not isinstance(recorded, list) or not isinstance(poses, list):
        raise ValueError("Blender QA export requires measured surfaces and poses")
    if len(recorded) > 206 or not 1 <= len(poses) <= MAX_POSES:
        raise ValueError("bone/pose measurement count exceeds expected bounds")
    found = {}
    kind_counts = Counter()
    for sample in recorded:
        _object(sample, "bone surface")
        sid = _identity(sample.get("bone_id"), "source bone")
        if sid not in all_bones or sid in found:
            raise ValueError("unknown or duplicate 206-source bone in Blender export")
        _identity(sample.get("object_name"), "Blender object")
        kind = sample.get("surface_kind")
        if kind not in SURFACE_KINDS:
            raise ValueError("unsupported geometry observation kind")
        _sha(sample.get("evaluated_vertex_buffer_sha256"), "measured mesh buffer SHA")
        if type(sample.get("vertex_count")) is not int or sample["vertex_count"] < 3:
            raise ValueError("bone surface vertex count invalid")
        if type(sample.get("triangle_count")) is not int or sample["triangle_count"] < 1:
            raise ValueError("bone surface triangle count invalid")
        _bounds(sample.get("world_bounds_m"))
        if type(sample.get("watertight_mesh")) is not bool:
            raise ValueError("source mesh manifold test not performed")
        if sample.get("bone_anatomy_expert_verified") is not False:
            raise ValueError("automated bone-name or mesh shape cannot declare expert verification")
        found[sid] = sample
        kind_counts[kind] += 1
    if not found:
        raise ValueError("empty Blender source bone surface measurement")

    seen_poses = set()
    family_counts = Counter()
    measured_joints = set()
    penetrations = []
    dubious_signs = []
    missing_surface_pairs = []
    measurement_count = 0
    for pose in poses:
        _object(pose, "Blender frame")
        pose_id = _identity(pose.get("pose_id"), "source measured pose")
        if pose_id in seen_poses:
            raise ValueError("duplicate pose snapshot")
        seen_poses.add(pose_id)
        family = pose.get("movement_family")
        if family not in FIT_FAMILIES:
            raise ValueError("unknown anatomical exercise/movement family")
        frame = pose.get("frame")
        if type(frame) is not int or not 0 <= frame <= 1_000_000:
            raise ValueError("Blender measured frame must be nonnegative")
        family_counts[family] += 1
        observations = pose.get("joint_surface_measurements")
        if not isinstance(observations, list) or len(observations) > 427:
            raise ValueError("pose joint measurements absent or excessive")
        pair_ids = set()
        for m in observations:
            _object(m, "joint measurement")
            joint = _identity(m.get("articulation_id"), "canonical 427 articulation")
            if joint not in all_joints or joint in pair_ids:
                raise ValueError("unrecognized or duplicate articulation in source pose")
            pair_ids.add(joint)
            measured_joints.add(joint)
            method = m.get("method")
            if method not in CLEARANCE_METHODS:
                raise ValueError("unknown clearance method or signed-distance semantics")
            signed = method == "mesh_bvh_signed"
            gap = _num(m.get("separation_mm"), "source-measured joint distance", lower=-1000, upper=1000)
            # Negative gap is NOT trustworthy unless both *bone surfaces*
            # are watertight, bpy-evaluated and signed method is actually used.
            original = next(j for j in joints["articulations"] if j["id"] == joint)
            participants = [p for p in original["participants"] if p in all_bones]
            measured_ends = [found.get(p) for p in participants]
            # Many canonical joints include actual cartilage, TFCC, or fused
            # subcomponents NOT counted among the conventional 206 bones.
            # A pair of bone proxies cannot certify a cartilage-inclusive gap.
            geometry_ready = (len(original["participants"]) == 2 and
                              len(measured_ends) == 2 and
                              all(p is not None and p["surface_kind"] == "blender_evaluated_mesh"
                                  and p["watertight_mesh"] for p in measured_ends))
            if not geometry_ready:
                missing_surface_pairs.append({"pose": pose_id, "joint": joint})
            if gap < 0:
                if signed and geometry_ready:
                    penetrations.append({"pose": pose_id, "joint": joint,
                                         "signed_separation_mm": gap,
                                         "interpretation": "requires anatomical contact classification"})
                else:
                    dubious_signs.append({"pose": pose_id, "joint": joint,
                                          "reported_mm": gap,
                                          "method": method,
                                          "interpretation": "not a defensible penetration sign"})
            if m.get("bone_contact_anatomically_approved") is not False:
                raise ValueError("measured source joint cannot self-approve its anatomical contact")
            measurement_count += 1
            if measurement_count > MAX_MEASUREMENTS:
                raise ValueError("measurement intake exceeds audited budget")

    coverage_by_source_region = defaultdict(lambda: {"observed_bones": 0, "inventory_bones": 0})
    for sid, region in regions.items():
        coverage_by_source_region[region]["inventory_bones"] += 1
        if sid in found:
            coverage_by_source_region[region]["observed_bones"] += 1
    region_status = {k: v["readiness"] for k, v in freeze["regions"].items()}
    return {
        "kind": "BLENDER_SOURCE_BONE_JOINT_QA_COVERAGE_NOT_ANATOMICAL_APPROVAL",
        "inventory_sha256_matches": True,
        "reported_git_commit": src["git_commit_sha"],
        "reported_scene_sha256": src["blender_scene_sha256"],
        "full_original_bone_inventory_count": len(all_bones),
        "observed_source_bones": len(found),
        "missing_source_bones": sorted(all_bones - set(found)),
        "bone_surface_types": dict(sorted(kind_counts.items())),
        "bone_coverage_by_inventory_region": dict(sorted(coverage_by_source_region.items())),
        "original_articulation_inventory_count": len(all_joints),
        "observed_distinct_articulations": len(measured_joints),
        "missing_articulation_ids": sorted(all_joints - measured_joints),
        "poses_measured": len(seen_poses),
        "movement_families_observed": dict(sorted(family_counts.items())),
        "not_sampled_movement_families": sorted(FIT_FAMILIES - set(family_counts)),
        "total_joint_measurements": measurement_count,
        "qualified_signed_negative_bone_clearances_review_required": penetrations,
        "unqualified_negative_distance_claims": dubious_signs,
        "joint_measurements_without_qualified_closed_bone_surfaces": missing_surface_pairs,
        "remaining_11_source_blocker_ids": [b["id"] for b in blockers["blockers"]],
        "actual_anatomical_readiness_by_region": region_status,
        "actual_readiness_counts_unchanged": dict(freeze["region_counts"]),
        "source_mesh_refitting_authorized": False,
        "bone_identity_independently_verified": False,
        "anatomical_joint_contact_verified": False,
        "production_or_canonical_promotion_allowed": False,
        "interpretation": (
            "This report checks IDs, geometry-method semantics, source provenance "
            "and multi-pose measurement coverage ONLY. Bpy-reported geometry is "
            "not independently verified anatomical bone truth. Independent "
            "literature, contact classification and qualified anatomical "
            "review are required before any canonical readiness change."
        ),
    }


def read_source_and_audit(raw, root=ANATOMY):
    path = Path(root)
    bones = json.loads((path / "adult_bone_inventory_206.json").read_text())
    joints = json.loads((path / "adult_articulation_inventory.json").read_text())
    freeze = json.loads((path / "canonical_freeze_readiness_v1.json").read_text())
    blockers = json.loads((path / "audit" / "claude_anatomical_development_20261009" /
                           "blocker_matrix_v1.json").read_text())
    return audit_measurements(raw, bones, joints, freeze, blockers)



def verify_scene_bytes(local_scene_path, report):
    """Independently hash the precise private .blend file used by a bpy export.

    This verifies scene-file provenance only, NOT that the reported mesh
    measurements were truthfully produced by Blender or are correct anatomy.
    """
    expected = _sha(_object(report.get("provenance"), "Blender provenance").get(
        "blender_scene_sha256"), "Blender scene hash")
    p = Path(local_scene_path)
    if not p.is_file() or p.suffix.lower() != ".blend":
        raise ValueError("independent original Blender .blend file is required")
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    if h.hexdigest() != expected:
        raise ValueError("original Blender .blend bytes changed; scene SHA mismatch")
    return True


def report_schema_template(bone_inventory_sha256, articulation_sha256):
    """Structurally valid EMPTY guide, explicitly unverified until filled by bpy."""
    return {
        "schema_version": 1,
        "kind": "HGPT_BLENDER_206_BONE_QA_EXPORT",
        "provenance": {
            "git_commit_sha": "<40-lowercase-hex-git-SHA>",
            "blender_scene_sha256": "<SHA256-of-actual-private-blend>",
            "bone_inventory_sha256": bone_inventory_sha256,
            "joint_inventory_sha256": articulation_sha256,
            "world_unit": "metres",
            "anatomical_label_basis": "source_anatomical_bone_id",
            "scene_was_evaluated_by_bpy": False,
        },
        "anatomical_identity_approved": False,
        "canonical_promotion_allowed": False,
        "bone_surfaces": [],
        "poses": [],
        "important": (
            "Guide only. Fill from real Blender-evaluated anatomical bone "
            "surfaces and original source-named joint clearances. Never mark "
            "bpy=true or insert measurements without Blender execution. "
            "Cartilage/TFCC/sesamoid extras are not among the conventional 206."
        ),
    }



def private_review_output(raw_path):
    """Enforce NEW private output outside any Git repository/worktree.

    Standalone on the anatomical audit baseline; depends on no CT PR module.
    """
    proposed = Path(raw_path).expanduser()
    if proposed.is_symlink():
        raise ValueError("private QA output must not be a symlink")
    resolved = proposed.resolve(strict=False)
    if resolved == REPO or REPO in resolved.parents:
        raise ValueError("private Blender report must never be placed in source Git worktree")
    for parent in (resolved.parent, *resolved.parents):
        if (parent / ".git").exists():
            raise ValueError("QA measurements must remain outside ANY Git worktree")
    return resolved


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", help="private measured JSON from Blender bpy")
    p.add_argument("--out", required=True, help="new private QA assessment JSON outside Git worktrees")
    p.add_argument("--scene-file", help="EXACT local .blend file to independently verify SHA-256")
    p.add_argument("--template-only", action="store_true",
                   help="emit an EMPTY, safely unverified source-pinned report guide without Blender")
    args = p.parse_args()
    output = private_review_output(args.out)
    if output.exists() or output.suffix != ".json":
        raise ValueError("refuse overwrite or non-JSON Blender assessment path")
    if args.template_only:
        if args.input is not None or args.scene_file is not None:
            raise ValueError("template mode must never consume or claim live Blender geometry")
        bones = json.loads(SOURCE_BONES.read_text())
        joints = json.loads(SOURCE_JOINTS.read_text())
        result = report_schema_template(
            hashlib.sha256(json.dumps(bones, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            hashlib.sha256(json.dumps(joints, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        )
    else:
        if not args.input or not args.scene_file:
            raise ValueError("a real bpy report AND the exact private .blend file are required")
        raw = json.loads(Path(args.input).read_text())
        verify_scene_bytes(args.scene_file, raw)
        result = read_source_and_audit(raw)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf8") as fp:
        json.dump(result, fp, sort_keys=True, indent=2)
        fp.write("\n")
    if args.template_only:
        print("Emitted EMPTY source-pinned Blender QA report template. No bpy data or anatomy approved.")
        return
    print(json.dumps({
        "bone_observations": result["observed_source_bones"],
        "articulations_covered": result["observed_distinct_articulations"],
        "movement_families": result["movement_families_observed"],
        "unreviewed_negative_clearances": len(
            result["qualified_signed_negative_bone_clearances_review_required"]),
        "canonical_promotion_allowed": False,
    }, indent=2))


if __name__ == "__main__":
    main()
