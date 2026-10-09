#!/usr/bin/env python3
"""Source-pinned 72-slice GE CT row/column orientation integrity preflight.

The prior full-series bundle checks source hashes, slice centres, spacing,
thickness and NORMAL, but not the two actual image in-plane axes. A frame
can be silently rotated 90 or 180 degrees about its normal while passing
those conditions, producing a scrambled 3D bony surface.

Download only the matching original NLM scanner text HEADERS transiently,
validate exact SHA-256 against the existing 72-slice source manifest and
extract ONLY scanner numerical fields with the existing privacy-safe parser.
Use exact scanner T-L/T-R/B-R geometry to check in-plane orientation,
left/right handedness, axial normal, field centre and spacing on EACH slice.

This audit does not download image pixels, infer anatomical labels, calibrate
CT Hounsfield units, resolve pixel edge/centre convention, segment bones or
register patient RAS to the HomeGymPT world. It NEVER changes a source bone.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import re

import nlm_ct_scanner_geometry_header as scan
import nlm_pelvis_region_scout as scout
import pelvic_ct_series_manifest as series

SOURCE_RE = re.compile(r"cvm[0-9]{4}f\Z")
EPS_MM = 0.001
AXIS_TOL = 0.0001
MAX_SOURCES = 200


def _sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def _dot(a, b):
    return sum(x*y for x,y in zip(a,b))


def _norm(a):
    return math.sqrt(_dot(a,a))


def _cross(a,b):
    return [a[1]*b[2]-a[2]*b[1],
            a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0]]


def _unit(v):
    n = _norm(v)
    if n <= 0 or not math.isfinite(n):
        raise ValueError("invalid scanner image axis")
    return [x/n for x in v]


def _near(a,b,tol=EPS_MM):
    return len(a)==len(b) and all(abs(x-y)<=tol for x,y in zip(a,b))


def _orientation(header, expected_row):
    if header["image_dimensions"] != expected_row["scanner_grid"]:
        raise ValueError("scanner header image grid differs from pinned series")
    if not _near(header["pixel_spacing_mm"], expected_row["pixel_spacing_mm"]):
        raise ValueError("scanner in-plane spacing differs from pinned series")
    if abs(header["slice_thickness_mm"]-expected_row["slice_thickness_mm"])>EPS_MM:
        raise ValueError("scanner slice thickness differs from pinned series")
    if not _near(header["reported_plane_centre_RAS_mm"],
                 expected_row["scanner_centre_RAS_mm"]):
        raise ValueError("scanner header RAS centre differs from pinned series")
    tl=header["plane_TL_RAS_mm"]
    tr=header["plane_TR_RAS_mm"]
    br=header["plane_BR_RAS_mm"]
    ex=_unit(_sub(tr,tl))
    ey=_unit(_sub(br,tr))
    normal=_unit(header["normal_RAS"])
    if not _near(normal,expected_row["slice_normal_RAS"],AXIS_TOL):
        raise ValueError("scanner normal differs from pinned series")
    if not _near(_cross(ex,ey),normal,AXIS_TOL):
        raise ValueError("scanner image axes not right-handed with pinned normal")
    if abs(_dot(ex,ey))>AXIS_TOL:
        raise ValueError("scanner image pixel axes not orthogonal")
    return {"x":ex,"y":ey,"normal":normal}


def verify_72_original_headers(bundle, source_headers):
    """Source integrity + orientation; input headers are already SAFELY parsed.

    source_headers: {source_id: {
      'source_header_sha256': raw original source-byte SHA-256,
      'safe_scanner_geometry': scanner_geometry_from_text(raw_bytes)}}
    The raw potentially identifying text must never enter this function.
    """
    before = series.validate_series_bundle(bundle)
    groups = bundle["series"]
    expected = [row for group in groups for row in group["slices"]]
    expected_ids = [row["source_id"] for row in expected]
    if (len(expected) != 72 or len(groups) != 2 or
            len(set(expected_ids)) != 72 or len(expected)>MAX_SOURCES):
        raise ValueError("only the pinned two-group 72-slice CT series is supported")
    if not isinstance(source_headers,dict) or set(source_headers)!=set(expected_ids):
        raise ValueError("every pinned original header must be supplied exactly once")

    first_axes = None
    group_summaries = []
    source_count = 0
    for group_i, group in enumerate(groups,1):
        reference = None
        for row in group["slices"]:
            name=row["source_id"]
            payload=source_headers[name]
            if not isinstance(payload,dict):
                raise ValueError("invalid source scanner-header evidence")
            if payload.get("source_header_sha256") != row["source_header_sha256"]:
                raise ValueError("original NLM GE header byte SHA changed")
            safe=payload.get("safe_scanner_geometry")
            if not isinstance(safe,dict):
                raise ValueError("missing safe scanner geometry")
            axes=_orientation(safe,row)
            if reference is None:
                reference=axes
            elif (not _near(axes["x"],reference["x"],AXIS_TOL) or
                  not _near(axes["y"],reference["y"],AXIS_TOL) or
                  not _near(axes["normal"],reference["normal"],AXIS_TOL)):
                raise ValueError("in-plane source image row/column axis changed within scan group")
            if first_axes is None:
                first_axes=axes
            elif (not _near(axes["x"],first_axes["x"],AXIS_TOL) or
                  not _near(axes["y"],first_axes["y"],AXIS_TOL)):
                raise ValueError("unregistered image axis mismatch across scan groups")
            source_count+=1
        group_summaries.append({
            "group_number":group_i,
            "source_slice_count":len(group["slices"]),
            "pixel_column_increasing_RAS_unit":reference["x"],
            "pixel_row_increasing_RAS_unit":reference["y"],
            "header_normal_RAS_unit":reference["normal"],
            "no_in_plane_axis_rotation_or_flip_found":True,
        })
    return {
        "schema_version":1,
        "kind":"NLM_72_ORIGINAL_CT_HEADER_ORIENTATION_PREFLIGHT",
        "status":"SOURCE_HEADER_AFFINE_AXES_VERIFIED_NOT_ANATOMICAL",
        "scanner_header_original_SHA256_matches_manifest_for_all_slices":True,
        "source_header_count_verified":source_count,
        "existing_series_bundle_contiguous":before["status"]=="CONTIGUOUS_MULTI_GROUP_SOURCE_VOLUME_NOT_ANATOMICAL",
        "source_groups":group_summaries,
        "cross_group_image_axes_aligned":True,
        "source_header_patient_identifiers_returned":False,
        "image_pixels_downloaded_or_committed":False,
        "index_zero_pixel_centre_vs_outer_edge_convention_verified":False,
        "original_PNG_stored_scalars_calibrated_as_HU":False,
        "candidate_bone_regions_independently_labelled":False,
        "independent_clinical_bone_surfaces_verified":False,
        "scanner_patient_RAS_to_HGPT_world_verified":False,
        "skeleton_or_mesh_modified":False,
        "canonical_promotion_allowed":False,
    }


def _fetch_one(source_id):
    if not isinstance(source_id,str) or SOURCE_RE.fullmatch(source_id) is None:
        raise ValueError("unsafe NLM CT source header name")
    raw = scout._safe_download(scan.ROOT+source_id+".txt",scan.MAX_TEXT_BYTES)
    # Scanner metadata may contain historical identifiers: never log,
    # commit or return raw text or messages from its contents.
    return source_id, {
        "source_header_sha256":hashlib.sha256(raw).hexdigest(),
        "safe_scanner_geometry":scan.scanner_geometry_from_text(raw),
    }


def fetch_safe_original_headers(bundle, workers=6):
    expected=[row["source_id"] for group in bundle["series"]
              for row in group["slices"]]
    if len(expected)!=72 or len(set(expected))!=72:
        raise ValueError("source manifest must be the original exact 72-slice bundle")
    if workers not in (1,2,4,6):
        raise ValueError("bounded original-source worker count required")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        records=list(pool.map(_fetch_one,expected))
    return dict(records)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-bundle",type=Path,required=True)
    parser.add_argument("--live-original-headers",action="store_true")
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    if not args.live_original_headers:
        parser.error("explicit --live-original-headers required for NLM request")
    source=json.loads(args.source_bundle.read_text(encoding="utf-8"))
    # Fail on forged/partial bundle before issuing any source requests.
    series.validate_series_bundle(source)
    report=verify_72_original_headers(source,fetch_safe_original_headers(source))
    payload=json.dumps(report,indent=2)+"\n"
    if args.out:
        with args.out.open("x",encoding="utf-8") as f:
            f.write(payload)
    else:
        print(payload,end="")


if __name__=="__main__":
    main()
