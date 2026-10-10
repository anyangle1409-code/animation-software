#!/usr/bin/env python3
"""U3 clavicle primary-literature source compatibility: no auto-promotion.

Reconciles separately labelled 2004 surface-sensor clavicular SC motion,
2009 transcortical bone-pin rotation, 2011 secondary review statement, and
the unchanged c004 vs generic OpenSim/MoBL candidate. It explicitly does
NOT fit or install a clavicle motion curve, set ROM or alter the skeleton.
"""
import argparse
import json
import math
from pathlib import Path

from whole_body_blender_evidence_gate import ANATOMY,private_review_output

REVIEW=ANATOMY/"audit/primary_clavicle_motion_u3_source_review_20261010.json"
GAP=ANATOMY/"audit/claude_anatomical_development_20261009/clavicle_elevation_gap_c004_v1.json"


def assessment(evidence, gap):
    if (evidence.get("schema_version")!=1 or
            evidence.get("kind")!="PRIMARY_SC_CLAVICLE_U3_SOURCE_COMPATIBILITY_NOT_NUMERICAL_TARGET" or
            gap.get("kind")!="READ_ONLY_FOLLOWER_GAP" or gap.get("finding")!="U3"):
        raise ValueError("source motion review or original U3 record changed")
    primary={s["id"]:s for s in evidence["sources"]}
    if set(primary)!={"ludewig2004_clavicle_surface",
                      "ludewig2009_bone_pin_shoulder",
                      "ludewig2011_shoulder_rehab"}:
        raise ValueError("original clavicle source set changed")
    a,b,c=(primary[k] for k in (
        "ludewig2004_clavicle_surface",
        "ludewig2009_bone_pin_shoulder",
        "ludewig2011_shoulder_rehab"))
    if (a["type"]!="primary_experimental" or a["subjects_total"]!=39 or
            a["asymptomatic_subjects"]!=30 or
            b["type"]!="primary_experimental" or b["subjects_total"]!=12 or
            c["type"]!="secondary_review"):
        raise ValueError("primary clavicle evidence protocol/population changed")
    d={v["quantity"]:v for v in a["measures"]}
    if (set(d)!={"sternoclavicular_elevation",
                 "sternoclavicular_retraction",
                 "sternoclavicular_posterior_axial_rotation"} or
            d["sternoclavicular_elevation"]["reported_maximum_range_deg"]!=[11,15] or
            d["sternoclavicular_retraction"]["reported_maximum_range_deg"]!=[15,29] or
            d["sternoclavicular_posterior_axial_rotation"]["reported_maximum_range_deg"]!=[15,31]):
        raise ValueError("primary SC elevation/retraction/axial rotation roles changed")
    pin={v["quantity"]:v for v in b["measures"]}
    if (pin["sternoclavicular_posterior_axial_rotation"].get("reported_average_deg")!=31 or
            pin["acromioclavicular_posterior_tilt"].get("reported_average_deg")!=19 or
            pin["sternoclavicular_elevation"].get("reported_numeric_trajectory_deg","bad") is not None):
        raise ValueError("31 deg bone-pin axial rotation is NOT clavicle elevation")
    if (c["measures"][0]["quantity"]!="sternoclavicular_elevation" or
            "below 10 degrees" not in c["measures"][0]["descriptive_statement"]):
        raise ValueError("secondary-review comparator changed")
    decision=evidence["unresolved_decision"]
    if any(decision[k] is not False for k in (
        "has_end_angle_clavicle_elevation_primary_curve",
        "has_source_matched_rest_pose",
        "has_verified_SC_AC_GH_axis_transforms",
        "has_independent_bilateral_anatomical_acceptance",
        "bone_mesh_skeleton_change_authorized",
        "canonical_promotion_allowed")):
        raise ValueError("unresolved primary shoulder motion was falsely approved")
    slope=evidence["existing_model_template"]["coefficient_deg_clavicle_elevation_per_deg_humerothoracic"]
    if not isinstance(slope,(int,float)) or not math.isclose(slope,.1025,abs_tol=1e-9):
        raise ValueError("generic MoBL template slope changed; recheck source frame")
    if (gap["clavicle_elevation_per_deg_HT"]!=slope or
            gap["c004"]["left"]["clavicle_chord_mm"]!=151.3 or
            gap["c004"]["right"]["clavicle_chord_mm"]!=151.3):
        raise ValueError("original noncanonical c004 shoulder reference changed")
    results=[]
    for side in ("left","right"):
        profile=gap["c004"][side]
        angle_rows=[]
        for condition in ("HT60","HT90","HT120","HT168"):
            ht=int(condition[2:])
            source=profile[condition]["model_clavicle_elevation_deg"]
            prediction=slope*ht
            if not math.isclose(source,prediction,abs_tol=.011):
                raise ValueError("generic joint model slope or recorded c004 observation mismatch")
            # The 2004 maxima are NOT a hard physiological bound and these
            # HT stages may not be identical to that study's endpoints.
            label=(
                "ABOVE_2004_REPORTED_MAXIMA_RANGE_NOT_PROOF_OF_INVALID_ANATOMY"
                if source>15 else
                "BELOW_2004_REPORTED_MAXIMA_RANGE_NO_MIDRANGE_TARGET"
                if source<11 else
                "WITHIN_2004_REPORTED_MAXIMA_RANGE_NO_CURVE_VALIDATION"
            )
            angle_rows.append({
                "humerothoracic_command_deg":ht,
                "generic_model_elevation_deg":source,
                "comparison_to_2004_reported_task_maxima":label,
                "literal_2004_midrange_curve_or_target_verified":False,
                "bone_pin_SC_elevation_source_curve_available":False,
                "candidate_c004_elevation_installed":False,
            })
        results.append({"side":side,"hypothetical_generic_model":angle_rows})
    return {
        "kind":"SOURCE_COMPARISON_U3_CLAVICLE_NO_MOTION_TARGET_SELECTED",
        "source_2004_primary_population":"39, 30 asymptomatic; original surface EM observations",
        "source_2004_reported_SC_elevation_maxima_deg":[11,15],
        "source_2009_primary_bone_pin_subjects":12,
        "source_2009_31deg_is_SC_posterior_axial_rotation_not_elevation":True,
        "source_2011_below_10deg_is_secondary_not_hard_limit":True,
        "c004_installed_clavicle_elevation":"NONE",
        "generic_mobl_slope_deg_per_deg_ht":slope,
        "sensitivity_not_target":results,
        "primary_curve_per_HT_angle_verified":False,
        "thorax_clavicle_joint_frames_match_verified":False,
        "candidate_motion_curve_authorized":False,
        "skeleton_or_mesh_change_authorized":False,
        "canonical_promotion_allowed":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    out=private_review_output(args.out)
    if out.exists() or out.suffix.lower()!=".json":
        raise ValueError("output must be new private JSON outside Git")
    report=assessment(json.loads(REVIEW.read_text()),json.loads(GAP.read_text()))
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("x",encoding="utf8") as fp:
        json.dump(report,fp,indent=2,sort_keys=True);fp.write("\n")
    print(json.dumps({
        "primary_SC_elevation_maxima_deg":report["source_2004_reported_SC_elevation_maxima_deg"],
        "generic_model_deg_per_deg_HT":report["generic_mobl_slope_deg_per_deg_ht"],
        "source_motion_curve_selected":False,
        "canonical_promotion_allowed":False},indent=2))


if __name__=="__main__":
    main()
