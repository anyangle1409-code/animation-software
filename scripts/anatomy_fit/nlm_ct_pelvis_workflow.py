#!/usr/bin/env python3
"""Run the noncanonical NLM pelvic CT evidence workflow on local inputs."""
import argparse
import copy
import json
import sys
from pathlib import Path

import nlm_ct_anatomical_review as anatomical_review
import nlm_ct_candidate_segmentation as candidate_segmentation
import nlm_ct_landmark_validation as landmark_validation


def _scanner_records(value):
    if not isinstance(value, dict):
        raise ValueError("scanner_by_source must be an object")
    records = {}
    for key, record in value.items():
        if type(key) is int:
            source_id = key
        elif isinstance(key, str) and key.isdigit():
            source_id = int(key)
        else:
            raise ValueError("scanner source IDs must be integers")
        if source_id in records:
            raise ValueError("duplicate scanner source ID")
        records[source_id] = record
    return records


def _unique(values):
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def run_workflow(inputs: dict) -> dict:
    """Compose review, sparse segmentation, and landmark validators."""
    if not isinstance(inputs, dict):
        raise ValueError("workflow inputs must be a JSON object")
    if inputs.get("canonical_output_requested") is not False:
        raise ValueError("canonical output is prohibited for candidate CT evidence")

    manifest = inputs.get("pinned_manifest")
    scanners = _scanner_records(inputs.get("scanner_by_source"))
    review = anatomical_review.validate_review_packet(
        inputs.get("review_packet"), manifest
    )
    segmentation = candidate_segmentation.validate_candidate_segmentation(
        inputs.get("segmentation_packet"), review, scanners
    )
    landmarks = landmark_validation.validate_landmarks(
        inputs.get("landmark_packet"), review, segmentation, scanners
    )

    safe_observations = [{
        "observation_id": item["observation_id"],
        "source_id": item["source_id"],
        "source_png_sha256": item["source_png_sha256"],
        "source_header_sha256": item["source_header_sha256"],
        "scanner_S_mm": item["scanner_S_mm"],
        "pixel": copy.deepcopy(item["pixel"]),
        "candidate_label": item["candidate_label"],
        "confidence": item["confidence"],
        "reviewer_id": item["reviewer_id"],
    } for item in review["observations"]]
    unmet = _unique(
        list(review["unmet_gates"])
        + list(segmentation["unmet_gates"])
        + list(landmarks["unmet_gates"])
    )
    return {
        "schema_version": 1,
        "kind": "NLM_PELVIC_CT_IDENTIFICATION_SEGMENTATION_LANDMARK_REPORT",
        "status": "CANDIDATE_EVIDENCE_ONLY",
        "source_skeleton_governs_geometry": True,
        "canonical_promotions": 0,
        "canonical_promotion_allowed": False,
        "source_image_or_header_bytes_copied": False,
        "missing_full_volume_coverage": True,
        "stage_evidence": {
            "anatomical_review": {
                "status": review["anatomical_status"],
                "observations": safe_observations,
                "citations": copy.deepcopy(review["citations"]),
            },
            "candidate_segmentation": {
                "candidate_label": segmentation["candidate_label"],
                "source_ids": list(segmentation["source_ids"]),
                "voxel_count": segmentation["voxel_count"],
                "connected_component_count_6_neighbour":
                    segmentation["connected_component_count_6_neighbour"],
                "sample_centre_bounds_RAS_mm":
                    copy.deepcopy(segmentation["sample_centre_bounds_RAS_mm"]),
                "coverage_complete": False,
                "bone_surface_segmentation_verified": False,
                "coverage_gaps": list(segmentation["coverage_gaps"]),
            },
            "candidate_landmarks": {
                "count": len(landmarks["landmarks"]),
                "all_landmarks_verified": False,
                "landmarks": copy.deepcopy(landmarks["landmarks"]),
            },
        },
        "unmet_gates": unmet,
    }


def load_inputs(path):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("workflow input must be a JSON object")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True,
                        help="private local workflow bundle JSON")
    parser.add_argument("--out", type=Path,
                        help="exclusive-create privacy-safe report JSON")
    parser.add_argument("--request-canonical-output", action="store_true",
                        help="always refused; candidate evidence cannot be canonical")
    args = parser.parse_args(argv)
    try:
        inputs = load_inputs(args.input)
        if args.request_canonical_output:
            inputs["canonical_output_requested"] = True
        report = run_workflow(inputs)
        text = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.out:
            with args.out.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(text)
        else:
            print(text, end="")
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"workflow refused input: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
