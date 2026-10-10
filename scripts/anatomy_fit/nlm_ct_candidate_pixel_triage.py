#!/usr/bin/env python3
"""Audit proposed NLM pelvic CT image pixels against source-pinned HU data.

A candidate image-point is NOT a verified anatomical landmark or suitable
bone-surface seed.  Its pixel may show soft tissue, cortex, a joint gap, or
artefact.  This script reports both centre HU and neighbourhood occupancy,
exactly bound to the source/GE headers, for independent human image review.

One scanner acquisition group per invocation. Never co-register the groups,
export medical images, overwrite previous private reports, or update anatomy.
"""
import argparse
import json
from pathlib import Path

from ct_pelvis_window_geometry import assert_private_location
from nlm_ct_provisional_surface import GRID, _private_source_slice
from nlm_ct_raw_png_calibration import validate_calibration_evidence
from pelvic_ct_series_manifest import validate_series_bundle

HU_OFFSET = -1024
THRESHOLDS = (150, 300, 500, 700)
NEIGHBOR_RADIUS = 2


def point_ras(geometry, row, col, pixel_center_assumption):
    """Pixel centre with either permissible, currently UNVERIFIED FOV origin."""
    if pixel_center_assumption not in ("outer_edge", "first_pixel_centre"):
        raise ValueError("pixel centre convention must remain explicit")
    tl = geometry["plane_TL_RAS_mm"]
    tr = geometry["plane_TR_RAS_mm"]
    br = geometry["plane_BR_RAS_mm"]
    shift = .5 if pixel_center_assumption == "outer_edge" else 0.
    return [
        tl[i] + (col + shift) * (tr[i]-tl[i]) / GRID
              + (row + shift) * (br[i]-tr[i]) / GRID
        for i in range(3)
    ]


def audit_pixel(observation, source, geometry, pixels):
    """Compute a non-acceptance review record from exactly ONE pinned CT slice."""
    if len(pixels) != GRID * GRID:
        raise ValueError("CT image size mismatched before anatomical review")
    identity = observation["observation_id"]
    if not isinstance(identity, str) or not identity:
        raise ValueError("candidate observation identifier missing")
    pixel = observation["pixel"]
    row, col = pixel["row"], pixel["column"]
    if (type(row) is not int or type(col) is not int
            or not 0 <= row < GRID or not 0 <= col < GRID):
        raise ValueError("candidate image pixel outside original source frame")
    ras_a = point_ras(geometry, row, col, "outer_edge")
    ras_b = point_ras(geometry, row, col, "first_pixel_centre")
    if abs(ras_a[2] - observation["scanner_S_mm"]) > 1e-5:
        raise ValueError("candidate point scanner plane disagrees with source")
    centre_hu = pixels[row * GRID + col] + HU_OFFSET
    nearby = [
        pixels[r * GRID + c] + HU_OFFSET
        for r in range(max(0, row - NEIGHBOR_RADIUS),
                       min(GRID, row + NEIGHBOR_RADIUS + 1))
        for c in range(max(0, col - NEIGHBOR_RADIUS),
                       min(GRID, col + NEIGHBOR_RADIUS + 1))
    ]
    if not nearby or not -1024 <= centre_hu <= 65535-1024:
        raise ValueError("unusable source sample")
    lowered = identity.lower()
    if "-right-" in lowered and "-left-" in lowered:
        raise ValueError("ambiguous original observation laterality")
    side = ("R" if "-right-" in lowered else
            "L" if "-left-" in lowered else "unspecified")
    # RAS positive R means patient's right, not image right.
    if side == "R":
        laterality = ras_a[0] > 0 and ras_b[0] > 0
    elif side == "L":
        laterality = ras_a[0] < 0 and ras_b[0] < 0
    else:
        laterality = None

    threshold_support = [
        {
            "minimum_HU": hu,
            "centre_sample_passes": centre_hu >= hu,
            "five_by_five_samples_passing": sum(v >= hu for v in nearby),
            "five_by_five_sample_count": len(nearby),
        }
        for hu in THRESHOLDS
    ]
    return {
        "observation_id": identity,
        "provisional_label_from_prior_report_not_anatomy": observation["candidate_label"],
        "source_id": source["source_id"],
        "source_png_sha256": source["source_png_sha256"],
        "source_header_sha256": source["source_header_sha256"],
        "pixel": {"row": row, "column": col},
        "scanner_S_mm": source["scanner_centre_RAS_mm"][2],
        "scanner_RAS_mm_if_FOV_corners_are_outer_edges": ras_a,
        "scanner_RAS_mm_if_first_pixel_is_at_FOV_corner": ras_b,
        "voxel_centre_origin_convention_verified": False,
        "point_source_stored_scalar": pixels[row * GRID + col],
        "point_HU_from_verified_addend": centre_hu,
        "five_by_five_HU_range": [min(nearby), max(nearby)],
        "five_by_five_neighbourhood_threshold_support": threshold_support,
        "proposed_laterality": side,
        "source_R_sign_consistent_with_proposed_side": laterality,
        "source_pixel_confirms_anatomical_bone_identity": False,
        "suitable_seed_for_full_bone_surface_verified": False,
        "independent_anatomist_review_required": True,
    }


