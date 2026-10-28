"""Read-only authored forearm-chain evidence; not anatomical validation.

This report asks whether the pinned native skeletal inventory contains evidence
for independently controlled radius and ulna segments.  Bone names, suffixes,
and twist helpers are never promoted to anatomical bindings or joint axes.
"""
import argparse
import hashlib
import json
import math
import os
import re
import tempfile
from pathlib import Path

from compare_rig_axes import EXPECTED, MODELS, NOT_GRANTED

JSON_NAME = "forearm_chain_readiness.json"
MD_NAME = "forearm_chain_readiness.md"
SHA256 = re.compile(r"[0-9a-f]{64}")


def _finite3(value):
    return (isinstance(value, list) and len(value) == 3 and
            all(type(x) in (int, float) and math.isfinite(x) for x in value))


def _selected_chain(bones, suffix):
    names = {
        "upperarm": f"upperarm_{suffix}",
        "forearm": f"forearm_{suffix}",
        "tw0": f"forearm_tw0_{suffix}",
        "tw1": f"forearm_tw1_{suffix}",
        "hand": f"hand_{suffix}",
    }
    missing = sorted(set(names.values()) - set(bones))
    if missing:
        raise ValueError("missing required authored forearm controls: " + ", ".join(missing))
    expected_parents = {
        names["forearm"]: names["upperarm"],
        names["tw0"]: names["forearm"],
        names["tw1"]: names["forearm"],
        names["hand"]: names["forearm"],
    }
    for name, parent in expected_parents.items():
        if bones[name].get("parent") != parent:
            raise ValueError(f"unexpected authored forearm chain: {name} parent")
    for name in names.values():
        item = bones[name]
        if not _finite3(item.get("rest_head_body_local_m")) or not _finite3(item.get("rest_tail_body_local_m")):
            raise ValueError(f"nonfinite or invalid chain coordinates: {name}")
        constraints = item.get("pose_constraint_metadata")
        if constraints != []:
            raise ValueError(f"unexpected or unrecorded chain constraint metadata: {name}")
    helpers = sorted(name for name in bones if re.fullmatch(rf"forearm_tw\d+_{suffix}", name, re.I))
    if helpers != [names["tw0"], names["tw1"]]:
        raise ValueError(f"unexpected twist helper inventory for suffix {suffix}: {helpers}")
    for name in helpers:
        if bones[name].get("use_deform") is not True or bones[name].get("pose_rotation_mode") != "QUATERNION":
            raise ValueError(f"twist helper semantics changed: {name}")
    return {
        "upperarm_control": names["upperarm"],
        "forearm_control": names["forearm"],
        "twist_helpers": [names["tw0"], names["tw1"]],
        "hand_control": names["hand"],
        "hand_parent": bones[names["hand"]]["parent"],
        "twist_helper_parents": [bones[names["tw0"]]["parent"], bones[names["tw1"]]["parent"]],
        "twist_helper_rotation_modes": [bones[names["tw0"]].get("pose_rotation_mode"), bones[names["tw1"]].get("pose_rotation_mode")],
        "radius_ulna_anatomical_binding_verified": False,
        "independent_radioulnar_rotation_verified": False,
    }


