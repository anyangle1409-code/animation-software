#!/usr/bin/env python3
"""Inspect PINNED upstream TotalSegmentator rib class maps without running models.

This reads the 33KB *public Python SOURCE FILE* at its immutable Git blob SHA,
parses AST literal dictionaries only and never executes the downloaded Python.
It does NOT fetch CT, masks, patients, neural models, licence-protected meshes
or imply one rib index equals the same anatomy across versions.
"""
from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import json
import re
import sys
import urllib.request

SOURCE_REPO = "wasserth/TotalSegmentator"
SOURCE_PATH = "totalsegmentator/map_to_binary.py"
SOURCE_BLOB = "34820bd066e0e930b81a741f8ccc6c81f588b528"
SOURCE_URL = (
    f"https://api.github.com/repos/{SOURCE_REPO}/git/blobs/{SOURCE_BLOB}"
)
MAX_SOURCE_BYTES = 100_000
VERSION_MAP_NAMES = {
    "total_v1": "legacy_v1",
    "total": "later_total_v2",
    "class_map_part_ribs": "later_rib_part",
}
RIB_BASE = {"legacy_v1": 58, "later_total_v2": 92, "later_rib_part": 1}
RIB_LEVELS = 12

def git_object_sha(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw
    ).hexdigest()


def source_from_github() -> bytes:
    request = urllib.request.Request(
        SOURCE_URL, headers={"User-Agent": "HGPT-rib-label-source-audit/1.0",
                             "Accept": "application/vnd.github+json"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        # GitHub REST blob metadata: public *source*, not patient files.
        if response.geturl() != SOURCE_URL:
            raise ValueError("Unexpected redirected source URL")
        body = response.read(MAX_SOURCE_BYTES * 2 + 1)
        if len(body) > 2 * MAX_SOURCE_BYTES:
            raise ValueError("Overlarge GitHub blob metadata")
        obj = json.loads(body)
    if (not isinstance(obj, dict) or obj.get("sha") != SOURCE_BLOB or
            obj.get("encoding") != "base64"):
        raise ValueError("Unexpected source blob identity or encoding")
    encoded = obj.get("content")
    if not isinstance(encoded, str):
        raise ValueError("Missing source bytes")
    raw = base64.b64decode(encoded, validate=False)
    if len(raw) > MAX_SOURCE_BYTES or obj.get("size") != len(raw):
        raise ValueError("Unexpected source byte count")
    if git_object_sha(raw) != SOURCE_BLOB:
        raise ValueError("Source bytes do not match frozen Git blob SHA")
    return raw


def literal_submap(tree: ast.Module, variable: str, key: str) -> dict:
    candidates = []
    for node in tree.body:
        if (isinstance(node, ast.Assign) and
                any(isinstance(t, ast.Name) and t.id == variable
                    for t in node.targets)):
            candidates.append(node.value)
    if len(candidates) != 1 or not isinstance(candidates[0], ast.Dict):
        raise ValueError("Expected one direct literal dictionary assignment")
    matched = []
    for k, v in zip(candidates[0].keys, candidates[0].values):
        if isinstance(k, ast.Constant) and k.value == key:
            matched.append(v)
    if len(matched) != 1:
        raise ValueError("Ambiguous or missing upstream class-map subset: " + key)
    try:
        output = ast.literal_eval(matched[0])
    except (ValueError, TypeError, SyntaxError, RecursionError) as e:
        raise ValueError("Nonliteral class map prohibited") from e
    if not isinstance(output, dict):
        raise ValueError("Source subset is not a mapping")
    if any(type(i) is not int or not isinstance(name, str)
           for i, name in output.items()):
        raise ValueError("Source class keys/values have unexpected types")
    return output


def expected_rib_map(base: int) -> dict[int, str]:
    out = {}
    for side_idx, side in enumerate(("left", "right")):
        for i in range(1, RIB_LEVELS+1):
            out[base + side_idx*RIB_LEVELS + i-1] = f"rib_{side}_{i}"
    return out


def extract_contract(raw: bytes, expected_blob: str = SOURCE_BLOB) -> dict:
    if git_object_sha(raw) != expected_blob:
        raise ValueError("Upstream Python source hash was not checked")
    try:
        source = raw.decode("utf-8", "strict")
        tree = ast.parse(source, filename=SOURCE_PATH)
    except (UnicodeDecodeError, SyntaxError) as e:
        raise ValueError("Upstream source not readable syntax") from e
    extracted = {}
    for name, report_key in VERSION_MAP_NAMES.items():
        variable = "class_map_5_parts" if name == "class_map_part_ribs" else "class_map"
        mapping = literal_submap(tree, variable, name)
        expected = expected_rib_map(RIB_BASE[report_key])
        observed = {k:v for k,v in mapping.items() if v.startswith("rib_")}
        if observed != expected:
            raise ValueError(f"Unexpected rib class label or order: {name}")
        extracted[report_key] = {
            "rib_class_id_by_name": {v: k for k, v in sorted(observed.items())},
            "distinct_rib_label_count": len(observed),
            "sternum_class_id": next((i for i, v in mapping.items() if v == "sternum"), None),
            "costal_cartilages_class_id": next((i for i, v in mapping.items()
                                               if v == "costal_cartilages"), None),
        }
    if (extracted["legacy_v1"]["sternum_class_id"] is not None or
            extracted["legacy_v1"]["costal_cartilages_class_id"] is not None or
            extracted["later_total_v2"]["sternum_class_id"] != 116 or
            extracted["later_total_v2"]["costal_cartilages_class_id"] != 117 or
            extracted["later_rib_part"]["sternum_class_id"] != 25 or
            extracted["later_rib_part"]["costal_cartilages_class_id"] != 26):
        raise ValueError("Version-dependent sternum/cartilage map changed")
    caveats = {
        "possible_11_rib_case": "11 ribs" in source,
        "possible_cervical_rib": "Halsrippe" in source,
        "possible_13_rib_case": "13. rib" in source,
    }
    if not all(caveats.values()):
        raise ValueError("Original upstream rib number ambiguity caution missing")
    return {
        "schema_version": 1,
        "kind": "HGPT_NONCANONICAL_UPSTREAM_RIB_CLASS_MAP_VERIFICATION",
        "source_file": f"https://github.com/{SOURCE_REPO}/blob/master/{SOURCE_PATH}",
        "source_git_blob_sha1": expected_blob,
        "read_only_upstream_source_parsed_as_AST_no_code_execution": True,
        "derived_legacy_v1_2022_dataset_mapping_proven": False,
        "individual_subject_rib_presence_proven": False,
        "subject_count_in_scope": 0,
        "all_subjects_typical_12_ribs_each_side_proven": False,
        "rib_segment_labels_anatomical_level_verified": False,
        "sternum_or_cartilage_identity_accepted": False,
        "source_ct_donor_metadata_downloaded": False,
        "patient_ct_masks_downloaded": False,
        "independent_population_targets_selected": False,
        "license_commercial_import_approved": False,
        "cp1_gate6_approved": False,
        "labelled_number_caveats_found": caveats,
        "versioned_maps": extracted,
    }


def validate_source_contract(data: dict) -> None:
    if data.get("kind") != "HGPT_NONCANONICAL_UPSTREAM_RIB_CLASS_MAP_VERIFICATION":
        raise ValueError("Unrecognized source-label report")
    restricted = (
        "derived_legacy_v1_2022_dataset_mapping_proven",
        "individual_subject_rib_presence_proven",
        "all_subjects_typical_12_ribs_each_side_proven",
        "rib_segment_labels_anatomical_level_verified",
        "sternum_or_cartilage_identity_accepted",
        "source_ct_donor_metadata_downloaded",
        "patient_ct_masks_downloaded",
        "independent_population_targets_selected",
        "license_commercial_import_approved",
        "cp1_gate6_approved",
    )
    if any(data.get(k) is not False for k in restricted):
        raise ValueError("Source label contract must never imply anatomical approval")
    if data.get("subject_count_in_scope") != 0:
        raise ValueError("No individual patients were screened")
    maps = data.get("versioned_maps", {})
    for key, base in RIB_BASE.items():
        item = maps.get(key, {})
        if item.get("rib_class_id_by_name") != {
            name: number for number,name in expected_rib_map(base).items()
        } or item.get("distinct_rib_label_count") != 24:
            raise ValueError("Label version or exact rib numbers changed")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--verify-public-source", action="store_true",
                   help="Read only immutable official GitHub source blob metadata")
    args = p.parse_args()
    if not args.verify_public_source:
        p.error("Network source verification requires explicit opt-in")
    try:
        out = extract_contract(source_from_github())
        validate_source_contract(out)
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as e:
        print("Fail-closed independent rib-label check: "+str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