def triage(bundle, calibration, review, group, source_dir, source_loader=None):
    """Validate manifest/observation provenance before reading each unique source."""
    validate_series_bundle(bundle)
    validate_calibration_evidence(calibration, bundle)
    if type(group) is not int or group not in (1, 2):
        raise ValueError("only a single verified original acquisition group")
    if review.get("kind") != "NLM_CT_ANATOMICAL_REVIEW_PACKET":
        raise ValueError("not an original source-linked CT review packet")
    if not isinstance(review.get("observations"), list) or not review["observations"]:
        raise ValueError("no source-bound observations")
    source_rows = {x["source_id"]: x for x in bundle["series"][group-1]["slices"]}
    all_sources = {
        x["source_id"]: (g, x)
        for g, series in enumerate(bundle["series"], 1) for x in series["slices"]
    }
    source_dir = assert_private_location(source_dir)
    if source_loader is None:
        source_loader = _private_source_slice
    selected = []
    seen = set()
    for obs in review["observations"]:
        sid = obs["source_id"]
        if sid not in all_sources:
            raise ValueError("candidate source missing from pinned original CT series")
        source_group, row = all_sources[sid]
        if obs["observation_id"] in seen:
            raise ValueError("duplicate original candidate observation identifier")
        seen.add(obs["observation_id"])
        if (obs["source_png_sha256"] != row["source_png_sha256"]
                or obs["source_header_sha256"] != row["source_header_sha256"]
                or abs(obs["scanner_S_mm"] - row["scanner_centre_RAS_mm"][2]) > 1e-5):
            raise ValueError("candidate source pin or scanner position disagrees")
        if source_group == group:
            selected.append((obs, source_rows[sid]))
    cache = {}
    records = []
    for obs, manifest_row in selected:
        sid = manifest_row["source_id"]
        if sid not in cache:
            geom, pixels = source_loader(source_dir, manifest_row)
            if abs(geom["scanner_S_mm"] - manifest_row["scanner_centre_RAS_mm"][2]) > 1e-5:
                raise ValueError("original scanner header S position changed")
            cache[sid] = (geom, pixels)
        records.append(audit_pixel(obs, manifest_row, *cache[sid]))
    if not records:
        raise ValueError("no source-linked candidates for requested group")
    summary = {
        "observations": len(records),
        "source_slices_read_once": len(cache),
        "centre_passes_by_HU": {
            str(h): sum(row["point_HU_from_verified_addend"] >= h for row in records)
            for h in THRESHOLDS
        },
        "centre_fails_300_HU": [
            row["observation_id"] for row in records
            if row["point_HU_from_verified_addend"] < 300
        ],
        "declared_side_disagreements": [
            row["observation_id"] for row in records
            if row["source_R_sign_consistent_with_proposed_side"] is False
        ],
    }
    return {
        "schema_version": 1,
        "kind": "SOURCE_PINNED_PELVIC_PIXEL_CANDIDATE_TRIAGE_NOT_ANATOMICAL_ACCEPTANCE",
        "acquisition_group": group,
        "verified_source_HU_addend": HU_OFFSET,
        "scanner_coordinate_frame": "ORIGINAL_SCANNER_RAS_MM",
        "pixel_centre_origin_convention_verified": False,
        "scanner_to_canonical_skeleton_transform_verified": False,
        "required_pelvic_bony_landmarks_anatomically_accepted": 0,
        "anatomical_bone_geometry_or_surface_verified": False,
        "canonical_promotion_allowed": False,
        "reviewer_original_confidence_not_substituted_for_evidence": True,
        "original_medical_image_or_header_bytes_exported": False,
        "observations": records,
        "summary": summary,
    }


def run(args):
    destination = assert_private_location(args.out)
    if destination.exists():
        raise ValueError("cannot overwrite a previous private anatomy review")
    bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    cal = json.loads(Path(args.calibration).read_text(encoding="utf-8"))
    review = json.loads(Path(args.review).read_text(encoding="utf-8"))
    report = triage(bundle, cal, review, args.group, args.ct_dir)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as fp:
        json.dump(report, fp, sort_keys=True, indent=2)
        fp.write("\n")
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ct-dir", required=True)
    p.add_argument("--group", type=int, required=True)
    p.add_argument("--bundle", required=True)
    p.add_argument("--calibration", required=True)
    p.add_argument("--review", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    report = run(args)
    print(json.dumps({
        "kind": report["kind"],
        "acquisition_group": report["acquisition_group"],
        "summary": report["summary"],
        "candidate_observations": [
            {"id": v["observation_id"],
             "pixel_HU": v["point_HU_from_verified_addend"],
             "nearby_HU_range": v["five_by_five_HU_range"],
             "laterality": v["source_R_sign_consistent_with_proposed_side"],
             "passes_HU": [s["minimum_HU"] for s in
                           v["five_by_five_neighbourhood_threshold_support"]
                           if s["centre_sample_passes"]]}
            for v in report["observations"]
        ],
        "anatomical_bone_geometry_or_surface_verified": False,
    }, indent=2))


if __name__ == "__main__":
    main()
