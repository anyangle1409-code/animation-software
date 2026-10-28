"""Read-only authored shoulder/lower-limb chain inventory, not anatomy."""
import argparse
import hashlib
import json
import math
import os
import re
import tempfile
from pathlib import Path

from compare_rig_axes import MODELS
from forearm_chain_readiness import load_native_evidence

JSON_NAME = "native_limb_chain_readiness.json"
MD_NAME = "native_limb_chain_readiness.md"
SHA256 = re.compile(r"[0-9a-f]{64}")
ABSENT_SEGMENT_TOKENS = ("patella", "talus", "calcaneus", "hindfoot", "midfoot", "forefoot")


def _finite3(value):
    return (isinstance(value, list) and len(value) == 3 and
            all(type(x) in (int, float) and math.isfinite(x) for x in value))


def _suffix_row(bones, suffix):
    names = {
        "clavicle": f"clavicle_{suffix}", "scapula": f"scapula_{suffix}",
        "upperarm": f"upperarm_{suffix}", "shoulder_cap": f"shoulder_cap_{suffix}",
        "thigh": f"thigh_{suffix}", "shin": f"shin_{suffix}",
        "foot": f"foot_{suffix}", "toe": f"toe_{suffix}",
        "hip_crease": f"hip_crease_{suffix}",
    }
    required = {"spine_03", "pelvis", *names.values()}
    missing = sorted(required - set(bones))
    if missing:
        raise ValueError("missing required authored chain controls: " + ", ".join(missing))
    parents = {
        names["clavicle"]: "spine_03", names["scapula"]: names["clavicle"],
        names["upperarm"]: names["scapula"], names["shoulder_cap"]: names["scapula"],
        names["thigh"]: "pelvis", names["shin"]: names["thigh"],
        names["foot"]: names["shin"], names["toe"]: names["foot"],
        names["hip_crease"]: "pelvis",
    }
    for name, parent in parents.items():
        if bones[name].get("parent") != parent:
            raise ValueError(f"unexpected authored hierarchy: {name} parent")
    for name in required:
        item = bones[name]
        if not _finite3(item.get("rest_head_body_local_m")) or not _finite3(item.get("rest_tail_body_local_m")):
            raise ValueError("nonfinite selected chain coordinates: " + name)
        if item.get("use_deform") is not True or not isinstance(item.get("pose_rotation_mode"), str):
            raise ValueError("selected chain control semantics changed: " + name)
        if item.get("pose_constraint_metadata") != []:
            raise ValueError("selected chain constraint metadata changed: " + name)
    return {
        "shoulder": ["spine_03", names["clavicle"], names["scapula"], names["upperarm"]],
        "shoulder_cap_authored_control": names["shoulder_cap"],
        "lower_limb": ["pelvis", names["thigh"], names["shin"], names["foot"], names["toe"]],
        "hip_crease_authored_control": names["hip_crease"],
        "anatomical_side_verified": False,
        "joint_centres_and_segment_frames_verified": False,
    }


