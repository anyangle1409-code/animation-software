#!/usr/bin/env python3
"""Original NLM adjacent CT triplet integrity / physical spacing inspection.

Limited to SIX externally verified original normalCT source filenames across
two three-slice windows. Never assumes file number is scanner coordinate.
Never labels a bone or produces a 3D mesh. Does not save raw pixels or
historical scanner headers; outputs anonymized source SHA, physical scanner
geometry and stored-value statistics only.

The original 3mm thick slices are NOT equivalent to validated sub-millimetre
bony feature surfaces. A three-slice window is for candidate anatomical
inspection and staging; the actual feature needs local full-res review.
"""
import argparse
import hashlib
import json
from pathlib import Path

import nlm_pelvis_region_scout as scout
import nlm_ct_scanner_geometry_header as hdr
import nlm_original_ct_png_probe as png

TRIPLETS=((1749,1752,1755),(1797,1800,1803))


def validate_windows(windows):
    if (not isinstance(windows,list) or len(windows)!=2 or
            tuple(tuple(row["source_id"] for row in group) for group in windows)!=TRIPLETS):
        raise ValueError("exact two reviewed original NLM triplets required")
    stats=[]
    for group in windows:
        for r in group:
            if (r.get("source_bytes_verified") is not True or
                    r.get("candidate_anatomical_label_approved") is not False):
                raise ValueError("source identity or anatomy evidence status invalid")
            if (r.get("scanner_grid")!=[512,512] or
                    r.get("pixel_spacing_mm")!=[.898438,.898438] or
                    abs(r.get("slice_thickness_mm",0)-3)>1e-6):
                raise ValueError("scanner grid or physical slice thickness inconsistent")
        steps=[group[i]["physical_scanner_S_mm"]-group[i+1]["physical_scanner_S_mm"]
               for i in (0,1)]
        if any(abs(s-3)>1e-5 for s in steps):
            raise ValueError("original CT window not contiguous at measured 3mm scanner intervals")
        stats.append({
            "source_ids":[row["source_id"] for row in group],
            "physical_scanner_Z_mm":[row["physical_scanner_S_mm"] for row in group],
            "measured_step_between_centres_mm":steps,
            "scan_window_extents_including_half_slice_mm":[
                group[-1]["physical_scanner_S_mm"]-1.5,
                group[0]["physical_scanner_S_mm"]+1.5],
            "continuous_original_CT_source_bytes_verified":True,
            "same_physical_scanner_group_verified":True,
            "any_bony_feature_independently_labelled":False,
            "submillimetre_anatomical_accuracy_approved":False
        })
    return stats


def inspect_triplet(triplet, loader):
    rows=[]
    originals=[]
    for n in triplet:
        filename=f"cvm{n}f.png"
        header=f"cvm{n}f.txt"
        image=loader(scout.INDEX_BASE+filename,png.MAX_BYTES)
        raw_header=loader(hdr.ROOT+header,hdr.MAX_TEXT_BYTES)
        info=png.inspect_png(image)
        safe=hdr.scanner_geometry_from_text(raw_header)
        decoded=scout.decode_grayscale_png16(image)
        originals.append(safe)
        rows.append({
            "source_id":n,
            "source_png_sha256":info["source_sha256"],
            "source_header_sha256":hashlib.sha256(raw_header).hexdigest(),
            "source_bytes_verified":True,
            "source_PNG_byte_count":len(image),
            "physical_scanner_S_mm":safe["image_location_superior_mm"],
            "scanner_grid":safe["image_dimensions"],
            "pixel_spacing_mm":safe["pixel_spacing_mm"],
            "slice_thickness_mm":safe["slice_thickness_mm"],
            "nominal_slice_spacing_mm":safe["nominal_series_slice_spacing_mm"],
            "raw_source_scalar_statistics":scout.raw_statistics(decoded),
            "candidate_anatomical_label_approved":False,
        })
    for a,b in zip(originals,originals[1:]):
        hdr.pair_consistency(a,b)
    return rows


def scout_windows(loader):
    rows=[inspect_triplet(t,loader) for t in TRIPLETS]
    checks=validate_windows(rows)
    return {
        "schema_version":1,
        "kind":"INDEPENDENT_NLM_ADJACENT_SOURCE_WINDOW_AUDIT",
        "status":"ORIGINAL_SCANNER_3MM_TRIPLETS_VERIFIED_NOT_ANATOMICAL",
        "source_custodian":"US National Library of Medicine",
        "number_of_source_windows":len(rows),
        "number_of_original_CT_images":sum(len(r) for r in rows),
        "source_images_or_patient_headers_committed":False,
        "source_HU_calibration_verified":False,
        "source_3D_bone_segmentations_validated":False,
        "anatomical_reference_landmarks_verified":False,
        "canonical_promotion_allowed":False,
        "source_image_rows":rows,
        "physical_contiguous_window_evidence":checks
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    if not a.live:
        p.error("explicit --live required for fetching original NLM CT source")
    report=scout_windows(scout._safe_download)
    result=json.dumps(report,indent=2)+"\n"
    if a.out:
        with a.out.open("x",encoding="utf-8") as f:
            f.write(result)
    else:
        print(result)

if __name__=="__main__":
    main()
