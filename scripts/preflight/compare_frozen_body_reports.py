#!/usr/bin/env python3
"""Compare mesh, weights and corrective shape keys in two read-only Blender reports.

Example:
python scripts/preflight/compare_frozen_body_reports.py \
  --source f23d_report.json --candidate f83a_report.json \
  --source-object HGPT_Female_Body \
  --candidate-object HGPT_Female_Body_F23d_REFERENCE_LOCKED

Object names are deliberately explicit. This tool never edits either checkpoint.
"""
import argparse
import json
import sys


def load(path):
    with open(path, encoding="utf-8") as source:
        return json.load(source)


def find(report, name):
    candidates = {obj["name"]: obj for obj in report.get("mesh_objects", [])}
    if name not in candidates:
        raise ValueError(
            f"{name!r} not found in {report.get('source_path')}. "
            f"Available meshes: {list(candidates)}"
        )
    return candidates[name]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True)
    p.add_argument("--candidate", required=True)
    p.add_argument("--source-object", required=True)
    p.add_argument("--candidate-object", required=True)
    args = p.parse_args()
    source_report = load(args.source)
    cand_report = load(args.candidate)
    source = find(source_report, args.source_object)
    candidate = find(cand_report, args.candidate_object)
    checks = {}
    for field in ("vertex_count", "edge_count", "polygon_count",
                  "geometry_sha256", "weights_sha256", "shape_keys_sha256"):
        checks[field] = {"equal": source.get(field) == candidate.get(field),
                         "source": source.get(field),
                         "candidate": candidate.get(field)}
    result = {
        "purpose": "Preservation of protected F23d source inside F83a",
        "source_checkpoint_sha256": source_report.get("source_sha256"),
        "candidate_checkpoint_sha256": cand_report.get("source_sha256"),
        "source_object": args.source_object,
        "candidate_object": args.candidate_object,
        "checks": checks,
        "all_equal": all(item["equal"] for item in checks.values()),
    }
    print(json.dumps(result, indent=2))
    if not result["all_equal"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
