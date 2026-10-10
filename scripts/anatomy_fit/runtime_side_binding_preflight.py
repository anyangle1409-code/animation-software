#!/usr/bin/env python3
"""Read-only anatomical-master -> legacy runtime side-binding preflight.

This intentionally DOES NOT patch production rigs, rename bones, or assert
that the two coordinate systems are globally registered. It proves only
whether named _l/_r aliases correspond to the *sided X* of the stored bones.

Input anatomy: r95 a003 (+X is anatomical left); runtime rev2c legacy _l
bones lie on -X. Name-matched alias rows therefore describe the opposite
body side. Report proposed inverse-name bindings as DIAGNOSTICS, never a
validated transform/production migration.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANATOMY = ROOT / "ORIGINAL_V1_WORK" / "anatomy"
FIT = ANATOMY / "character_fit_r95_a003.json"
ALIASES = ANATOMY / "adult_bone_blender_aliases_206.json"
RUNTIME = ROOT / "ORIGINAL_V1_WORK" / "hgpt_canonical_v4_original_rev2c.json"

SIDES = {"left": "_r", "right": "_l"}
POSITIVE_MIN_M = 0.0001
ANCHORS = {
    "clavicle": "clavicle",
    "humerus": "upperarm",
    "femur": "thigh",
}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def x_mid(record, atlas):
    key = "head_m" if atlas else "head"
    tail = "tail_m" if atlas else "tail"
    return 0.5 * (float(record[key][0]) + float(record[tail][0]))


def suffix(name):
    if name.endswith("_l"):
        return "_l"
    if name.endswith("_r"):
        return "_r"
    return None


def opposite(name):
    s = suffix(name)
    if s is None:
        raise ValueError("Expected a sided runtime name: " + name)
    return name[:-2] + ("_r" if s == "_l" else "_l")


def required(condition, detail):
    if not condition:
        raise ValueError(detail)


def check_anchors(fit_bones, rig_bones):
    """Independent geometry check; never trust declared side names alone."""
    checks = []
    for anatomical_name, runtime_name in ANCHORS.items():
        for side in ("left", "right"):
            ab = fit_bones[anatomical_name + "_" + side]
            expected = runtime_name + SIDES[side]
            rb = rig_bones[expected]
            ax, rx = x_mid(ab, True), x_mid(rb, False)
            s = 1 if side == "left" else -1
            required(s * ax > POSITIVE_MIN_M,
                     "Anatomical anchor chirality changed: " + anatomical_name + "_" + side)
            required(s * rx > POSITIVE_MIN_M,
                     "Runtime anchor chirality changed: " + expected)
            checks.append({
                "anatomical_id": anatomical_name + "_" + side,
                "resolved_runtime_name": expected,
                "anatomical_x_m": round(ax, 6),
                "runtime_x_m": round(rx, 6),
                "status": "SIDE_SIGNS_AGREE_ONLY",
            })
    return checks


def build_report(fit, aliases, runtime):
    fit_bones = fit["bones"]
    rig_items = runtime["bones"]
    rig_bones = {x["name"]: x for x in rig_items}
    rows = aliases["aliases"]
    ids = [x["anatomical_id"] for x in rows]
    required(len(rows) == len(set(ids)) == 206, "Alias atlas must contain 206 unique IDs")
    required(set(ids) == set(fit_bones), "Alias IDs do not match 206 anatomical fit IDs")
    required(len(rig_items) == len(rig_bones) == 67, "Unexpected original runtime rig inventory")
    conv = fit["conventions"]
    required(conv["runtime_side_binding"] == SIDES,
             "Previously recorded side binding changed; re-audit source coordinate systems")
    required("anatomical LEFT = +X" in conv["world"],
             "Expected anatomical left/right coordinates not explicitly declared")
    anchors = check_anchors(fit_bones, rig_bones)
    counts = {
        "named_sided_aliases": 0,
        "name_only_wrong_side": 0,
        "named_side_consistent": 0,
        "unsided_or_collapsed": 0,
        "no_runtime_mapping": 0,
    }
    diagnosed = []
    for row in rows:
        anatomical_id = row["anatomical_id"]
        side = ("left" if anatomical_id.endswith("_left") else
                "right" if anatomical_id.endswith("_right") else None)
        given = row["current_rig"]
        required(isinstance(given, list), "Invalid current_rig alias list: " + anatomical_id)
        for name in given:
            required(name in rig_bones, "Unknown current rig bone in alias: " + anatomical_id + " -> " + name)
        if not given:
            counts["no_runtime_mapping"] += 1
            continue
        sided_names = [n for n in given if suffix(n)]
        if not side or not sided_names:
            counts["unsided_or_collapsed"] += 1
            continue
        required(len(sided_names) == len(given),
                 "Mixed-sided and unsided mapping requires manual review: " + anatomical_id)
        expected_suffix = SIDES[side]
        ax = x_mid(fit_bones[anatomical_id], True)
        expected_sign = 1 if side == "left" else -1
        required(expected_sign * ax > POSITIVE_MIN_M,
                 "Anatomical bone appears on opposite/centre side: " + anatomical_id)
        for current in sided_names:
            counterpart = opposite(current)
            required(counterpart in rig_bones,
                     "No opposite runtime bone for " + anatomical_id + " -> " + current)
            observed = x_mid(rig_bones[current], False)
            corrected = x_mid(rig_bones[counterpart], False)
            required(expected_sign * corrected > POSITIVE_MIN_M,
                     "Inverse runtime candidate does not occupy anatomical side: " + anatomical_id)
            counts["named_sided_aliases"] += 1
            wrong = (suffix(current) != expected_suffix)
            if wrong:
                required(expected_sign * observed < -POSITIVE_MIN_M,
                         "Name mismatch but source geometry does not corroborate inversion: " + anatomical_id)
                counts["name_only_wrong_side"] += 1
            else:
                required(expected_sign * observed > POSITIVE_MIN_M,
                         "Name-match geometry does not corroborate same side: " + anatomical_id)
                counts["named_side_consistent"] += 1
            diagnosed.append({
                "anatomical_id": anatomical_id,
                "relationship": row["relationship"],
                "stored_alias": current,
                "stored_alias_x_m": round(observed, 6),
                "inverse_name_candidate": counterpart if wrong else current,
                "candidate_x_m": round(corrected if wrong else observed, 6),
                "status": "OPPOSITE_BODY_SIDE" if wrong else "SAME_BODY_SIDE",
                "independent_anatomical_x_m": round(ax, 6),
            })
    # Opposite-name candidates must preserve bilateral pairing where the
    # atlas maps pairs to a single sided segment. Explicit collapses are retained.
    by_id = {x["anatomical_id"]: x for x in rows}
    for row in rows:
        aid = row["anatomical_id"]
        if not aid.endswith("_left"):
            continue
        pid = aid[:-5] + "_right"
        required(pid in by_id, "Missing counterpart for anatomical bone " + aid)
        here, there = row["current_rig"], by_id[pid]["current_rig"]
        if len(here) == len(there) == 1 and suffix(here[0]) and suffix(there[0]):
            required(opposite(here[0]) == there[0],
                     "Stored bilateral alias names aren't paired: " + aid)
    required(counts["name_only_wrong_side"] > 0,
             "Stored source no longer exhibits old naming inversion; re-audit before use")
    return {
        "schema_version": 1,
        "scope": "READ_ONLY_STATIC_X_SIDE_CHIRALITY; NOT_RIG_REGISTRATION",
        "anatomical_convention": conv["world"],
        "runtime_convention": runtime.get("coordinate_system"),
        "expected_runtime_suffix_for_anatomy": SIDES,
        "summary": counts,
        "independent_six_anchor_checks": anchors,
        "sided_alias_evidence": diagnosed,
        "safe_to_use_name_only_mapping": False,
        "source_mesh_updated": False,
        "rig_export_approved": False,
        "verified_full_3d_transform": False,
        "next_action": "Use explicit side-resolved mapping in a separate reviewed adapter; prove full 3D axis/frame parity, joints, pose transforms and Blender mesh before production transfer.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fit", type=Path, default=FIT)
    parser.add_argument("--aliases", type=Path, default=ALIASES)
    parser.add_argument("--runtime", type=Path, default=RUNTIME)
    parser.add_argument("--out", type=Path, help="Optional report destination (never changes source)")
    parser.add_argument("--require-name-safe", action="store_true",
                        help="Return nonzero while original name-only side mapping is unsafe")
    args = parser.parse_args()
    report = build_report(load(args.fit), load(args.aliases), load(args.runtime))
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    if args.require_name_safe and not report["safe_to_use_name_only_mapping"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