def audit_loaded(docs, member_sha256):
    if set(docs) != set(MODELS) or set(member_sha256) != set(MODELS):
        raise ValueError("exact W8/V14/R120 evidence is required")
    if any(not isinstance(value, str) or not SHA256.fullmatch(value) for value in member_sha256.values()):
        raise ValueError("every consumed rig member requires a SHA256")
    rows, fingerprints = {}, {}
    for model in MODELS:
        items = docs[model].get("bones")
        if not isinstance(items, list) or not items:
            raise ValueError(model + ": missing bone inventory")
        names = [item.get("name") for item in items]
        if any(not isinstance(name, str) or not name for name in names) or len(names) != len(set(names)):
            raise ValueError(model + ": duplicate or invalid bone names")
        separately_named = sorted(name for name in names
                                  if any(token in name.lower() for token in ABSENT_SEGMENT_TOKENS))
        if separately_named:
            raise ValueError(model + ": unexpected segment-named controls require explicit review")
        bones = dict(zip(names, items))
        suffix_rows = {suffix: _suffix_row(bones, suffix) for suffix in ("l", "r")}
        selected = sorted({name for row in suffix_rows.values()
                           for value in row.values() if isinstance(value, (list, str))
                           for name in (value if isinstance(value, list) else [value])
                           if name in bones})
        subset = {name: {key: bones[name].get(key) for key in
                         ("parent", "rest_head_body_local_m", "rest_tail_body_local_m",
                          "pose_rotation_mode", "use_deform", "pose_constraint_metadata")}
                  for name in selected}
        fingerprint = hashlib.sha256(json.dumps(subset, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        fingerprints[model] = fingerprint
        rows[model] = {
            "consumed_rig_member_sha256": member_sha256[model],
            "bone_count": len(items),
            "suffix_chains": suffix_rows,
            "separately_named_patella_talus_calcaneus_hindfoot_midfoot_or_forefoot_controls": [],
            "selected_chain_fingerprint_sha256": fingerprint,
        }
    if len(set(fingerprints.values())) != 1:
        raise ValueError("cross-model selected chain mismatch requires review")
    return {
        "status": "AUTHORED_LIMB_CHAINS_PRESENT_ANATOMICAL_FRAMES_AND_COUPLING_BLOCKED",
        "evidence_scope": "PINNED_NATIVE_REST_SKELETAL_INVENTORY_ONLY",
        "models": rows,
        "all_three_selected_chains_identical": True,
        "scapulohumeral_coordination_tested": False,
        "clavicle_scapula_humerus_anatomical_frames_verified": False,
        "hip_knee_ankle_joint_centres_verified": False,
        "separately_named_patella_or_internal_foot_controls_observed": False,
        "ground_contact_tested": False,
        "balance_tested": False,
        "skin_deformation_tested": False,
        "anatomical_approval": "NOT_GRANTED",
        "limitations": [
            "Authored control hierarchy is not an ISB segment or joint coordinate frame.",
            "Shoulder-cap and hip-crease authored controls are not promoted to anatomical landmarks, muscles or joint centres.",
            "No shoulder rhythm, squat, gait, foot contact, toe loading, balance or return trajectory was executed.",
            "No separately named patella, talus, calcaneus, hindfoot, midfoot or forefoot control was observed; this does not prove the mesh lacks those anatomical forms.",
            "Suffix l/r is not independently verified anatomical side and population ROM means are not limits.",
        ],
    }


def audit(root):
    docs, hashes = load_native_evidence(root)
    return audit_loaded(docs, hashes)


def markdown(report):
    lines = ["# Native shoulder and lower-limb chain readiness", "",
             "**Status:** `" + report["status"] + "`", "",
             "Pinned rest-skeleton hierarchy only; no movement or anatomical calibration.", "",
             "| Model | Bones | Shoulder chain | Lower-limb chain |", "|---|---:|---|---|"]
    for model in MODELS:
        row = report["models"][model]
        left = row["suffix_chains"]["l"]
        lines.append(f"| {model} | {row['bone_count']} | {' → '.join(left['shoulder'])} | {' → '.join(left['lower_limb'])} |")
    lines += ["", "The corresponding authored r-suffix chains have the same hierarchy. No suffix is certified as anatomical side.",
              "No scapulohumeral coordination, squat/contact/balance or skin behavior was tested.", "", "## Limits", ""]
    lines += ["- " + item for item in report["limitations"]]
    return "\n".join(lines) + "\n"


def _within(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _atomic(path, content):
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temp = Path(handle.name)
        handle.write(content)
    try:
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def write_report(report, out, evidence_roots):
    out = Path(out)
    roots = [Path(root).resolve() for root in evidence_roots]
    resolved = out.resolve()
    if any(resolved == root or _within(resolved, root) for root in roots):
        raise ValueError("output directory cannot be inside evidence")
    out.mkdir(parents=True, exist_ok=True)
    targets = (out / JSON_NAME, out / MD_NAME)
    members = [p for root in roots if root.exists() for p in root.rglob("*") if p.is_file() or p.is_symlink()]
    for target in targets:
        if target.exists() or target.is_symlink():
            for member in members:
                try:
                    if target.samefile(member):
                        raise ValueError("output alias targets evidence")
                except FileNotFoundError:
                    pass
    _atomic(targets[0], json.dumps(report, indent=2) + "\n")
    _atomic(targets[1], markdown(report))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.root)
    write_report(report, args.out, [args.root])
    print(report["status"], {m: report["models"][m]["bone_count"] for m in MODELS})


if __name__ == "__main__":
    main()
