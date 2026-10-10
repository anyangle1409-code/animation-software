#!/usr/bin/env python3
"""Noncanonical primary-source sternum table QA and endpoint difference audit.

No clinical image/PDF copying, no mesh edits or accepted absolute target.
Primary 2006 sample results must not be conflated with separate CT cohorts,
with the 182cm project donor, or with a Blender stick.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/"ORIGINAL_V1_WORK/anatomy/sternum_selthofer_2006_primary_table_recheck_20261010.json"
PREVIOUS = ROOT/"ORIGINAL_V1_WORK/anatomy/canonical_sternum_target_review_v1.json"
EXPECTED_TABLE = {
    "manubrium_length_cm": (5.52,0.36),
    "manubrium_max_breadth_cm": (6.82,0.80),
    "manubrium_min_breadth_cm": (3.68,0.55),
    "manubrium_avg_breadth_cm": (5.25,0.68),
    "manubrium_avg_thickness_cm": (1.26,0.19),
    "body_length_cm": (10.97,1.44),
    "body_avg_breadth_cm": (3.07,0.43),
    "body_avg_thickness_cm": (1.00,0.11),
    "total_sternum_length_cm": (20.86,1.46),
    "sternal_angle_deg": (166.35,7.38),
}
REQUIRED_DENIALS = (
    "sternum_abs_length_contradiction_resolved",
    "notch_by_notch_vertical_coordinate_target_closed",
    "sternum_frame_kinematic_joint_centres_closed",
    "joint_centres_selected",
    "canonical_geometry_mutated",
    "canonical_promotion_allowed",
    "cp1_gate6_passed",
    "regional_readiness_upgraded",
)


def audit(paper:dict, prior:dict) -> dict:
    if paper.get("kind") != "HGPT_NONCANONICAL_PRIMARY_STERNUM_ENDPOINT_RECHECK":
        raise ValueError("Unrecognized source record")
    src = paper.get("source",{})
    sample=src.get("donor_specimens",{})
    if (src.get("pubmed") != "16617574" or src.get("year") != 2006 or
            src.get("primary_fulltext_url") != "https://hrcak.srce.hr/file/11308" or
            src.get("public_fulltext_pages") != 5 or
            sample.get("male") != 55 or sample.get("female") != 35 or
            sample.get("mean_age_years") != 65):
        raise ValueError("Primary source identity or study sample changed")
    if src.get("pdf_bytes_locally_downloaded_and_hash_verified") is not False:
        raise ValueError("No downloaded/hash-pinned PDF may be claimed")
    table=paper.get("male_table_primary",{})
    for name,(mean,sd) in EXPECTED_TABLE.items():
        cell=table.get(name,{})
        if (type(cell.get("mean")) not in (int,float) or
                type(cell.get("sd")) not in (int,float) or
                abs(cell["mean"]-mean)>1e-8 or abs(cell["sd"]-sd)>1e-8):
            raise ValueError("Source table numeric mismatch: "+name)
    if (table.get("total_length_endpoint") !=
            "centre of jugular notch to end of xiphoid process" or
            table.get("notch_distances_full_level_table_available") is not False):
        raise ValueError("Invalid source length endpoints or notch data claim")
    if (paper.get("explicit_decision",{}).get("source_fulltext_gap_closed") is not True or
            any(paper["explicit_decision"].get(k) is not False for k in REQUIRED_DENIALS)):
        raise ValueError("Unverified source data cannot promote geometry/contacts")
    turkey = paper.get("reconciled_turkish_2018_primary", {})
    if (turkey.get("doi") != "10.5603/FM.a2018.0002" or
            turkey.get("pmid") != "29345718" or
            turkey.get("population_male_n") != 97 or
            turkey.get("source_exact_total_definition") !=
            "CL = length of manubrium (M) plus length of body (B)" or
            turkey.get("xiphoid_included_in_154_1mm_total") is not False or
            turkey.get("source_xiphoid_separately_measured") is not True or
            turkey.get("historical_canonical_file_mutated") is not False or
            turkey.get("historical_value_correct_but_semantic_label_wrong") is not True or
            turkey.get("male_combined_CL_mm",{}).get("mean") != 154.1 or
            turkey.get("male_xiphoid_separate_mm",{}).get("mean") != 39.1 or
            turkey.get("male_manubrium_mm",{}).get("mean") != 51.2 or
            turkey.get("male_body_mm",{}).get("mean") != 102.4):
        raise ValueError("Original Turkish CT total endpoint exclusion not verified")
    if (paper["explicit_decision"].get("turkish_2018_semantic_source_label_error_identified") is not True or
            paper["explicit_decision"].get("length_comparison_method_contradiction_resolved") is not False):
        raise ValueError("Historical source label requires noncanonical correction; target unresolved")
    prev=prior.get("population_male_means_mm",{}).get("total_including_xiphoid_turkey_CT",{})
    a003=prior.get("a003",{})
    if (prev.get("mean")!=154.1 or prev.get("sd")!=13.1 or
            a003.get("sternum_stick_mm")!=213.2 or
            a003.get("manubriosternal_depth_mm")!=76.1):
        raise ValueError("Historical evidence record changed unexpectedly")
    if (paper.get("comparative_existing_evidence",{}).get(
            "matching_physical_endpoints_independently_confirmed") is not False or
            paper.get("comparative_existing_evidence",{}).get(
            "a003_sternal_stick_mm") != a003["sternum_stick_mm"]):
        raise ValueError("Endpoint or target equivalence claimed without evidence")
    new_total=round(10*table["total_sternum_length_cm"]["mean"],1)
    new_sd=round(10*table["total_sternum_length_cm"]["sd"],1)
    manubrium=round(10*table["manubrium_length_cm"]["mean"],1)
    body=round(10*table["body_length_cm"]["mean"],1)
    return {
        "schema_version": 1,
        "kind":"HGPT_NONCANONICAL_STERNUM_PRIMARY_SOURCE_COMPARISON",
        "paper_url":src["primary_fulltext_url"],
        "source_study_male_n":55,
        "historical_turkey_source_samples_not_replaced":True,
        "selthofer_2006_male_total_jugular_to_xiphoid_mean_mm":new_total,
        "selthofer_2006_total_sd_mm":new_sd,
        "selthofer_2006_manubrium_mean_mm":manubrium,
        "selthofer_2006_body_mean_mm":body,
        "source_derived_total_minus_manubrium_minus_body_mean_mm":
            round(new_total-manubrium-body,1),
        "source_derived_component_difference_is_not_xiphoid_accepted_length":True,
        "prior_turkey_CT_reported_mean_mm":prev["mean"],
        "historic_Turkey_total_is_MANUBRIUM_PLUS_BODY_excludes_xiphoid":True,
        "prior_canonical_record_semantic_key_including_xiphoid_is_wrong":True,
        "original_Turkey_CT_male_xiphoid_separately_measured_mm":39.1,
        "original_Turkey_CT_male_manubrium_plus_body_mean_mm":154.1,
        "Selthofer_2006_manubrium_plus_body_mean_mm":round(manubrium+body,1),
        "more_comparable_combined_M_plus_B_means_difference_mm":round(manubrium+body-prev["mean"],1),
        "separately_summed_component_means_difference_mm":round(manubrium+body-51.2-102.4,1),
        "incompatible_totals_arithmetic_difference_NOT_anatomical_conflict_mm":round(new_total-prev["mean"],1),
        "remaining_cross_study_cohort_method_and_stature_difference_unresolved":True,
        "a003_stick_length_mm":a003["sternum_stick_mm"],
        "a003_difference_from_selthofer_unadjusted_mean_mm":
            round(a003["sternum_stick_mm"]-new_total,1),
        "old_a003_stick_vs_Turkey_comparison_was_only_reported_arithmetic":True,
        "source_licensing_republication_cleared":False,
        "notch_by_notch_verified_coordinates_available":False,
        "anatomical_geometry_promoted":False,
        "cp1_gate6_passed":False,
    }


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,default=SOURCE)
    p.add_argument("--prior",type=Path,default=PREVIOUS)
    args=p.parse_args()
    data=json.loads(args.source.read_text(encoding="utf-8"))
    prev=json.loads(args.prior.read_text(encoding="utf-8"))
    print(json.dumps(audit(data,prev),indent=2,sort_keys=True))


if __name__=="__main__":
    main()
