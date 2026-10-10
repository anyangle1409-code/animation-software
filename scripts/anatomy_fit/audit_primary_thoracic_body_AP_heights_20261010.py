#!/usr/bin/env python3
"""Audit recovered ORIGINAL 2011 Table 2 vertebral AP heights and source context.

Previously the canonical THORACIC_BODY_DISC_2011 record included only A/P
averages, although the actual original paper has both A and P means and SDs.
These raw individual-level mixed-sex study summaries do NOT determine angles,
whole-spine pose, physical endplate axes, disc clearance or 182cm male targets.

No images, clinical datasets, meshes, Blender or accepted bones are changed.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"ORIGINAL_V1_WORK/anatomy/thoracic_2011_original_VBHA_VBHP_table2_20261010.json"
CANONICAL=ROOT/"ORIGINAL_V1_WORK/anatomy/canonical_proportion_sources_v1.json"
# Distinct exact ORIGINAL Table 2 source values, not accepted model target.
# (Anterior mean, anterior SD, posterior mean, posterior SD, printed A/P average)
PRINTED_TABLE=(
    ("C7",13.89,1.42,14.38,2.22,14.14),
    ("T1",14.49,1.23,15.28,1.14,14.88),
    ("T2",15.01,1.51,16.11,1.67,15.56),
    ("T3",15.65,1.85,17.41,1.12,16.53),
    ("T4",15.42,1.46,18.15,1.54,16.79),
    ("T5",15.84,1.07,17.33,2.16,16.59),
    ("T6",16.04,1.43,18.22,1.38,17.13),
    ("T7",15.94,1.61,18.67,1.64,17.31),
    ("T8",16.99,1.70,20.05,1.77,18.52),
    ("T9",18.26,2.12,20.25,2.44,19.26),
    ("T10",18.98,1.40,20.35,1.89,19.67),
    ("T11",19.60,1.92,22.67,1.38,21.14),
    ("T12",20.80,1.96,23.12,1.94,21.96),
)
ALL_DENIALS=(
    "standing_segmental_wedge_angles_accepted",
    "thoracic_AP_depths_from_same_cohort_obtained",
    "vertebral_body_3d_endplate_planes_verified",
    "fully_coupled_sternum_rib_spine_chain_validated",
    "canonical_182cm_spine_targets_selected",
    "c005_blender_master_freeze_approved",
    "regional_readiness_promoted",
    "cp1_gate6_passed",
)
ALL_CAVEATS=(
    "not_a_vertebral_body_angle_measurement",
    "original_AP_vertebral_depth_at_each_level_unavailable",
    "endplate_surface_normals_not_identified",
    "no_patient_matched_whole_spine_global_curve",
    "no_healthy_standing_male_182_cm_target",
    "cannot_derive_segmental_angles_from_height_difference_alone",
    "cannot_multiply_mixed_cohort_height_differences_by_independent_CT_AP_widths",
    "cannot_sum_all_segment_height_wedges_to_43_7_degrees_without_measured_angles",
    "posterior_greater_than_anterior_height_is_only_wedging_direction_context",
    "discs_in_source_studied_separately_no_cross_cohort_arithmetic",
    "source_recovery_closes_missing_primary_VBHA_VBHP_table_only",
)

def audit(paper:dict,canonical:dict)->dict:
    if paper.get("kind")!="HGPT_INDEPENDENT_NONCANONICAL_DIRECT_PRIMARY_THORACIC_BODY_AP_HEIGHT_TABLE":
        raise ValueError("Source review type changed")
    s=paper.get("source",{})
    if (s.get("pmcid")!="PMC3171774" or s.get("pmid")!="21615399" or
        s.get("doi")!="10.1111/j.1469-7580.2011.01397.x" or
        s.get("direct_table_observed") is not True or
        s.get("raw_pdf_bytes_downloaded") is not False or
        (s.get("study_total_vertebral_segments"),
         s.get("study_total_distinct_donors"),s.get("study_donor_male_n"),
         s.get("study_donor_female_n"),s.get("segments_per_disc_level"))!=(72,30,15,15,6) or
        s.get("source_is_standing_sagittal_curve") is not False or
        s.get("source_is_radiographic_ex_vivo_segmentation") is not True or
        s.get("eligible_male_182_cm_conditional_cohort") is not False or
        s.get("original_figures_copied") is not False or
        s.get("patient_images_or_3d_mesh_imported") is not False):
        raise ValueError("Original paper identity, cohort or methods cannot be promoted")
    flags=paper.get("explicit_acceptance",{})
    for flag in ALL_DENIALS:
        if flags.get(flag) is not False:
            raise ValueError("Original mixed-sex isolated bodies are not canonically approved: "+flag)
    for field in ("source_table_2_vbha_vbhp_levelled_obtained",
                  "body_height_mean_pattern_provisionally_usable_for_cross_source_check"):
        if flags.get(field) is not True:
            raise ValueError("Unverified primary source entry")
    caveats=paper.get("measurement_caveats",{})
    if any(caveats.get(key) is not True for key in ALL_CAVEATS):
        raise ValueError("Source wedge heights were falsely treated as joint angles/endplates")
    current=paper.get("body_table_2",{})
    expected_levels={row[0] for row in PRINTED_TABLE}
    if set(current)!=expected_levels:
        raise ValueError("Must verify every C7-T12 level and no extra one")
    candidates=[x for x in canonical.get("sources",[])
                if x.get("id")=="THORACIC_BODY_DISC_2011"]
    if len(candidates)!=1 or candidates[0].get("pmcid")!="PMC3171774":
        raise ValueError("Historical canonical 2011 source identity absent or duplicated")
    frozen=candidates[0]
    canonical_averages=frozen.get("body_average_height_mm",{})
    if set(canonical_averages)!=expected_levels:
        raise ValueError("Frozen source contains incomplete or surplus thoracic average levels")
    if canonical_averages!=frozen.get("average_body_height_mm"):
        raise ValueError("Original canonical aliases to study average disagree")

    measurements={}
    diffs=[]
    for level,anterior,asd,posterior,psd,average in PRINTED_TABLE:
        row=current[level]
        if (row!={"anterior_mean_mm":anterior,"anterior_sd_mm":asd,
                  "posterior_mean_mm":posterior,"posterior_sd_mm":psd,
                  "reported_AP_average_mm":average} or
                canonical_averages[level]!=average):
            raise ValueError("Original source Table 2 or frozen level average changed: "+level)
        if not all(math.isfinite(x) and x>0
                   for x in (anterior,asd,posterior,psd,average)):
            raise ValueError("Nonphysical Table 2 input")
        if abs((anterior+posterior)/2-average)>0.011:
            raise ValueError("Printed average incompatible with source anterior/posterior")
        difference=round(posterior-anterior,2)
        if difference<=0:
            raise ValueError("Unexpected original posterior-vs-anterior wedge sign")
        measurements[level]={
            "anterior_mean_mm":anterior,
            "posterior_mean_mm":posterior,
            "posterior_minus_anterior_mean_mm":difference,
            "anterior_over_posterior_height_ratio":round(anterior/posterior,5),
            "two_input_sd_values_not_independent_segment_angle_SD":[asd,psd],
            "angle_or_AP_depth_inferred":False,
        }
        diffs.append(difference)
    ct_sources=[x for x in canonical.get("sources",[])
                if x.get("id")=="THORACIC_CT_2016_INDIA"]
    if len(ct_sources)!=1:
        raise ValueError("Independent CT source missing")
    ct=ct_sources[0].get("body_height_anterior_posterior_mm",{})
    if sorted(ct)!=sorted(expected_levels-{"C7"}):
        raise ValueError("Independent CT level IDs changed")
    cross=[]
    for level in ("T1","T4","T7","T10","T12"):
        ap=ct[level]
        if not (isinstance(ap,list) and len(ap)==2 and
                all(type(v) in (int,float) and math.isfinite(v) and v>0
                    for v in ap)):
            raise ValueError("Independent CT AP height data unexpected")
        if ap[1]<=ap[0]:
            raise ValueError("Independent source does not support expected sign: "+level)
        cross.append({
            "level":level,
            "kunkel_2011_posterior_gt_anterior":True,
            "separate_indian_CT_2016_posterior_gt_anterior":True,
            "sources_can_supply_vertebral_depths_for_one_another":False,
            "cohort_differences_unresolved":True
        })
    return {
        "schema_version":1,
        "kind":"HGPT_NONCANONICAL_RESTORED_THORACIC_WEDGE_HEIGHT_CONTEXT",
        "original_2011_source_url":s["primary_full_html"],
        "original_donor_count":30,
        "original_72_segments_across_12_disc_levels":True,
        "body_levels_examined_count":len(PRINTED_TABLE),
        "thoracic_body_levels_examined_count":12,
        "all_13_levels_posterior_taller_than_anterior_means":True,
        "min_posterior_minus_anterior_mm":min(diffs),
        "max_posterior_minus_anterior_mm":max(diffs),
        "reused_existing_source_average_body_heights_without_changes":True,
        "cross_source_2016_CT_spotcheck":cross,
        "original_levelled_source_heights":measurements,
        "per_level_standing_spinal_cobb_angles_reported":False,
        "patient_matched_3d_endplate_depths_reported":False,
        "mean_A_P_heights_can_be_read_as_182cm_male_target":False,
        "freeze_C2_to_S1_stack_ready":False,
        "CP1_gate6_passed":False
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,default=SOURCE)
    p.add_argument("--canonical",type=Path,default=CANONICAL)
    args=p.parse_args()
    a=json.loads(args.source.read_text(encoding="utf-8"))
    b=json.loads(args.canonical.read_text(encoding="utf-8"))
    print(json.dumps(audit(a,b),indent=2,sort_keys=True))

if __name__=="__main__":
    main()
