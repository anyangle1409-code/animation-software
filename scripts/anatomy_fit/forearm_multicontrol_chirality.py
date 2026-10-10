#!/usr/bin/env python3
"""Additional read-only chirality check for grouped radius/ulna twist helpers.

Extends the 118 one-to-one alias bindings reported in PR #27 with 12
multi-control links deliberately excluded by its single-control scanner.
This never registers bones, changes rig names or promotes evidence.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import anatomical_runtime_chirality_gate as base

ROOT = Path(__file__).resolve().parents[2]
BONE_NAMES = ("radius", "ulna")
EXPECTED_CONTROLS = ("forearm", "forearm_tw0", "forearm_tw1")
MIN_SIDE_M = 0.004


def record_mid(record, a, b):
    return base.bone_midpoint(record, a, b)


def report(fit, runtime, aliases):
    _, lateral = base.validate_frame(fit, runtime)
    rows = aliases["aliases"]
    by_id = {a["anatomical_id"]: a for a in rows}
    by_name = {b["name"]: b for b in runtime["bones"]}
    if len(by_id) != len(rows) or len(by_name) != len(runtime["bones"]):
        raise ValueError("Duplicate anatomical alias or runtime control name")
    if len(by_id) != 206 or len(by_name) != 67:
        raise ValueError("Unexpected source inventory counts")
    evidence = []
    for osseous in BONE_NAMES:
        for side in ("left", "right"):
            aid = osseous + "_" + side
            names = by_id[aid]["current_rig"]
            side_in_name = "_l" if side == "left" else "_r"
            side_by_geometry = "_r" if side == "left" else "_l"
            expected_stored = [name + side_in_name for name in EXPECTED_CONTROLS]
            if names != expected_stored:
                raise ValueError("Unexpected multi-control map; re-audit " + aid)
            if by_id[aid]["relationship"] != "radius_ulna_collapsed_with_twist_helpers":
                raise ValueError("Relationship no longer marks shared radius/ulna twist helpers")
            anatomical = fit["bones"][aid]
            anatomical_pos = base.convert_audit_to_runtime(
                record_mid(anatomical, "head_m", "tail_m"))
            anatomical_x = base.signed_lateral(anatomical_pos, lateral)
            sign = 1 if side == "left" else -1
            if sign * anatomical_x <= MIN_SIDE_M:
                raise ValueError("Source radius/ulna side coordinate contradicted: " + aid)
            for target in EXPECTED_CONTROLS:
                old = target + side_in_name
                opposite = target + side_by_geometry
                if old not in by_name or opposite not in by_name:
                    raise ValueError("Missing forearm or twist helper runtime counterpart: " + target)
                x_old = base.signed_lateral(record_mid(by_name[old], "head", "tail"), lateral)
                x_opposite = base.signed_lateral(record_mid(by_name[opposite], "head", "tail"), lateral)
                if sign * x_old >= -MIN_SIDE_M or sign * x_opposite <= MIN_SIDE_M:
                    raise ValueError("Unexpected runtime forearm twist helper physical side: " + old)
                evidence.append({
                    "anatomical_reference": aid,
                    "relationship": by_id[aid]["relationship"],
                    "legacy_alias": old,
                    "opposite_side_candidate": opposite,
                    "source_anatomical_lateral_m": round(anatomical_x, 6),
                    "legacy_alias_lateral_m": round(x_old, 6),
                    "candidate_lateral_m": round(x_opposite, 6),
                    "status": "OPPOSITE_PHYSICAL_SIDE_IN_NAME_ONLY_ALIAS",
                })
    return {
        "schema_version": 1,
        "scope": "READ_ONLY_RADIUS_ULNA_MULTI_CONTROL_SIDE_CHECK",
        "independent_bone_id_count": 4,
        "additional_crossed_alias_links": len(evidence),
        "legacy_single_control_links_in_parent_pr": 118,
        "total_crossed_side_links_when_combined": 118 + len(evidence),
        "source_anatomical_bones_verified": False,
        "twist_motion_or_pronation_supination_verified": False,
        "rig_export_approved": False,
        "source_or_runtime_modified": False,
        "evidence": evidence,
        "blocking_handoff": (
            "Review forearm and both twist helpers on both sides in a distinct "
            "adapter. A side-correct alias is NOT proof of proper pronation, "
            "supination, hand chirality or skinned wrist motion."
        ),
    }


def from_repository(root=ROOT):
    raw = {k: (root / path).read_bytes() for k, path in base.SOURCE.items()}
    records = {k: json.loads(v) for k, v in raw.items()}
    result = report(records["fitted_skeleton"], records["runtime_skeleton"],
                    records["alias_inventory"])
    result["source_sha256"] = {base.SOURCE[k]: hashlib.sha256(v).hexdigest()
                                for k, v in raw.items()}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    encoded = json.dumps(from_repository(), indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
