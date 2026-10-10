#!/usr/bin/env python3
"""Extract SOURCE-PINNED, HU-calibrated provisional CT voxel surfaces for private Blender review.

A thresholded connected voxel set is NOT a segmented anatomical bone. The script
never labels anatomy, modifies the canonical skeleton, or authorizes promotion.
Each extraction is confined to one original NLM acquisition group and a bounded
ROI. Outputs remain outside the repository and use an explicit pixel-origin
assumption; voxel-to-scanner origin ambiguity is not silently resolved.

Example:
  python scripts/anatomy_fit/nlm_ct_provisional_surface.py \
    --ct-dir /private/nlm_ct --group 1 --start 0 --count 3 \
    --roi 200 260 180 240 --hu-min 300 \
    --bundle ORIGINAL_V1_WORK/anatomy/audit/nlm_pelvic_ct_full_series_candidate_bundle_20261009.json \
    --calibration ORIGINAL_V1_WORK/anatomy/audit/nlm_pelvic_ct_full_series_hu_calibration_20261009.json \
    --out /private/review/ct_candidate.obj
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from ct_pelvis_window_geometry import (
    assert_private_location, decode_png_gray16, parse_scanner_header,
)
from nlm_ct_raw_png_calibration import validate_calibration_evidence
from pelvic_ct_series_manifest import validate_series_bundle

GRID = 512
MAX_ROI_SAMPLES = 4_000_000
MAX_OCCUPIED_VOXELS = 150_000

# Directions are (slice, row, column), with slice increasing inferiorly.
FACE_DEFS = (
    ((0, 0, -1), ((0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0))),
    ((0, 0, 1), ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1))),
    ((0, -1, 0), ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1))),
    ((0, 1, 0), ((0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0))),
    ((-1, 0, 0), ((0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0))),
    ((1, 0, 0), ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1))),
)


def _sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def component_sizes(occupied):
    remaining = set(occupied)
    counts = []
    while remaining:
        pending = [remaining.pop()]
        size = 0
        while pending:
            z, r, c = pending.pop()
            size += 1
            for dz, dr, dc in (v[0] for v in FACE_DEFS):
                neighbour = (z + dz, r + dr, c + dc)
                if neighbour in remaining:
                    remaining.remove(neighbour)
                    pending.append(neighbour)
        counts.append(size)
    return sorted(counts, reverse=True)


def make_surface(occupied, scanner_geometry, first_s_mm, thickness_mm=3.0,
                 pixel_origin="outer_edge"):
    """Return oriented, deduplicated voxel boundary quads in scanner RAS mm.

    Geometry describes the FIRST source slice; subsequent slices must already
    have been verified to share its XY corners and to descend by thickness_mm.
    A face-only boundary is not automatically manifold or anatomically valid.
    """
    if pixel_origin not in ("outer_edge", "first_pixel_centre"):
        raise ValueError("pixel origin must be a named, unverified assumption")
    if not occupied or len(occupied) > MAX_OCCUPIED_VOXELS:
        raise ValueError("empty or oversized provisional voxel selection")
    if not math.isfinite(first_s_mm) or thickness_mm <= 0:
        raise ValueError("invalid source slab")
    tl = scanner_geometry["plane_TL_RAS_mm"]
    tr = scanner_geometry["plane_TR_RAS_mm"]
    br = scanner_geometry["plane_BR_RAS_mm"]
    ux = [(tr[i] - tl[i]) / GRID for i in range(3)]
    uy = [(br[i] - tr[i]) / GRID for i in range(3)]
    if any(abs(ux[2]) > 1e-6 or abs(uy[2]) > 1e-6 for _ in (0,)):
        raise ValueError("only source-verified axial geometry is supported")
    shift = -0.5 if pixel_origin == "first_pixel_centre" else 0.0

    def point(key):
        z, row, col = key
        return (tl[0] + (col + shift) * ux[0] + (row + shift) * uy[0],
                tl[1] + (col + shift) * ux[1] + (row + shift) * uy[1],
                first_s_mm + thickness_mm / 2 - z * thickness_mm)

    expected = {
        (0, 0, -1): [-v for v in ux],
        (0, 0, 1): ux,
        (0, -1, 0): [-v for v in uy],
        (0, 1, 0): uy,
        (-1, 0, 0): [0, 0, 1],
        (1, 0, 0): [0, 0, -1],
    }
    index = {}
    vertices = []
    quads = []
    for z, row, col in sorted(occupied):
        if any(type(v) is not int for v in (z, row, col)) or not (
                z >= 0 and 0 <= row < GRID and 0 <= col < GRID):
            raise ValueError("invalid voxel index")
        for (dz, dr, dc), face in FACE_DEFS:
            if (z + dz, row + dr, col + dc) in occupied:
                continue
            indices = []
            for dcube, rcube, zcube in face:
                key = (z + zcube, row + rcube, col + dcube)
                if key not in index:
                    index[key] = len(vertices) + 1
                    vertices.append(point(key))
                indices.append(index[key])
            a, b, c = (vertices[indices[i] - 1] for i in (0, 1, 2))
            normal = _cross(_sub(b, a), _sub(c, a))
            if _dot(normal, expected[(dz, dr, dc)]) < 0:
                indices.reverse()
            quads.append(tuple(indices))
    return vertices, quads


def component_from_explicit_seed(occupied, seed):
    """Restrict the review OBJ to a source-identified voxel, NEVER auto-rank bones.

    Caller must independently justify the voxel seed using source planes.
    Missing/non-thresholded seeds fail closed rather than choosing the largest.
    """
    if (not isinstance(seed, (tuple, list)) or len(seed) != 3 or
            any(type(v) is not int for v in seed)):
        raise ValueError("review seed must be [slice,row,column] integers")
    seed = tuple(seed)
    if seed not in occupied:
        raise ValueError("explicit review seed is absent from the HU candidate volume")
    selected = {seed}
    pending = [seed]
    while pending:
        z, row, col = pending.pop()
        for offset in (
                (-1, 0, 0), (1, 0, 0), (0, -1, 0),
                (0, 1, 0), (0, 0, -1), (0, 0, 1)):
            item = (z + offset[0], row + offset[1], col + offset[2])
            if item in occupied and item not in selected:
                selected.add(item)
                pending.append(item)
    return selected


def _private_source_slice(ct_dir, row):
    name = row["source_id"]
    png_file = ct_dir / (name + ".png")
    hdr_file = ct_dir / (name + ".txt")
    png = png_file.read_bytes()
    hdr = hdr_file.read_bytes()
    if (len(png) != row["source_png_bytes"] or
            hashlib.sha256(png).hexdigest() != row["source_png_sha256"] or
            hashlib.sha256(hdr).hexdigest() != row["source_header_sha256"]):
        raise ValueError(name + ": source PNG/header does not match original pin")
    geometry = parse_scanner_header(hdr)
    if abs(geometry["scanner_S_mm"] - row["scanner_centre_RAS_mm"][2]) > 1e-5:
        raise ValueError(name + ": scanner S differs from source manifest")
    width, height, pixels = decode_png_gray16(png)
    if (width, height, len(pixels)) != (GRID, GRID, GRID * GRID):
        raise ValueError(name + ": invalid CT pixel dimensions")
    return geometry, pixels


def extract(args):
    source = Path(args.ct_dir)
    destination = Path(args.out)
    assert_private_location(source)
    assert_private_location(destination)
    if source.resolve() == destination.resolve() or destination.exists():
        raise ValueError("output must be a new private OBJ file")
    sidecar = destination.with_suffix(destination.suffix + ".json")
    if sidecar.exists():
        raise ValueError("output evidence file already exists")
    bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    calibration = json.loads(Path(args.calibration).read_text(encoding="utf-8"))
    validate_series_bundle(bundle)
    validate_calibration_evidence(calibration, bundle)
    if args.group not in (1, 2):
        raise ValueError("acquisition group must be 1 or 2; never bridge groups")
    rows = bundle["series"][args.group - 1]["slices"]
    if args.start < 0 or args.count < 2 or args.start + args.count > len(rows):
        raise ValueError("selection must include consecutive slices in one group")
    col0, col1, row0, row1 = args.roi
    if not (0 <= col0 < col1 <= GRID and 0 <= row0 < row1 <= GRID):
        raise ValueError("ROI must be a bounded image rectangle")
    if (col1 - col0) * (row1 - row0) * args.count > MAX_ROI_SAMPLES:
        raise ValueError("ROI exceeds bounded candidate extraction budget")
    if type(args.hu_min) is not int or not -1024 <= args.hu_min <= 3000:
        raise ValueError("invalid candidate HU threshold")
    threshold = args.hu_min + 1024
    chosen = rows[args.start:args.start + args.count]
    occupied = set()
    first_geometry = None
    first_s = chosen[0]["scanner_centre_RAS_mm"][2]
    step = bundle["series"][args.group - 1]["expected_step_S_mm"]
    if abs(step + 3.0) > 1e-6:
        raise ValueError("source group not on the verified 3 mm acquisition grid")
    for z, row in enumerate(chosen):
        if abs(row["scanner_centre_RAS_mm"][2] - (first_s - 3.0 * z)) > 1e-6:
            raise ValueError("source scanner slices are not a contiguous 3 mm run")
        geometry, pixels = _private_source_slice(source, row)
        if first_geometry is None:
            first_geometry = geometry
        else:
            for field in ("plane_TL_RAS_mm", "plane_TR_RAS_mm",
                          "plane_BR_RAS_mm"):
                if any(abs(geometry[field][i] - first_geometry[field][i]) > .01
                       for i in (0, 1)):
                    raise ValueError("mixed XY corner geometry across CT slices")
        for r in range(row0, row1):
            base = GRID * r
            for c in range(col0, col1):
                if pixels[base + c] >= threshold:
                    occupied.add((z, r, c))
                    if len(occupied) > MAX_OCCUPIED_VOXELS:
                        raise ValueError("selection exceeds provisional geometry cap")
    if not occupied:
        raise ValueError("no thresholded voxels; no source surface to export")
    original_voxel_count = len(occupied)
    original_components = component_sizes(occupied)
    explicit_seed = getattr(args, "seed", None)
    if explicit_seed is not None:
        occupied = component_from_explicit_seed(occupied, explicit_seed)
    selected_cuts = set()
    for z, row, col in occupied:
        if z == 0:
            selected_cuts.add("source_selection_superior_cut")
        if z == len(chosen) - 1:
            selected_cuts.add("source_selection_inferior_cut")
        if col == col0:
            selected_cuts.add("ROI_col_min_cut")
        if col == col1 - 1:
            selected_cuts.add("ROI_col_max_cut")
        if row == row0:
            selected_cuts.add("ROI_row_min_cut")
        if row == row1 - 1:
            selected_cuts.add("ROI_row_max_cut")
    vertices, quads = make_surface(
        occupied, first_geometry, first_s,
        chosen[0]["slice_thickness_mm"], args.pixel_origin)
    components = component_sizes(occupied)
    # Nothing is written before all source pins and geometric checks pass.
    evidence = {
        "schema_version": 1,
        "kind": "SOURCE_PINNED_HU_THRESHOLD_VOXEL_BOUNDARY_NOT_BONE_SURFACE",
        "group": args.group,
        "source_ids": [row["source_id"] for row in chosen],
        "source_png_sha256": [row["source_png_sha256"] for row in chosen],
        "threshold_HU": args.hu_min,
        "threshold_stored": threshold,
        "ROI_col_start_stop_row_start_stop": list(args.roi),
        "coordinate_frame": "ORIGINAL_SCANNER_RAS_MM",
        "pixel_origin_assumption_unverified": args.pixel_origin,
        "voxel_count": len(occupied),
        "all_candidate_voxel_count_before_seed": original_voxel_count,
        "all_candidate_components_6_neighbour_before_seed": original_components,
        "selection_mode": "explicit_review_seed" if explicit_seed is not None else "unfiltered",
        "explicit_review_seed_z_row_col": list(explicit_seed) if explicit_seed is not None else None,
        "candidate_voxels_not_in_selected_component": original_voxel_count - len(occupied),
        "selected_boundary_cut_contacts": sorted(selected_cuts),
        "selected_component_proven_complete_anatomical_bone": False,
        "connected_components_6_neighbour": components,
        "vertices": len(vertices),
        "boundary_quads": len(quads),
        "acquisition_boundary_crossed": False,
        "bone_identity_or_surface_verified": False,
        "seven_required_pelvic_landmarks_verified": 0,
        "scanner_to_HGPT_registration_verified": False,
        "canonical_promotion_allowed": False,
        "private_original_pixels_or_headers_exported": False,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as out:
        out.write("# CT intensity-threshold boundary; NOT a validated bone surface\n")
        out.write("# scanner RAS millimetres, pixel origin assumption "
                  + args.pixel_origin + "\n")
        for p in vertices:
            out.write("v %.9f %.9f %.9f\n" % p)
        for face in quads:
            out.write("f %s\n" % " ".join(str(i) for i in face))
    evidence["OBJ_sha256"] = hashlib.sha256(destination.read_bytes()).hexdigest()
    with sidecar.open("x", encoding="utf-8") as out:
        json.dump(evidence, out, indent=2, sort_keys=True)
        out.write("\n")
    return evidence


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ct-dir", required=True)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--calibration", required=True)
    parser.add_argument("--group", type=int, required=True)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--roi", type=int, nargs=4, required=True,
                        metavar=("COL0", "COL1", "ROW0", "ROW1"))
    parser.add_argument("--hu-min", type=int, required=True)
    parser.add_argument("--pixel-origin", default="outer_edge",
                        choices=("outer_edge", "first_pixel_centre"))
    parser.add_argument("--out", required=True)
    parser.add_argument("--seed", type=int, nargs=3,
                        metavar=("SLICE", "ROW", "COL"),
                        help="explicit reviewer-selected occupied voxel; never auto-select largest component")
    args = parser.parse_args(argv)
    print(json.dumps(extract(args), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
