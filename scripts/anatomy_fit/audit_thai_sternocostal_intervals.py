#!/usr/bin/env python3
"""Validate actual 2022 primary sternum costal-facet distances; never fit HGPT.

The printed source samples are older northern Thai cadavers whose training
statures end at 180cm, below our 182cm male target. Report independent
measurement semantics and *diagnostic* relative spacing only.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/"ORIGINAL_V1_WORK/anatomy/sternum_thai_2022_three_facet_intervals_20261010.json"
OLD = ROOT/"ORIGINAL_V1_WORK/anatomy/canonical_sternum_target_review_v1.json"
EXPECTED = {
    "intercostal_center_distance_2_to_3_mm": (29.30, 3.11, (18.88,36.07)),
    "intercostal_center_distance_3_to_4_mm": (25.20, 2.71, (15.14,32.29)),
    "intercostal_center_distance_4_to_5_mm": (19.56, 2.87, (9.46,28.17)),
}
UNAPPROVED_FIELDS = (
    "remaining_four_or_more_attachment_gaps_missing",
    "side_specific_axes_missing",
    "full_per_notch_depth_targets_available",
    "normative_182cm_calibration_passed",
    "commercial_source_visual_reuse_authorized",
    "canonical_sternum_coordinate_selected",
    "canonical_rib_contacts_selected",
    "existing_canonical_records_mutated",
    "cp1_gate6_passed",
    "regional_readiness_changed",
)

def validate(record: dict, old: dict) -> dict:
    if record.get("kind")!="HGPT_NONCANONICAL_PRIMARY_STERNOCOSTAL_FACET_INTERVALS":
        raise ValueError("Unexpected sternocostal source record")
    src = record["source"]
    if (src.get("doi")!="10.5115/acb.22.045" or src.get("pmid")!="35773219" or
        src.get("pmcid")!="PMC9256492" or src.get("license_reported","").startswith("CC BY-NC 4.0") is not True or
        src.get("paper_or_images_copied_into_repository") is not False or
        (src.get("all_cases_total"),src.get("training_total"),src.get("training_male"),
         src.get("training_female"),src.get("held_out_test_total"),
         src.get("held_out_test_male"),src.get("held_out_test_female"))!=(219,199,104,95,20,10,10)):
        raise ValueError("Original source identity, licence or donor counts changed")
    if (src.get("training_stature_range_cm") != [140,180] or
        src.get("target_stature_cm") != 182 or
        src.get("target_stature_is_inside_study_training_range") is not False or
        src.get("side_specific_measurements_published") is not False):
        raise ValueError("Unjustified target-stature or source-sides claim")
    table = record["male_training_table_2"]
    for field, (mean,sd,rng) in EXPECTED.items():
        cell = table[field]
        if (cell.get("mean")!=mean or cell.get("sd")!=sd or
            cell.get("range")!=list(rng)):
            raise ValueError("Mismatch from original 2022 male Table 2 "+field)
    if (table["manubrium_length_mm"] != {"mean":48.9,"sd":5.28} or
        table["mesosternum_length_mm"] != {"mean":97.12,"sd":9.57} or
        table["combined_jugular_to_mesoxiphoidal_chord_mm"] != {"mean":146.02,"sd":10.41}):
        raise ValueError("Noncomparable source combined length changed")
    defs=record["endpoint_definitions"]
    for pair,field in (("2nd","ICL23"),("3rd","ICL34"),("4th","ICL45")):
        if pair not in defs.get(field,""):
            raise ValueError("Intercostal facet centre pair semantically altered")
    for field in ("not_vertebral_costal_rib_bone_tip_distance","not_3d_cartilage_path_distance",
                  "not_necessarily_sternum_global_vertical_gap","side_and_scanner_frame_not_defined",
                  "other_intervals_not_provided","no_absolute_rib_level_centres_in_common_3d_frame"):
        if defs.get(field) is not True:
            raise ValueError("Original source interval method overinterpreted")
    flags=record["acceptance"]
    if flags.get("verified_three_original_male_intercostal_intervals") is not True:
        raise ValueError("Verified original subset missing")
    for field in UNAPPROVED_FIELDS:
        intended = field in ("remaining_four_or_more_attachment_gaps_missing","side_specific_axes_missing")
        if flags.get(field) is not intended:
            raise ValueError("Cannot promote unavailable sternocostal geometry: "+field)
    previous=old["a003"]["sternocostal_depth_mm"]
    if any(previous.get(k)!=v for k,v in {"2":38.7,"3":73.9,"4":105.8,"5":136.8}.items()):
        raise ValueError("Existing nonanatomical a003 control baseline changed")
    if record["comparison"]["a003_is_3d_facets_with_matching_study_endpoint"] is not False:
        raise ValueError("Model vertical point markers not proven to match cartilage-facet centres")
    means=[EXPECTED[k][0] for k in EXPECTED]
    if not (means[0]>means[1]>means[2]):
        raise ValueError("Expected decreasing original male mean spacing")
    return {
        "kind":"HGPT_NONCANONICAL_STERNOCOSTAL_THREE_INTERVAL_AUDIT",
        "doi":src["doi"],
        "n_training_male":104,
        "target_182cm_outside_training_stature_range":True,
        "source_study_means_center2_to3_3to4_4to5_mm":means,
        "successive_mean_interval_decreases_mm":[round(means[0]-means[1],2),
                                                  round(means[1]-means[2],2)],
        "final_to_initial_mean_interval_ratio":round(means[-1]/means[0],4),
        "a003_vertical_level_spacing_2to3_3to4_4to5_diagnostic_only_mm":[
           round(previous["3"]-previous["2"],1),
           round(previous["4"]-previous["3"],1),
           round(previous["5"]-previous["4"],1)
        ],
        "true_3d_facet_centres_captured":False,
        "source_noncommercial_visual_reuse_cleared":False,
        "absolute_spatial_transforms_or_joint_centres_selected":False,
        "remaining_notch_levels_unresolved":True,
        "canonical_geometry_changed":False,
        "cp1_gate6_passed":False
    }

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,default=SOURCE)
    p.add_argument("--prior",type=Path,default=OLD)
    args=p.parse_args()
    print(json.dumps(validate(json.loads(args.source.read_text(encoding="utf-8")),
                              json.loads(args.prior.read_text(encoding="utf-8"))),
                     indent=2, sort_keys=True))
