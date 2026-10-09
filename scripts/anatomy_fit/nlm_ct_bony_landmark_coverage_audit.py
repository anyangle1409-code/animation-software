#!/usr/bin/env python3
"""Independent source-evidence audit for seven REQUIRED real bony landmarks.

The 72 original NLM CT source frames have verified GE scanner image axes:
increasing PNG column -> scanner -R; increasing PNG row -> scanner -A.
The existing ten Work observations are *candidate broad bone regions*, NOT
individual osseous ASIS/pubis/S1/femoral articular landmark coordinates.

This module cross-checks source hashes, source 3D positions, left/right
consistency, physical sample bounds and actual reviewer coverage. It does
NOT promote broad-region/one-slice observations to real landmark evidence.
All pixel positions are a clearly labelled candidate under an unresolved
GE image-corner-to-pixel-sample convention. No medical pixels are exported.
"""
import argparse
import collections
import json
from pathlib import Path

import nlm_ct_anatomical_review as review
import pelvic_ct_series_manifest as series

REQUIRED_BONY_FEATURES={
    "asis_left": ("iliac_blade", "left", "not_an_identified_bony_ASIS"),
    "asis_right": ("iliac_blade", "right", "not_an_identified_bony_ASIS"),
    "pubic_tubercle_left": ("pubic_region", "left", "not_a_bony_pubic_tubercle"),
    "pubic_tubercle_right": ("pubic_region", "right", "not_a_bony_pubic_tubercle"),
    "s1_superior_endplate_centre": ("sacrum", "midline", "not_a_traced_S1_superior_endplate"),
    "femoral_head_centre_left": ("femoral_head_left", "left", "not_a_fitted_articular_sphere_centre"),
    "femoral_head_centre_right": ("femoral_head_right", "right", "not_a_fitted_articular_sphere_centre"),
}
VERIFIED_AXIS_CONVENTION={
    "scanner_positive_R_is_patient_right": True,
    "source_image_column_direction_RAS": [-1,0,0],
    "source_image_row_direction_RAS": [0,-1,0],
    "source_plane_normal_RAS": [0,0,1],
    "GE_top_left_corner_is_outer_FOV_edge_verified": False,
}

def _source_rows(bundle):
    validation=series.validate_series_bundle(bundle)
    if validation["slice_count"]!=72 or len(bundle["series"])!=2:
        raise ValueError("requires pinned 72-source two-group CT series")
    rows={}
    for index,group in enumerate(bundle["series"],1):
        for r in group["slices"]:
            rows[r["source_id"]]=dict(r,source_acquisition_group=index)
    return rows

def _side(obs):
    label=obs["candidate_label"]
    key=obs["observation_id"].lower()
    label_side=("left" if label.endswith("_left") else
                "right" if label.endswith("_right") else None)
    id_left="-left-" in key
    id_right="-right-" in key
    if id_left and id_right:
        raise ValueError("candidate laterality conflicts within source observation identifier")
    id_side="left" if id_left else "right" if id_right else None
    if label_side and id_side and label_side!=id_side:
        raise ValueError("candidate label laterality conflicts with original source observation identifier")
    return label_side or id_side or (
        "midline" if label in ("sacrum","pubic_region") else "unlabelled")

def _candidate_ras(obs,source):
    """Diagnostic physical coordinate, conditional on OUTER FOV corners."""
    centre=source["scanner_centre_RAS_mm"]
    grid=source["scanner_grid"]
    spacing=source["pixel_spacing_mm"]
    row,col=obs["pixel"]["row"],obs["pixel"]["column"]
    if grid!=[512,512] or spacing!=[0.898438,0.898438] or source["slice_normal_RAS"]!=[0,0,1]:
        raise ValueError("unexpected GE scanner source world grid or orientation")
    if not isinstance(row,int) or type(row)is bool or not isinstance(col,int) or type(col)is bool:
        raise ValueError("invalid original CT integer pixel indices")
    r=centre[0]+(grid[0]/2-col-.5)*spacing[0]
    a=centre[1]+(grid[1]/2-row-.5)*spacing[1]
    s=centre[2]
    return {
        "candidate_scanner_RAS_mm_if_outer_FOV_origin":[round(r,6),round(a,6),s],
        "in_plane_half_pixel_mm":[spacing[0]/2,spacing[1]/2],
        "axial_half_slice_thickness_mm":source["slice_thickness_mm"]/2,
        "original_GE_outer_edge_vs_pixel_centre_origin_verified":False,
        "physical_bony_feature_identity_verified":False,
    }

