#!/usr/bin/env python3
"""Read-only numeric bilateral position probe for 54 source STLs.

Uses only SHA-verified source report bounding-box data. Numerical candidate
axis consistency is NOT proof of CT scanner left/right, HGPT bone-side mapping,
physical units, joint centres, morphology or any anatomy gate acceptance.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

FROZEN = "ac8de2b38f5ae1a0996053ca0639dd6ae43358f1"
GROUPS = {"carpus_file_candidate": 8, "tarsus_file_candidate": 7,
          "rib_file_candidate": 12}
MATCH = re.compile(r"^(.+?)_(LEFT|RIGHT)\.stl$")


def build_pairs(report: dict) -> dict:
    if (report.get("kind") != "HGPT_NONCANONICAL_54_BONE_SURFACE_QA" or
            report.get("source_revision") != FROZEN or
            report.get("cp1_gate6_approved") is not False or
            report.get("canonical_geometry_changed") is not False or
            report.get("independent_subject_evidence") is not False or
            report.get("stl_physical_units_and_axes_confirmed") is not False or
            len(report.get("items", [])) != 54):
        raise ValueError("Invalid, changed or falsely accepted source report")
    paired = defaultdict(dict)
    seen = set()
    for item in report["items"]:
        path = item["source_relpath"]
        if not isinstance(path, str) or path in seen or len(path.split("/")) != 2:
            raise ValueError("Malformed or duplicate source bone path")
        seen.add(path)
        group = item["source_file_group"]
        if group not in GROUPS:
            raise ValueError("Unexpected source region")
        folder, name = path.split("/")
        m = MATCH.fullmatch(name)
        if not m:
            raise ValueError("Bone name missing explicit side")
        bone, side = m.groups()
        if group == "carpus_file_candidate" and folder != "HAND_"+side:
            raise ValueError("Carpal source folder/name side disagreement")
        if group == "tarsus_file_candidate" and folder != "FOOT_"+side:
            raise ValueError("Tarsal source folder/name side disagreement")
        if group == "rib_file_candidate" and (folder != "THORAX" or
                                                   not re.fullmatch(r"RIB_[0-9]{1,2}", bone)):
            raise ValueError("Unexpected rib source")
        source_sha = item.get("reference_sha256_verified")
        if (not isinstance(source_sha, str) or len(source_sha) != 64 or
                any(c not in "0123456789abcdef" for c in source_sha)):
            raise ValueError("Source STL was not SHA-pinned")
        small = item.get("bbox_min_source_units_unknown")
        large = item.get("bbox_max_source_units_unknown")
        if (not isinstance(small, list) or not isinstance(large, list) or
                len(small) != 3 or len(large) != 3 or
                any(not isinstance(t, (int, float)) or not math.isfinite(t)
                    for t in small + large) or
                any(large[j] <= small[j] for j in range(3))):
            raise ValueError("Invalid source bounding box")
        midpoint = [(small[j]+large[j])/2 for j in range(3)]
        key = group+":"+bone
        if side in paired[key]:
            raise ValueError("Duplicate source side for same bone")
        paired[key][side] = midpoint
    if len(paired) != 27:
        raise ValueError("Not exactly 27 distinct source bone pairs")
    if {k:sum(key.startswith(k+":") for key in paired) for k in GROUPS} != GROUPS:
        raise ValueError("Missing side-group bone pairs")
    deltas = {}
    for key, sides in paired.items():
        if set(sides) != {"LEFT", "RIGHT"}:
            raise ValueError("Missing labelled bilateral counterpart")
        deltas[key] = [sides["LEFT"][j]-sides["RIGHT"][j] for j in range(3)]
    x_positive = sum(x[0]>0 for x in deltas.values())
    dominant_x = sum(abs(x[0])>max(abs(x[1]),abs(x[2])) for x in deltas.values())
    summaries = {}
    for group in GROUPS:
        group_deltas = [v for k, v in deltas.items() if k.startswith(group+":")]
        summaries[group] = {
            "pair_count": len(group_deltas),
            "labelled_left_positive_x_pairs": sum(v[0]>0 for v in group_deltas),
            "source_x_largest_abs_separation_pairs": sum(
                abs(v[0]) > max(abs(v[1]),abs(v[2])) for v in group_deltas),
            "median_xyz_labelled_left_minus_right_source_units_unknown": [
                statistics.median(x[j] for x in group_deltas) for j in range(3)],
        }
    return {
        "schema_version": 1,
        "kind": "HGPT_SOURCE_LABEL_BILATERAL_BBOX_FRAME_HYPOTHESIS",
        "source_revision": FROZEN,
        "verified_raw_stl_count": 54,
        "bilateral_file_pairs": 27,
        "labelled_left_x_greater_than_right": x_positive,
        "dominant_source_x_difference_pairs": dominant_x,
        "hypothesis_left_label_on_source_positive_x": x_positive == 27 and dominant_x == 27,
        "source_units_and_scanner_axes_verified": False,
        "anat_left_correspondence_proven": False,
        "bone_centroids_measured": False,
        "articular_contacts_measured": False,
        "runtime_adapter_approved": False,
        "cp1_gate6_approved": False,
        "cohort_independent": False,
        "groups": summaries,
        "pair_deltas_source_units_unknown": dict(sorted(deltas.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        src = args.input.expanduser().resolve()
        out = args.output.expanduser().resolve()
        repo_root = Path(__file__).resolve().parents[2]
        if out.exists() or repo_root == out.parent or repo_root in out.parent.parents:
            raise ValueError("Report must be new, private and outside the Git checkout")
        report = json.loads(src.read_text(encoding="utf-8"))
        derived = build_pairs(report)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("x", encoding="utf-8") as fp:
            json.dump(derived, fp, indent=2, sort_keys=True)
            fp.write("\n")
        print(json.dumps({
            "bilateral_pairs": derived["bilateral_file_pairs"],
            "left_label_positive_source_x": derived["labelled_left_x_greater_than_right"],
            "source_x_largest_pair_separation": derived["dominant_source_x_difference_pairs"],
            "source_frame_and_actual_anatomical_laterality_verified": False,
            "report_path": str(out),
        }, indent=2))
        return 0
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as err:
        print("Rejected source-frame diagnostic: "+str(err), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