def audit_loaded(docs, member_sha256):
    if set(docs) != set(MODELS) or set(member_sha256) != set(MODELS):
        raise ValueError("exact W8/V14/R120 evidence is required")
    if any(not isinstance(v, str) or not SHA256.fullmatch(v) for v in member_sha256.values()):
        raise ValueError("every consumed rig member requires a SHA256")
    model_rows = {}
    fingerprints = {}
    for model in MODELS:
        items = docs[model].get("bones")
        if not isinstance(items, list) or not items:
            raise ValueError(model + ": missing bone inventory")
        names = [x.get("name") for x in items]
        if any(not isinstance(x, str) or not x for x in names) or len(names) != len(set(names)):
            raise ValueError(model + ": duplicate or invalid bone names")
        bones = dict(zip(names, items))
        chains = {suffix: _selected_chain(bones, suffix) for suffix in ("l", "r")}
        radius_named = sorted(x for x in names if re.search(r"(^|[_.-])radius($|[_.-])", x, re.I))
        ulna_named = sorted(x for x in names if re.search(r"(^|[_.-])ulna($|[_.-])", x, re.I))
        if radius_named or ulna_named:
            raise ValueError(model + ": unexpected radius/ulna-named controls require explicit review")
        subset = {name: {k: bones[name].get(k) for k in
                         ("parent", "rest_head_body_local_m", "rest_tail_body_local_m",
                          "pose_rotation_mode", "pose_constraint_metadata")}
                  for suffix in ("l", "r") for name in
                  (f"upperarm_{suffix}", f"forearm_{suffix}", f"forearm_tw0_{suffix}",
                   f"forearm_tw1_{suffix}", f"hand_{suffix}")}
        fingerprint = hashlib.sha256(json.dumps(subset, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        fingerprints[model] = fingerprint
        model_rows[model] = {
            "consumed_rig_member_sha256": member_sha256[model],
            "bone_count": len(items),
            "authored_suffix_chains": chains,
            "radius_named_controls": radius_named,
            "ulna_named_controls": ulna_named,
            "authored_forearm_chain_fingerprint_sha256": fingerprint,
        }
    if len(set(fingerprints.values())) != 1:
        raise ValueError("cross-model authored forearm chain mismatch requires review")
    return {
        "status": "BLOCKED_NO_INDEPENDENT_RADIUS_ULNA_CONTROL_EVIDENCE",
        "evidence_scope": "PINNED_NATIVE_REST_SKELETAL_INVENTORY_ONLY",
        "models": model_rows,
        "all_three_authored_forearm_chains_identical": True,
        "separate_radius_ulna_skeletal_controls_observed": False,
        "twist_helpers_are_anatomical_radius_ulna": False,
        "authored_suffixes_are_anatomical_sides": False,
        "bone_local_axes_are_isb_axes": False,
        "elbow_flexion_tested": False,
        "forearm_pronation_supination_tested": False,
        "skin_deformation_tested": False,
        "anatomical_approval": "NOT_GRANTED",
        "limitations": [
            "The inventory shows one authored forearm control plus two twist helpers per suffix; it does not bind them to radius or ulna anatomy.",
            "The hand is parented to the authored forearm control, not through either twist helper; this is hierarchy evidence, not motion behavior.",
            "No posed elbow-flexion or pronation/supination trajectory was executed.",
            "Absence of radius/ulna-named controls is not proof that the mesh lacks radius/ulna form, only that independent skeletal controls are not evidenced here.",
            "Suffix l/r and reflected rest geometry are not independently verified anatomical sides.",
            "Population ROM means are not joint limits and are not applied by this audit.",
        ],
    }


def _validate_native_doc(doc, model):
    if (doc.get("model") != model or doc.get("source_sha256") != EXPECTED[model]
        or doc.get("original_source_unchanged") is not True
        or doc.get("status") != "BLENDER_LOCAL_BONE_AXIS_INVENTORY_ONLY_ANATOMICAL_MAPPING_NOT_APPROVED"
        or any(doc.get(key) is not False for key in NOT_GRANTED)):
        raise ValueError(model + ": pinned source identity/preservation/approval failed")
    bones = doc.get("bones")
    if not isinstance(bones, list) or not bones or doc.get("bone_count") != len(bones):
        raise ValueError(model + ": missing/inconsistent bone count")
    if not isinstance(doc.get("body_modifier_metadata"), list):
        raise ValueError(model + ": missing modifier inventory")
    for item in bones:
        axes = item.get("rest_local_X_Y_Z_unit_in_body_coordinates")
        if (not _finite3(item.get("rest_head_body_local_m"))
            or not _finite3(item.get("rest_tail_body_local_m"))
            or not isinstance(axes, list) or len(axes) != 3 or not all(_finite3(axis) for axis in axes)):
            raise ValueError(model + ": invalid/nonfinite rest coordinates or axes")
        if any(abs(sum(x * x for x in axis) - 1.0) > 0.002 for axis in axes):
            raise ValueError(model + ": non-unit rest axis")
        if any(abs(sum(x * y for x, y in zip(axes[i], axes[j]))) > 0.002
               for i, j in ((0, 1), (0, 2), (1, 2))):
            raise ValueError(model + ": nonorthogonal rest axes")
    return doc


def audit(root):
    root = Path(root)
    docs = {}
    hashes = {}
    for model in MODELS:
        path = root / model / "rig_rest_axes_metadata.json"
        payload = path.read_bytes()
        hashes[model] = hashlib.sha256(payload).hexdigest()
        try:
            parsed = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(model + ": invalid rig JSON") from exc
        docs[model] = _validate_native_doc(parsed, model)
    return audit_loaded(docs, hashes)


def markdown(report):
    lines = [
        "# Native forearm skeletal-chain readiness", "",
        "**Status:** `" + report["status"] + "`", "",
        "This is pinned rest-skeleton hierarchy evidence, not an elbow or radioulnar movement test.", "",
        "| Model | Bones | l chain | r chain | Separate radius/ulna controls |",
        "|---|---:|---|---|---|",
    ]
    for model in MODELS:
        row = report["models"][model]
        def chain(side):
            value = row["authored_suffix_chains"][side]
            return value["upperarm_control"] + " → " + value["forearm_control"] + " → " + value["hand_control"]
        lines.append(f"| {model} | {row['bone_count']} | {chain('l')} | {chain('r')} | not observed |")
    lines += ["", "Each suffix also has two forearm twist helpers parented to the single forearm control; the hand bypasses those helpers in the recorded hierarchy.",
              "No helper is certified as radius or ulna, and no pronation/supination was run.", "", "## Limits", ""]
    lines += ["- " + item for item in report["limitations"]]
    return "\n".join(lines) + "\n"


def _is_within(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _atomic_text(path, content):
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
    roots = [Path(x).resolve() for x in evidence_roots]
    resolved_out = out.resolve()
    if any(resolved_out == root or _is_within(resolved_out, root) for root in roots):
        raise ValueError("output directory cannot be inside evidence")
    out.mkdir(parents=True, exist_ok=True)
    targets = [out / JSON_NAME, out / MD_NAME]
    members = [p for root in roots if root.exists() for p in root.rglob("*") if p.is_file() or p.is_symlink()]
    for target in targets:
        if target.exists() or target.is_symlink():
            for member in members:
                try:
                    if target.samefile(member):
                        raise ValueError("output alias targets evidence")
                except FileNotFoundError:
                    pass
    _atomic_text(targets[0], json.dumps(report, indent=2) + "\n")
    _atomic_text(targets[1], markdown(report))


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
