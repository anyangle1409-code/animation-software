#!/usr/bin/env python3
"""Read-only anatomical ↔ runtime side-binding audit.

Uses a003 measured bilateral bone endpoints and the frozen 67-bone runtime
geometry. Reporting a mismatch is NOT authority to rename bones or change
pose conventions. No Blender scene, mesh, rig, canonical anatomy or alias is
modified by this tool.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANATOMY = "ORIGINAL_V1_WORK/anatomy/"
SOURCE = {
    "fitted_skeleton": ANATOMY + "character_fit_r95_a003.json",
    "runtime_skeleton": "ORIGINAL_V1_WORK/hgpt_canonical_v4_original_rev2c.json",
    "alias_inventory": ANATOMY + "adult_bone_blender_aliases_206.json",
}
# Independent bilaterally represented gross segments; not soft-tissue surfaces.
PROBES = (("clavicle", "clavicle"), ("humerus", "upperarm"), ("femur", "thigh"))
AUDIT_WORLD = "+Z up; character faces -Y; anatomical LEFT = +X"
RUNTIME_WORLD = "project_x_right_y_up_z_forward"


def vector(x):
    if not isinstance(x, list) or len(x) != 3 or any(
        isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
        for v in x
    ):
        raise ValueError("Expected a finite 3D coordinate")
    return tuple(float(v) for v in x)


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1],
            a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


def convert_audit_to_runtime(v):
    """Rigid proper rotation: audit +Z up/-Y forward -> runtime +Y up/+Z forward."""
    x, y, z = vector(list(v))
    return (x, z, -y)


def signed_lateral(v, lateral):
    return sum(x*y for x, y in zip(v, lateral))


def midpoint(a, b):
    return tuple((x+y)*0.5 for x, y in zip(a, b))


def bone_midpoint(bone, a, c):
    return midpoint(vector(bone[a]), vector(bone[c]))


def validate_frame(fit, runtime):
    convention = fit.get("conventions", {})
    if AUDIT_WORLD not in convention.get("world", ""):
        raise ValueError("Unrecognized fitted anatomical frame: manual review required")
    if convention.get("runtime_side_binding") != {"left": "_r", "right": "_l"}:
        raise ValueError("Source-recorded runtime binding changed: manual review required")
    if runtime.get("coordinate_system") != RUNTIME_WORLD:
        raise ValueError("Unrecognized runtime frame: manual review required")
    audit_lateral = cross((0, 0, 1), (0, -1, 0))
    runtime_lateral = cross((0, 1, 0), (0, 0, 1))
    if convert_audit_to_runtime(list(audit_lateral)) != runtime_lateral:
        raise ValueError("Frame transform reverses chirality")
    return audit_lateral, runtime_lateral


def inspect(fit, runtime, inventory):
    al, rl = validate_frame(fit, runtime)
    fit_bones, runtime_bones = fit["bones"], {b["name"]: b for b in runtime["bones"]}
    aliases = {a["anatomical_id"]: a for a in inventory["aliases"]}
    if len(runtime_bones) != len(runtime["bones"]) or len(aliases) != len(inventory["aliases"]):
        raise ValueError("Duplicate bone / alias identity")
    probes, issues = [], []
    for anatomical, rigstem in PROBES:
        left, right = fit_bones[anatomical+"_left"], fit_bones[anatomical+"_right"]
        lp = convert_audit_to_runtime(bone_midpoint(left, "head_m", "tail_m"))
        rp = convert_audit_to_runtime(bone_midpoint(right, "head_m", "tail_m"))
        for side, sign, fitpos in (("left", 1, lp), ("right", -1, rp)):
            # Bilateral centre removes global shift; projected lateral must be outboard.
            relative = tuple(a-b for a,b in zip(fitpos, midpoint(lp,rp)))
            if sign * signed_lateral(relative, rl) < 0.01:
                raise ValueError("Anatomical side not established for " + anatomical + "_" + side)
            anatom_id = anatomical+"_"+side
            alias = aliases[anatom_id]["current_rig"]
            if not isinstance(alias,list) or len(alias)!=1:
                raise ValueError("Expected sole current-rig alias for "+anatom_id)
            observed = alias[0]
            expected_side = "r" if side=="left" else "l"
            expected = rigstem + "_" + expected_side
            if expected not in runtime_bones or observed not in runtime_bones:
                raise ValueError("Missing runtime side counterpart for "+anatom_id)
            expected_pos = bone_midpoint(runtime_bones[expected], "head", "tail")
            observed_pos = bone_midpoint(runtime_bones[observed], "head", "tail")
            if sign * signed_lateral(expected_pos, rl) < 0.01:
                raise ValueError("Runtime orientation assumption failed for "+expected)
            if sign * signed_lateral(observed_pos, rl) > 0.0:
                outcome = "SAME_ANATOMICAL_SIDE"
            else:
                outcome = "CROSSED_ANATOMICAL_SIDE"
                issues.append(anatom_id)
            probes.append({
                "anatomical_id": anatom_id, "stored_rig_alias": observed,
                "geometrically_side_matching_rig_bone": expected,
                "fitted_lateral_m": round(signed_lateral(fitpos,rl), 6),
                "runtime_stored_alias_lateral_m": round(signed_lateral(observed_pos,rl), 6),
                "runtime_expected_lateral_m": round(signed_lateral(expected_pos,rl), 6),
                "finding": outcome,
            })
    # Unsupported, grouped, or collapsed aliases do not become "correct" by assumption.
    return {
        "schema_version": 1,
        "scope": "Read-only coordinate/side audit; three gross bilateral anchors; no bone-shape acceptance",
        "frame": {"fitted": fit["conventions"]["world"], "runtime": runtime["coordinate_system"],
                  "audit_to_runtime": "(x,y,z) -> (x,z,-y)", "proper_rotation": True,
                  "lateral_axis_in_both_frames": list(rl)},
        "anchors_compared": len(probes), "crossed_aliases": sorted(issues),
        "crossed_count": len(issues), "probes": probes,
        "status": "BLOCK_RUNTIME_SIDE_BINDING" if issues else "EVIDENCE_ONLY_OWNER_DECISION_PENDING",
        "owner_approval": False, "canonical_promotion": False, "runtime_mapping_changed": False,
        "remaining_limits": [
            "Only three independent gross bilateral pairs establish side; no claim about all 206 bone geometries.",
            "This does not prove the scene's mesh normals, skinning, wrist handedness or movement under load.",
            "Changing aliases without also auditing pose-driver side commands may make movements wrong.",
            "The r95 a003 and frozen runtime revision refer to distinct coordinate frames.",
        ],
    }


def from_repository(root=ROOT):
    raw = {k: (root/path).read_bytes() for k,path in SOURCE.items()}
    parsed = {k: json.loads(v) for k,v in raw.items()}
    result = inspect(parsed["fitted_skeleton"], parsed["runtime_skeleton"],
                     parsed["alias_inventory"])
    result["input_sha256"] = {SOURCE[k]:hashlib.sha256(v).hexdigest() for k,v in raw.items()}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="Write a diagnostic JSON outside canonical inputs")
    args = parser.parse_args()
    report = json.dumps(from_repository(), indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(report, encoding="utf-8")
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
