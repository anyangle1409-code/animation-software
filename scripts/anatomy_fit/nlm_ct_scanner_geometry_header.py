#!/usr/bin/env python3
"""Privacy-filtered original NLM Visible Human CT scanner geometry reader.

Use a STRICT allowlist of radiological image geometry fields. Never copy
patient or operator fields from the historical GE text headers to reports,
commits, exceptions or logs. This script only emits image geometry and a
source-file SHA; it does not import 3D bones or verify bone segmentation.

Scanner coordinates R/A/S are NOT the HomeGymPT skeleton world frame, and
corner coordinates may refer to pixel edges rather than sample centres.
Do not infer a physical pixel-to-patient affine matrix until the original
scanner convention, pixel index origin and header coherence are validated.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path
import urllib.request

ROOT="https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Male-Images/PNG_format/radiological/normalCTHeaders/"
ALLOWED=("cvm1013f.txt","cvm1014f.txt")
MAX_TEXT_BYTES=64*1024

KEYS={
    "Image matrix size - X":"width_pixels",
    "Image matrix size - Y":"height_pixels",
    "Image pixel size - X":"pixel_spacing_x_mm",
    "Image pixel size - Y":"pixel_spacing_y_mm",
    "Slice Thickness (mm)":"slice_thickness_mm",
    "Spacing Between scans(mm)":"series_nominal_slice_spacing_mm",
    "Image location":"image_location_mm",
    "Center R coord of plane image":"scanner_R_centre_mm",
    "Center A coord of plane image":"scanner_A_centre_mm",
    "Center S coord of Plane image":"scanner_S_centre_mm",
    "R Coord of Top Left Hand Corner":"R_TL_mm",
    "A Coord of Top Left Hand Corner":"A_TL_mm",
    "S Coord of Top Left Hand Corner":"S_TL_mm",
    "R Coord of Top Right Hand Corner":"R_TR_mm",
    "A Coord of Top Right Hand Corner":"A_TR_mm",
    "S Coord of Top Right Hand Corner":"S_TR_mm",
    "R Coord of Bottom Right Hand Corner":"R_BR_mm",
    "A Coord of Bottom Right Hand Corner":"A_BR_mm",
    "S Coord of Bottom Right Hand Corner":"S_BR_mm",
    "Normal R coord":"normal_R",
    "Normal A coord":"normal_A",
    "Normal S coord":"normal_S",
}
INTEGER_FIELDS={"width_pixels","height_pixels"}


def scanner_geometry_from_text(raw):
    if not isinstance(raw,(str,bytes)):
        raise ValueError("invalid header text")
    blob=raw.encode("utf-8") if isinstance(raw,str) else raw
    if len(blob)>MAX_TEXT_BYTES:
        raise ValueError("scanner text header too large")
    t=blob.decode("utf-8","replace")
    vals={}
    # Explicitly match keys ONLY from the curated numerical geometry list.
    # Everything else (e.g. patient names, IDs, institution, DOB) is skipped.
    for line in t.splitlines():
        if ":" not in line:
            continue
        head,rest=line.split(":",1)
        k=re.sub(r"\.{2,}","",head).strip()
        if k not in KEYS:
            continue
        alias=KEYS[k]
        if alias in vals:
            raise ValueError("duplicate registered scanner geometry field")
        number=re.match(r"^\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)",rest)
        if not number:
            raise ValueError("invalid registered scanner geometry scalar")
        v=float(number.group(1))
        if not math.isfinite(v):
            raise ValueError("nonfinite registered scanner geometry scalar")
        if alias in INTEGER_FIELDS:
            if v!=int(v):
                raise ValueError("noninteger scanner pixel dimensions")
            v=int(v)
        vals[alias]=v
    if set(vals)!=set(KEYS.values()):
        raise ValueError("required scanner geometry fields absent")
    if vals["width_pixels"]!=512 or vals["height_pixels"]!=512:
        raise ValueError("nonoriginal CT scanner image dimensions")
    if not 0<vals["pixel_spacing_x_mm"]<2 or not 0<vals["pixel_spacing_y_mm"]<2:
        raise ValueError("invalid pixel spacing in mm")
    if not 0<vals["slice_thickness_mm"]<10 or not 0<vals["series_nominal_slice_spacing_mm"]<10:
        raise ValueError("invalid axial scanner slice thickness/spacing")
    p=lambda prefix:[vals[f"R_{prefix}_mm"],vals[f"A_{prefix}_mm"],vals[f"S_{prefix}_mm"]]
    tl,tr,br=p("TL"),p("TR"),p("BR")
    dx=[tr[i]-tl[i] for i in range(3)]
    dy=[br[i]-tr[i] for i in range(3)]
    lenx=math.sqrt(sum(x*x for x in dx))
    leny=math.sqrt(sum(x*x for x in dy))
    scalar=vals["width_pixels"]*vals["pixel_spacing_x_mm"]
    scalar_y=vals["height_pixels"]*vals["pixel_spacing_y_mm"]
    if abs(lenx-scalar)>.01 or abs(leny-scalar_y)>.01:
        raise ValueError("reported CT scanner corners are inconsistent with pixel spacing")
    if abs(sum(x*y for x,y in zip(dx,dy))) > .001*lenx*leny:
        raise ValueError("reported CT scanner axes are not orthogonal")
    normal=[vals[f"normal_{axis}"] for axis in ("R","A","S")]
    if not .99<math.sqrt(sum(x*x for x in normal))<1.01:
        raise ValueError("reported scanner normal has wrong magnitude")
    if abs(vals["image_location_mm"]-vals["scanner_S_centre_mm"])>.01:
        raise ValueError("image-location and scanner superior coordinate differ")
    if abs(tl[2]-vals["scanner_S_centre_mm"])>.01:
        raise ValueError("nonaxial CT slice requires separate image transform")
    return {
        "kind":"ORIGINAL_NLM_CT_GEOMETRY_SAFE_FIELDS_ONLY",
        "scanner_frame":"GE_RAS_MM_NOT_HOMEGYMPT_WORLD",
        "image_dimensions":[vals["width_pixels"],vals["height_pixels"]],
        "pixel_spacing_mm":[vals["pixel_spacing_x_mm"],vals["pixel_spacing_y_mm"]],
        "slice_thickness_mm":vals["slice_thickness_mm"],
        "nominal_series_slice_spacing_mm":vals["series_nominal_slice_spacing_mm"],
        "image_location_superior_mm":vals["image_location_mm"],
        "reported_plane_centre_RAS_mm":[vals["scanner_R_centre_mm"],
                                        vals["scanner_A_centre_mm"],
                                        vals["scanner_S_centre_mm"]],
        "plane_TL_RAS_mm":tl,
        "plane_TR_RAS_mm":tr,
        "plane_BR_RAS_mm":br,
        "normal_RAS":normal,
        "scanner_corner_range_x_mm":lenx,
        "scanner_corner_range_y_mm":leny,
        "pixel_to_real_world_centre_offset_verified":False,
        "image_is_anatomically_a_pelvis_slice":False,
        "patient_identifiers_excluded_by_allowlist":True,
        "patient_to_HGPT_frame_registered":False,
        "HU_conversion_from_png_verified":False,
        "bony_landmarks_selected":False,
        "canonical_promotion_allowed":False,
    }


def pair_consistency(one,two):
    if one["image_dimensions"]!=two["image_dimensions"] or one["pixel_spacing_mm"]!=two["pixel_spacing_mm"]:
        raise ValueError("different geometric pixel grids in adjacent CT frames")
    separation=abs(one["image_location_superior_mm"]-two["image_location_superior_mm"])
    expected=one["nominal_series_slice_spacing_mm"]
    if abs(separation-expected)>.01:
        raise ValueError("two selected CT scans not nominally adjacent in scanner coordinates")
    for k in ("plane_TL_RAS_mm","plane_TR_RAS_mm","plane_BR_RAS_mm"):
        if any(abs(one[k][i]-two[k][i])>.01 for i in (0,1)):
            raise ValueError("transverse scanner corner grid changes between adjacent slices")
    return {"kind":"ADJACENT_CT_GEOMETRY_COMPARISON",
            "slice_spacing_measured_mm":separation,
            "measured_and_reported_spacing_agree":True,
            "scanner_to_HGPT_world_registration_verified":False,
            "canonical_promotion_allowed":False}


def fetch_header(name):
    if name not in ALLOWED:
        raise ValueError("not an allowlisted NLM scan geometry header")
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*a,**k):
            raise ValueError("NLM source changed location")
    opener=urllib.request.build_opener(NoRedirect())
    request=urllib.request.Request(ROOT+name,headers={"User-Agent":"HomeGymPT-CT-Geometry-Header/1.0"})
    with opener.open(request,timeout=20) as response:
        raw=response.read(MAX_TEXT_BYTES+1)
    geometry=scanner_geometry_from_text(raw)
    geometry["source_filename"]=name
    geometry["raw_source_sha256"]=hashlib.sha256(raw).hexdigest()
    geometry["original_header_only_temporary_memory"]=True
    return geometry


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--header",type=Path)
    p.add_argument("--fetch",choices=ALLOWED)
    p.add_argument("--check-adjacent-pair",action="store_true")
    args=p.parse_args()
    if sum(bool(v) for v in (args.header,args.fetch,args.check_adjacent_pair))!=1:
        p.error("choose exactly one of --header, --fetch or --check-adjacent-pair")
    if args.check_adjacent_pair:
        first=fetch_header(ALLOWED[0])
        second=fetch_header(ALLOWED[1])
        result={"source_headers":[first,second],
                "adjacent_scan_geometry":pair_consistency(first,second),
                "canonical_promotion_allowed":False,
                "source_header_patient_identifiers_never_exported":True}
    elif args.fetch:
        result=fetch_header(args.fetch)
    else:
        raw=args.header.read_bytes()
        result=scanner_geometry_from_text(raw)
        result["raw_source_sha256"]=hashlib.sha256(raw).hexdigest()
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
