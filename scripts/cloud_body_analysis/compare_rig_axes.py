"""Hash-pinned, read-only comparison of W8/V14/R120 Blender bone-local rest axes.

Matching bone axes does NOT prove human joint coordinate calibration, plausible
skin movement, true muscle attachments, or anatomical left/right identity.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

MODELS = ("W8", "V14", "R120")
EXPECTED = {
    "W8": "2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c",
    "V14": "5969aa98122e267b6bdd94fdfaf6d2877a1b27f7ea8d11c6a8e078b467b0ff91",
    "R120": "fb3b0acfc68bc59952b0fc6c45f7d7715717207fd9ba0b7f2b124e905ce2ddcb",
}
NOT_GRANTED = (
    "model_motion_axes_calibrated_to_ISB",
    "actual_anatomical_joint_centres_verified",
    "anatomical_side_mapped",
    "native_human_ROM_limits_validated",
    "any_bones_rotated_or_keyframed",
)
FIELDS = (
    "name", "parent", "rest_head_body_local_m", "rest_tail_body_local_m",
    "rest_local_X_Y_Z_unit_in_body_coordinates", "axis_noncircularity_dot_max",
    "roll_radians_stored", "use_deform", "connected_to_parent",
    "pose_rotation_mode", "pose_constraint_metadata",
)

def finite3(v):
    return (isinstance(v, list) and len(v) == 3 and
            all(type(x) in (int, float) and math.isfinite(x) for x in v))

def load(root, model):
    d = json.loads((Path(root) / model / "rig_rest_axes_metadata.json").read_text(encoding="utf-8"))
    if (d.get("model") != model or d.get("source_sha256") != EXPECTED[model]
        or d.get("original_source_unchanged") is not True):
        raise ValueError(model + ": pinned source identity/preservation failed")
    if d.get("status") != "BLENDER_LOCAL_BONE_AXIS_INVENTORY_ONLY_ANATOMICAL_MAPPING_NOT_APPROVED":
        raise ValueError(model + ": invalid anatomy approval status")
    if any(d.get(key) is not False for key in NOT_GRANTED):
        raise ValueError(model + ": unearned anatomy or model modification claim")
    bones = d.get("bones")
    if not isinstance(bones, list) or not bones or d.get("bone_count") != len(bones):
        raise ValueError(model + ": missing/inconsistent bone count")
    names = [b.get("name") for b in bones]
    if any(not isinstance(n, str) or not n for n in names) or len(set(names)) != len(names):
        raise ValueError(model + ": duplicate/invalid bone names")
    for b in bones:
        if any(k not in b for k in FIELDS):
            raise ValueError(model + ": incomplete bone metadata")
        if b["parent"] is not None and (b["parent"] not in names or b["parent"] == b["name"]):
            raise ValueError(model + ": invalid parent")
        if not finite3(b["rest_head_body_local_m"]) or not finite3(b["rest_tail_body_local_m"]):
            raise ValueError(model + ": invalid bone coordinates")
        axes = b["rest_local_X_Y_Z_unit_in_body_coordinates"]
        if not isinstance(axes, list) or len(axes) != 3 or not all(finite3(v) for v in axes):
            raise ValueError(model + ": invalid bone axes")
        if any(abs(sum(x*x for x in v) - 1) > 0.002 for v in axes):
            raise ValueError(model + ": non-unit bone axes")
        if any(abs(sum(x*y for x, y in zip(axes[i], axes[j]))) > 0.002
               for i, j in ((0, 1), (0, 2), (1, 2))):
            raise ValueError(model + ": nonorthogonal bone axes")
    if not isinstance(d.get("body_modifier_metadata"), list):
        raise ValueError(model + ": missing modifier inventory")
    return d

def comparable(d):
    return {
        "bones": {b["name"]: {k: b[k] for k in FIELDS} for b in d["bones"]},
        "body_object": d.get("body_object"),
        "rig_object": d.get("rig_object"),
        "body_modifier_metadata": d["body_modifier_metadata"],
    }

def mirror_residuals(bones):
    """Only X-mirror geometry of _l/_r *labels*, never side verification."""
    rows = []
    for name, b in sorted(bones.items()):
        if not name.endswith("_l") or name[:-2] + "_r" not in bones:
            continue
        other = bones[name[:-2] + "_r"]
        def dist(field):
            x = b[field]
            return round(1000 * math.dist([-x[0], x[1], x[2]], other[field]), 5)
        rows.append({"suffix_l": name, "suffix_r": other["name"],
                     "head_residual_mm": dist("rest_head_body_local_m"),
                     "tail_residual_mm": dist("rest_tail_body_local_m")})
    return rows

def compare(root):
    docs = {m: load(root, m) for m in MODELS}
    data = {m: comparable(docs[m]) for m in MODELS}
    diffs = {}
    for m in ("V14", "R120"):
        names = sorted(set(data["W8"]["bones"]) | set(data[m]["bones"]))
        diffs[m] = [n for n in names if data["W8"]["bones"].get(n) != data[m]["bones"].get(n)]
        for field in ("body_object", "rig_object", "body_modifier_metadata"):
            if data["W8"][field] != data[m][field]:
                diffs[m].append("<" + field + ">")
    same = not any(diffs.values())
    mirrors = mirror_residuals(data["W8"]["bones"])
    if not mirrors:
        raise ValueError("no paired suffix landmarks available")
    fingerprints = {
        m: hashlib.sha256(json.dumps(data[m], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        for m in MODELS
    }
    return {
        "status": ("REST_AXIS_METADATA_IDENTICAL_NOT_ANATOMICAL_APPROVAL" if same
                   else "REST_AXIS_METADATA_MISMATCH_REVIEW_REQUIRED"),
        "source_sha256": EXPECTED, "run_ids": {m: docs[m].get("run") for m in MODELS},
        "bone_counts": {m: len(data[m]["bones"]) for m in MODELS},
        "metadata_fingerprints_sha256": fingerprints,
        "all_three_identical": same, "differences_vs_W8": diffs,
        "w8_x_mirror_suffix_pairs": mirrors,
        "w8_max_head_reflection_residual_mm": max(r["head_residual_mm"] for r in mirrors),
        "w8_max_tail_reflection_residual_mm": max(r["tail_residual_mm"] for r in mirrors),
        "anatomical_side_verified": False, "isb_joint_axes_calibrated": False,
        "human_joint_rom_limits_approved": False, "skin_deformation_approved": False,
        "limitations": [
            "Only as-loaded bone-local REST axes, no posed exercise or movement validation",
            "Same rig matrices do not establish ISB joint axes, joint centres or anatomy",
            "X-reflection and suffix pairs are geometric proxies, not anatomical side proof",
            "Clinical population ROM means must not become bone rotation hard limits",
            "V14 archive vertex mismatch and shoulder, elbow, hip, foot, grip defects unresolved",
            "No source .blend, mesh, skin weights, muscle binding or PT-App changes",
        ],
    }

def markdown(d):
    lines = ["# Home Gym PT read-only cross-model rig-axis comparison", "",
             "**Status:** " + d["status"], "",
             "| Model | Bones | Rig metadata SHA256 |", "|---|---:|---|"]
    for m in MODELS:
        lines.append(f"| {m} | {d['bone_counts'][m]} | {d['metadata_fingerprints_sha256'][m]} |")
    lines += ["", f"All rest rig metadata identical: **{d['all_three_identical']}**.",
              f"W8 suffix pairs: **{len(d['w8_x_mirror_suffix_pairs'])}**.",
              f"W8 maximum X-mirror head/tail residuals: **{d['w8_max_head_reflection_residual_mm']} / {d['w8_max_tail_reflection_residual_mm']} mm**.",
              "", "These are geometric rest-axis results, NOT certified human anatomical axes.", "",
              "## Unresolved issues", ""]
    lines += ["- " + s for s in d["limitations"]]
    for m, diffs in d["differences_vs_W8"].items():
        if diffs:
            lines.append(f"- {m} metadata differs: {', '.join(diffs)}")
    return "\n".join(lines) + "\n"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    report = compare(a.root)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "rig_rest_axis_comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    (a.out / "rig_rest_axis_comparison.md").write_text(markdown(report))
    print(report["status"], report["bone_counts"])
    if not report["all_three_identical"]:
        raise SystemExit("Rest rig metadata differ: explicit review required")

if __name__ == "__main__":
    main()