def audit(bundle,observations):
    rows=_source_rows(bundle)
    validated=review.validate_review_packet(observations,bundle)
    if len(validated["observations"])!=10 or validated["anatomical_status"]!="CANDIDATE":
        raise ValueError("expected ten unapproved original CT source observations")
    out=[]
    by_key=collections.defaultdict(list)
    reviewer_ids=set()
    for obs in validated["observations"]:
        src=rows[obs["source_id"]]
        side=_side(obs)
        position=_candidate_ras(obs,src)
        x=position["candidate_scanner_RAS_mm_if_outer_FOV_origin"][0]
        # Do NOT silently mirror an anatomically named candidate.
        # This checks ONLY the metadata orientation and its review label.
        if (side=="right" and x<=0) or (side=="left" and x>=0):
            raise ValueError("candidate laterality conflicts with independently verified GE RAS image direction")
        reviewer_ids.add(obs["reviewer_id"])
        record={
            "source_observation_id":obs["observation_id"],
            "candidate_label":obs["candidate_label"],
            "candidate_side_from_existing_review":side,
            "source_id":obs["source_id"],
            "source_png_sha256":obs["source_png_sha256"],
            "source_header_sha256":obs["source_header_sha256"],
            "source_ge_scanner_group":src["source_acquisition_group"],
            "scanner_S_mm":src["scanner_centre_RAS_mm"][2],
            **position,
            "observation_confidence_is_not_landmark_accuracy":obs["confidence"],
            "same_source_observation_independent_second_anatomical_reviewer":False,
        }
        by_key[(obs["candidate_label"],side)].append(record)
        out.append(record)

    inventory=[]
    for name,(label,side,limit) in REQUIRED_BONY_FEATURES.items():
        matching=by_key[(label,side)]
        different_levels=sorted({x["scanner_S_mm"] for x in matching},reverse=True)
        inventory.append({
            "required_physical_osseous_landmark":name,
            "current_supporting_region_label":label,
            "region_review_observations":len(matching),
            "unique_physical_scanner_levels":different_levels,
            "source_region_observations_still_only_candidates":True,
            "reason_region_cannot_certify_landmark":limit,
            "requires_independently_segmented_or_traced_true_bone_feature":True,
            "requires_independent_second_source_anatomy_review":True,
            "specific_bony_landmark_verified":False,
            "candidate_supported_by_3_adjacent_source_slices":False,
        })
    all_source_z=[r["scanner_centre_RAS_mm"][2] for r in rows.values()]
    all_groups=[]
    for i,group in enumerate(bundle["series"],1):
        zz=[x["scanner_centre_RAS_mm"][2] for x in group["slices"]]
        thickness=group["slices"][0]["slice_thickness_mm"]
        all_groups.append({
            "source_group":i,
            "slice_count":len(zz),
            "source_S_centres_mm":[max(zz),min(zz)],
            "source_S_covered_slab_mm":[min(zz)-thickness/2,max(zz)+thickness/2],
            "full_bony_pelvis_coverage_proven":False,
        })
    return {
        "schema_version":1,
        "kind":"NLM_CANDIDATE_72_IMAGE_REQUIRED_BONY_LANDMARK_COVERAGE_AUDIT",
        "status":"ALL_SEVEN_REQUIRED_TRUE_OSSEOUS_FEATURES_UNVERIFIED",
        "source_rows_verified":len(rows),
        "original_candidate_review_count":len(out),
        "independent_anatomical_reviewers_count":0,
        "source_reviewers_in_existing_packet":sorted(reviewer_ids),
        "scanner_RAS_axis_evidence":VERIFIED_AXIS_CONVENTION,
        "conditional_pixel_sample_coordinates_are_not_clinical_measurements":True,
        "source_scan_groups":all_groups,
        "candidate_observations":out,
        "required_osseous_landmark_coverage":inventory,
        "number_of_true_bony_landmarks_independently_verified":0,
        "full_anatomical_pelvis_coverage_verified":False,
        "bony_source_meshes_independently_verified":False,
        "CT_PNG_to_HU_conversion_verified":False,
        "patient_scanner_to_HGPT_world_transform_verified":False,
        "skeleton_or_mesh_modified":False,
        "canonical_promotion_allowed":False,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-bundle",type=Path,required=True)
    p.add_argument("--candidate-review",type=Path,required=True)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    bundle=json.loads(args.source_bundle.read_text())
    observations=json.loads(args.candidate_review.read_text())
    data=audit(bundle,observations)
    result=json.dumps(data,indent=2)+"\n"
    if args.out:
        with args.out.open("x",encoding="utf-8") as f:
            f.write(result)
    else:
        print(result,end="")
if __name__=="__main__":
    main()
