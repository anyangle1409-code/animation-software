#!/usr/bin/env python3
"""Source-pinned multi-slice HU threshold topology; NOT identified anatomical bone.

Intended for selecting credible regions for independent manual anatomy review:
- evaluate identical physically located ROI at several HU thresholds;
- preserve every disconnected 6-neighbour component, its bounding scanner-RAS
  envelope, slice support and ROI/cutoff contact;
- flag incomplete surfaces; NEVER infer component-to-bone identity.
No source pixel arrays, GE headers, or derived mesh are written to Git.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from ct_pelvis_window_geometry import assert_private_location
from nlm_ct_provisional_surface import (
    GRID, MAX_ROI_SAMPLES, _private_source_slice, component_from_explicit_seed,
)
from nlm_ct_raw_png_calibration import validate_calibration_evidence
from pelvic_ct_series_manifest import validate_series_bundle

NEIGHBOURS = (
    (-1, 0, 0), (1, 0, 0), (0, -1, 0),
    (0, 1, 0), (0, 0, -1), (0, 0, 1),
)
MAX_SELECTED = 350_000


def components_with_bounds(voxels, selected_slices, roi, geometry, first_s, thickness):
    """Count ALL components; expose truncation instead of filtering islands.

    Voxel indices are (slice, image row, image column). Scanner-RAS bounds
    use the outer-FOV-edge assumption, which remains explicitly UNVERIFIED.
    """
    col0, col1, row0, row1 = roi
    tl, tr, br = (geometry[k] for k in (
        "plane_TL_RAS_mm", "plane_TR_RAS_mm", "plane_BR_RAS_mm"))
    dx = [(tr[i] - tl[i]) / GRID for i in range(3)]
    dy = [(br[i] - tr[i]) / GRID for i in range(3)]

    def scanner_xy(c, r):
        return [tl[i] + c * dx[i] + r * dy[i] for i in range(2)]

    remaining = set(voxels)
    result = []
    while remaining:
        q = [remaining.pop()]
        count = 0
        zmin = rmin = cmin = 10**9
        zmax = rmax = cmax = -1
        slice_support = set()
        touches = set()
        while q:
            z, r, c = q.pop()
            count += 1
            slice_support.add(z)
            zmin, zmax = min(zmin, z), max(zmax, z)
            rmin, rmax = min(rmin, r), max(rmax, r)
            cmin, cmax = min(cmin, c), max(cmax, c)
            if z == 0:
                touches.add("source_selection_superior_cut")
            if z == selected_slices - 1:
                touches.add("source_selection_inferior_cut")
            if r == row0:
                touches.add("ROI_row_min_cut")
            if r == row1 - 1:
                touches.add("ROI_row_max_cut")
            if c == col0:
                touches.add("ROI_col_min_cut")
            if c == col1 - 1:
                touches.add("ROI_col_max_cut")
            for dz, dr, dc in NEIGHBOURS:
                n = (z + dz, r + dr, c + dc)
                if n in remaining:
                    remaining.remove(n)
                    q.append(n)
        # Include full voxel cell and axial slab, not just centre samples.
        corners = [
            scanner_xy(c, r)
            for c in (cmin, cmax + 1)
            for r in (rmin, rmax + 1)
        ]
        source_slab = [
            first_s - thickness * (zmax + 0.5),
            first_s - thickness * (zmin - 0.5),
        ]
        result.append({
            "voxel_count": count,
            "scanner_RAS_outer_edge_assumption_bounds_mm": {
                "R": [min(p[0] for p in corners), max(p[0] for p in corners)],
                "A": [min(p[1] for p in corners), max(p[1] for p in corners)],
                "S": source_slab,
            },
            "voxel_index_min_max_z_row_col": {
                "min": [zmin, rmin, cmin],
                "max": [zmax, rmax, cmax],
            },
            "source_slice_support_count": len(slice_support),
            "selection_cut_contacts": sorted(touches),
            "complete_object_surface_in_this_selection": False if touches else None,
        })
    result.sort(key=lambda c: (
        -c["voxel_count"],
        c["voxel_index_min_max_z_row_col"]["min"],
    ))
    return result



def seed_relationships(volumes, seeds, selected_slices, roi):
    """Check HU connectivity of *prior hypotheses*, never assign bone identity."""
    col0, col1, row0, row1 = roi
    if len(seeds) < 2 or len(seeds) > 8:
        raise ValueError("compare two through eight independently named review seeds")
    ids = [p["id"] for p in seeds]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate source-linked observation seeds")
    for p in seeds:
        z, r, c = p["voxel_z_row_col"]
        if (type(z) is not int or type(r) is not int or type(c) is not int
                or not 0 <= z < selected_slices
                or not row0 <= r < row1 or not col0 <= c < col1):
            raise ValueError("source-reviewed seed lies outside acquisition/ROI")
    reports = []
    for hu, voxels in sorted(volumes.items()):
        hits = []
        comps = {}
        for p in seeds:
            original = tuple(p["voxel_z_row_col"])
            if original not in voxels:
                hits.append({
                    "id": p["id"], "voxel_z_row_col": list(original),
                    "seed_meets_threshold": False,
                    "connected_voxels": None,
                    "selection_boundary_contacts": [],
                })
                continue
            component = component_from_explicit_seed(voxels, original)
            comps[p["id"]] = component
            cuts = set()
            for z, r, c in component:
                if z == 0 or z == selected_slices-1:
                    cuts.add("source_selection_end")
                if r == row0 or r == row1-1 or c == col0 or c == col1-1:
                    cuts.add("ROI_edge")
            hits.append({
                "id": p["id"], "voxel_z_row_col": list(original),
                "seed_meets_threshold": True,
                "connected_voxels": len(component),
                "selection_boundary_contacts": sorted(cuts),
            })
        pairs = []
        for i, a in enumerate(seeds):
            for b in seeds[i+1:]:
                if a["id"] in comps and b["id"] in comps:
                    same = tuple(b["voxel_z_row_col"]) in comps[a["id"]]
                else:
                    same = None
                pairs.append({
                    "id_a": a["id"],
                    "id_b": b["id"],
                    "same_HU_connected_component": same,
                    "separate_anatomical_bones_proven": False,
                })
        reports.append({
            "HU": hu,
            "review_seeds": hits,
            "pairwise_HU_connectivity": pairs,
            "HU_component_is_NOT_anatomical_bone": True,
        })
    return reports


def analyze_pixels(pixel_layers, geometry, first_s, roi, thresholds_hu, review_seeds=None):
    """Analyze actual decoded PNG stored-scalar layers or deterministic fixtures."""
    if not isinstance(thresholds_hu, (list, tuple)) or not 2 <= len(thresholds_hu) <= 6:
        raise ValueError("require two through six CT thresholds")
    if (any(type(v) is not int or v < -1024 or v > 3000 for v in thresholds_hu)
            or list(thresholds_hu) != sorted(set(thresholds_hu))):
        raise ValueError("HU thresholds must be distinct ascending integers")
    col0, col1, row0, row1 = roi
    if not (0 <= col0 < col1 <= GRID and 0 <= row0 < row1 <= GRID):
        raise ValueError("invalid source ROI")
    layers = len(pixel_layers)
    if layers < 2 or layers * (col1-col0) * (row1-row0) > MAX_ROI_SAMPLES:
        raise ValueError("ROI/slice selection exceeds reconstruction budget")
    volumes = {t: set() for t in thresholds_hu}
    for z, image in enumerate(pixel_layers):
        if len(image) != GRID * GRID:
            raise ValueError("decoded source image grid must be 512 squared")
        for row in range(row0, row1):
            offset = row * GRID
            for col in range(col0, col1):
                scalar = image[offset + col]
                for hu in thresholds_hu:
                    if scalar >= hu + 1024:
                        volumes[hu].add((z, row, col))
                        if len(volumes[hu]) > MAX_SELECTED:
                            raise ValueError("candidate volume too large to review")
    result = []
    for hu in thresholds_hu:
        voxels = volumes[hu]
        components = components_with_bounds(
            voxels, layers, roi, geometry, first_s, 3.0
        ) if voxels else []
        result.append({
            "HU": hu,
            "stored_value_minimum": hu + 1024,
            "voxel_count": len(voxels),
            "component_count_6_neighbour": len(components),
            "largest_components": components[:20],
            "smaller_components_not_discarded": max(0, len(components) - 20),
            "component_selection_or_anatomical_identity_accepted": False,
        })
    comparisons = []
    for lo, hi in zip(thresholds_hu, thresholds_hu[1:]):
        low, high = volumes[lo], volumes[hi]
        if not high.issubset(low):
            raise ValueError("CT threshold monotonicity violated")
        comparisons.append({
            "HU_low": lo,
            "HU_high": hi,
            "global_occupancy_Jaccard": len(high) / len(low) if low else None,
            "voxels_lost_at_higher_threshold": len(low) - len(high),
            "individual_anatomical_surface_stability_verified": False,
        })
    evidence = {"thresholds": result, "comparisons": comparisons}
    if review_seeds is not None:
        evidence["proposed_point_HU_connectivity_not_anatomical_identity"] = seed_relationships(
            volumes, review_seeds, layers, roi)
    return evidence


def run(args):
    source = assert_private_location(args.ct_dir)
    out = assert_private_location(args.out)
    if out.exists():
        raise ValueError("refuse to overwrite private CT review evidence")
    bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    calibration = json.loads(Path(args.calibration).read_text(encoding="utf-8"))
    validate_series_bundle(bundle)
    validate_calibration_evidence(calibration, bundle)
    if args.group not in (1, 2):
        raise ValueError("keep acquisition groups separate")
    rows = bundle["series"][args.group - 1]["slices"]
    if args.start < 0 or args.count < 2 or args.start + args.count > len(rows):
        raise ValueError("source selection must stay within a single contiguous group")
    chosen = rows[args.start:args.start + args.count]
    first_s = chosen[0]["scanner_centre_RAS_mm"][2]
    layers, first_geometry = [], None
    for z, row in enumerate(chosen):
        if abs(row["scanner_centre_RAS_mm"][2] - (first_s - 3*z)) > 1e-6:
            raise ValueError("source slice physical ordering changed")
        geometry, pixels = _private_source_slice(source, row)
        if first_geometry is None:
            first_geometry = geometry
        else:
            for field in ("plane_TL_RAS_mm", "plane_TR_RAS_mm",
                          "plane_BR_RAS_mm"):
                if any(abs(geometry[field][axis] - first_geometry[field][axis]) > .01
                       for axis in (0, 1)):
                    raise ValueError("scanner plane XY geometry changed")
        layers.append(pixels)
    chosen_review_ids = getattr(args, "seed_observation", None)
    seeds = None
    if chosen_review_ids:
        if len(chosen_review_ids) < 2 or not getattr(args, "review", None):
            raise ValueError("two source-linked observation IDs and original review evidence required")
        review = json.loads(Path(args.review).read_text(encoding="utf-8"))
        if review.get("kind") != "NLM_CT_ANATOMICAL_REVIEW_PACKET":
            raise ValueError("unrecognised source observation packet")
        source_map = {row["source_id"]: (idx, row)
                      for idx, row in enumerate(chosen)}
        found = {}
        for obs in review["observations"]:
            key = obs["observation_id"]
            if key not in chosen_review_ids:
                continue
            if key in found:
                raise ValueError("duplicate source candidate identifier")
            if obs["source_id"] not in source_map:
                raise ValueError("review seed source outside selected original acquisition")
            z, row = source_map[obs["source_id"]]
            if (obs["source_png_sha256"] != row["source_png_sha256"]
                    or obs["source_header_sha256"] != row["source_header_sha256"]
                    or abs(obs["scanner_S_mm"] - row["scanner_centre_RAS_mm"][2]) > 1e-5):
                raise ValueError("review seed CT source pin mismatch")
            found[key] = {
                "id": key,
                "voxel_z_row_col": [z, obs["pixel"]["row"], obs["pixel"]["column"]],
            }
        if len(found) != len(set(chosen_review_ids)):
            raise ValueError("missing source candidate observation")
        seeds = [found[key] for key in chosen_review_ids]
    analysis = analyze_pixels(layers, first_geometry, first_s, args.roi, args.hu, seeds)
    report = {
        "schema_version": 1,
        "kind": "REAL_CT_MULTI_SLICE_HU_TOPOLOGY_NOT_BONE_IDENTIFICATION",
        "source_ids": [row["source_id"] for row in chosen],
        "source_png_sha256": [row["source_png_sha256"] for row in chosen],
        "group": args.group,
        "scanner_S_centres_mm": [row["scanner_centre_RAS_mm"][2] for row in chosen],
        "ROI_col_start_stop_row_start_stop": args.roi,
        "scanner_frame": "SCANNER_RAS_MM",
        "thresholds_in_verified_HU": True,
        "pixel_centre_convention_verified": False,
        "outer_edge_RAS_bounds_are_conditional": True,
        "ROI_and_selection_truncation_must_be_reviewed": True,
        "anatomical_bone_identity_verified": False,
        "seven_pelvic_landmarks_verified": 0,
        "scanner_to_HGPT_registration_verified": False,
        "canonical_promotion_allowed": False,
        "original_CT_or_header_bytes_exported": False,
        **analysis,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as fp:
        json.dump(report, fp, indent=2, sort_keys=True)
        fp.write("\n")
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ct-dir", required=True)
    p.add_argument("--bundle", required=True)
    p.add_argument("--calibration", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--group", type=int, required=True)
    p.add_argument("--start", type=int, required=True)
    p.add_argument("--count", type=int, required=True)
    p.add_argument("--roi", type=int, nargs=4, required=True,
                   metavar=("COL0", "COL1", "ROW0", "ROW1"))
    p.add_argument("--hu", type=int, nargs="+", required=True)
    p.add_argument("--review", help="original candidate evidence file; required for seed comparisons")
    p.add_argument("--seed-observation", action="append", help="exact original observation ID; repeat for pairwise CT connectivity")
    args = p.parse_args()
    report = run(args)
    print(json.dumps({
        "kind": report["kind"], "source_ids": report["source_ids"],
        "threshold_results": [
            {"HU": s["HU"], "voxels": s["voxel_count"],
             "components": s["component_count_6_neighbour"],
             "largest_component_voxels": (
                 s["largest_components"][0]["voxel_count"] if s["largest_components"] else 0),
             "largest_component_cut_contacts": (
                 s["largest_components"][0]["selection_cut_contacts"] if s["largest_components"] else []),
            } for s in report["thresholds"]
        ],
        "comparisons": report["comparisons"],
        "canonical_promotion_allowed": report["canonical_promotion_allowed"],
        "point_connectivity": report.get("proposed_point_HU_connectivity_not_anatomical_identity"),
    }, indent=2))


if __name__ == "__main__":
    main()
