#!/usr/bin/env python3
"""Fail-closed first-party sternum source-endpoint compatibility audit.

Never modifies canonical skeletons, source PDFs, Blender assets, muscles or mesh.
A matched historical mean is NOT evidence for an accepted 182 cm joint target.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANATOMY = ROOT / "ORIGINAL_V1_WORK/anatomy"
CONTRACT = ANATOMY / "sternum_endpoint_compatibility_contract_20261010.json"
OLDER = ANATOMY / "canonical_sternum_target_review_v1.json"
GEO = ANATOMY / "canonical_sternum_geometry_audit_v1.json"
SELT = ANATOMY / "sternum_selthofer_2006_primary_table_recheck_20261010.json"
THAI = ANATOMY / "sternum_thai_2022_three_facet_intervals_20261010.json"

EXPECTED_PINNED_INPUTS = {
    "canonical_sternum_target_review_v1.json": "8103df8daf4b96eafb7bbca5a01f3ea0fbcbc053",
    "canonical_sternum_geometry_audit_v1.json": "775bcbb158c227a6f7e5b246e2b23f2735ad414b",
    "sternum_selthofer_2006_primary_table_recheck_20261010.json": "feeec9f44a8c729b9b416d6325089b15dd5fa44b",
    "sternum_thai_2022_three_facet_intervals_20261010.json": "47503b8f92c7c47c224b9a123d8f5a7169ff2b4a",
}
EXPECTED_INCOMPATIBLE_PAIRS = {
    frozenset(("SELTHOFER2006_WHOLE", "TURKEY2018_CL")): (
        "DISTAL_XIPHOID_INCLUDED_VS_EXCLUDED", 54.5),
    frozenset(("SELTHOFER2006_WHOLE", "A003_JUGULAR_TO_XIPHISTERNAL_CHORD")): (
        "DISTAL_XIPHOID_VS_XIPHISTERNAL_AND_MODEL_CONTROL", None),
    frozenset(("SELTHOFER2006_SUM_M_B", "TURKEY2018_CL")): (
        "DERIVED_SUM_OF_COHORT_MEANS_VS_DIRECT_COMPOSITE_DIFFERENT_STUDIES", 10.8),
    frozenset(("THAI2022_CMM", "TURKEY2018_CL")): (
        "DIRECT_CHORD_VS_CL_COMBINED_MEASUREMENT_AND_COHORT", None),
    frozenset(("THAI2022_ICL23", "A003_LEVEL2_3_Z")): (
        "3D_COSTAL_FACET_SPACING_VS_MODEL_Z_PROJECTION", None),
}
DENIAL_KEYS = {
    "allow_absolute_sternum_target": False,
    "allow_automatic_source_pooling": False,
    "allow_assuming_joint_centres_from_group_means": False,
    "allow_using_legacy_misnamed_total_as_xiphoid_inclusive": False,
    "allow_rib_level_1_to7_contact_reconstruction": False,
    "allow_mesh_skin_refit": False,
    "allow_canonical_geometry_mutation": False,
    "allow_CP1_Gate6_promotion": False,
    "regions_READY": 0,
    "regions_PARTIAL": 9,
    "regions_BLOCKED": 3,
}
SOURCE_ELIGIBILITY = {
    "all_primary_data_originals_preserved": True,
    "thai_182cm_target_outside_sample_height_range": True,
    "thai_article_CC_BY_NC_figures_not_imported": True,
    "no_182cm_population_regression_selected": True,
    "no_CT_STL_to_model_registration": True,
    "no_source_to_joint_patch_correspondence": True,
    "no_full_1_to7_costal_facet_3d_contact_coords": True,
}

def git_blob_sha_lf(raw: bytes) -> str:
    # Track Git's canonical LF bytes, including from Windows core.autocrlf clones.
    normalized = raw.replace(b"\r\n", b"\n")
    return hashlib.sha1(
        b"blob " + str(len(normalized)).encode("ascii") + b"\0" + normalized
    ).hexdigest()

def verify_original_input_pins() -> None:
    for name, expected_sha in EXPECTED_PINNED_INPUTS.items():
        path = ANATOMY / name
        if git_blob_sha_lf(path.read_bytes()) != expected_sha:
            raise ValueError("Historical source bytes drifted: "+name)

def read(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object: " + str(path))
    return data

def expected_measurements(sel: dict, thai: dict, geo: dict) -> dict:
    t = sel["male_table_primary"]
    tr = sel["reconciled_turkish_2018_primary"]
    st = thai["male_training_table_2"]
    def cm(field):
        return float(t[field]["mean"]) * 10, float(t[field]["sd"]) * 10
    whole,whole_sd=cm("total_sternum_length_cm")
    manu,manu_sd=cm("manubrium_length_cm")
    body,body_sd=cm("body_length_cm")
    source_types = {
        "SELTHOFER2006_WHOLE": (whole,whole_sd,"JUGULAR_TO_DISTAL_XIPHOID_TOTAL_LENGTH",True,55),
        "SELTHOFER2006_M": (manu,manu_sd,"MANUBRIUM_ANATOMICAL_LENGTH",False,55),
        "SELTHOFER2006_B": (body,body_sd,"MESOSTERNUM_ANATOMICAL_LENGTH",False,55),
        "SELTHOFER2006_SUM_M_B": (manu+body,None,"M_PLUS_B_ARITHMETIC_SUM_OF_MEANS",False,55),
        "TURKEY2018_CL": (tr["male_combined_CL_mm"]["mean"],
                         tr["male_combined_CL_mm"]["sd"],"MANUBRIUM_PLUS_BODY_SOURCE_COMBINED_CL",False,97),
        "TURKEY2018_XIPHOID": (tr["male_xiphoid_separate_mm"]["mean"],
                              tr["male_xiphoid_separate_mm"]["sd"],"XIPHOID_PROCESS_LENGTH",True,97),
        "THAI2022_CMM": (st["combined_jugular_to_mesoxiphoidal_chord_mm"]["mean"],
                         st["combined_jugular_to_mesoxiphoidal_chord_mm"]["sd"],
                         "JUGULAR_TO_MESOXIPHOIDAL_STRAIGHT_CHORD",False,104),
        "A003_JUGULAR_TO_XIPHISTERNAL_CHORD": (
            geo["current_a003"]["chord_length_mm"],None,"MODEL_CONTROL_JUGULAR_TO_XIPHISTERNAL_CHORD",False,None),
        "A003_LEVEL2_3_Z": (35.2,None,"MODEL_CONTROL_LEVEL2_TO3_Z_PROJECTION",False,None),
    }
    for suffix,field,category in (
            ("23","intercostal_center_distance_2_to_3_mm","FACET_CENTER_EUCLIDEAN_RIB_2_TO_3"),
            ("34","intercostal_center_distance_3_to_4_mm","FACET_CENTER_EUCLIDEAN_RIB_3_TO_4"),
            ("45","intercostal_center_distance_4_to_5_mm","FACET_CENTER_EUCLIDEAN_RIB_4_TO_5")):
        source_types["THAI2022_ICL"+suffix]=(
            st[field]["mean"],st[field]["sd"],category,False,104)
    return source_types

def check_contract(contract: dict, sel: dict, thai: dict, old: dict, geo: dict) -> dict:
    if (contract.get("schema_version") != 1 or
            contract.get("kind") != "HGPT_STERNUM_NONCANONICAL_ENDPOINT_COMPATIBILITY_GATE" or
            contract.get("governing_policy") != "SKELETON_FIRST_NO_ACCEPTED_GEOMETRY_FROM_UNMATCHED_SOURCE_MEANS"):
        raise ValueError("Unrecognized/noncanonical measurement gate")
    observed_paths = contract.get("immutable_existing_sources",[])
    observed = {Path(x["path"]).name: x["git_blob_sha"] for x in observed_paths}
    if len(observed_paths) != len(observed) or observed != EXPECTED_PINNED_INPUTS:
        raise ValueError("Historical data source pin/manifest altered")
    if contract.get("approval") != DENIAL_KEYS:
        raise ValueError("Unauthorized anatomy promotion or altered region readiness")
    if contract.get("source_eligibility") != SOURCE_ELIGIBILITY:
        raise ValueError("Missing source geometry/stature/rights safeguards")
    if (old["population_male_means_mm"]["total_including_xiphoid_turkey_CT"] !=
            {"mean":154.1,"sd":13.1}):
        raise ValueError("Legacy numerical datum changed; migrate semantics separately")
    if (sel["reconciled_turkish_2018_primary"]["xiphoid_included_in_154_1mm_total"] is not False or
            sel["reconciled_turkish_2018_primary"]["historical_value_correct_but_semantic_label_wrong"] is not True or
            sel["explicit_decision"]["canonical_promotion_allowed"] is not False):
        raise ValueError("Turkish xiphoid exclusion/acceptance source evidence changed")
    if (geo["current_a003"]["tail_definition"] != "xiphisternal region, inset from skin; xiphoid itself not included" or
            geo["current_a003"]["placement"] != "surface_landmark"):
        raise ValueError("Old a003 endpoint role not verified")
    if (thai["source"]["training_stature_range_cm"] != [140,180] or
            thai["source"]["target_stature_is_inside_study_training_range"] is not False or
            thai["acceptance"]["cp1_gate6_passed"] is not False):
        raise ValueError("Thai population sample not valid for direct 182cm freeze")
    expected = expected_measurements(sel,thai,geo)
    rows=contract.get("measurement_terms",[])
    ids = [x["id"] for x in rows]
    if len(ids) != len(set(ids)) or set(ids) != set(expected):
        raise ValueError("Missing, duplicate or substituted source measurement")
    by_id = {x["id"]:x for x in rows}
    for ident, (mean,sd,category,xiphoid,n) in expected.items():
        row=by_id[ident]
        if (type(row.get("value_mm")) not in (int,float) or
                not math.isclose(row["value_mm"],mean,abs_tol=1e-7,rel_tol=0) or
                (sd is None and row.get("sd_mm") is not None) or
                (sd is not None and
                 (type(row.get("sd_mm")) not in (int,float) or
                  not math.isclose(row["sd_mm"],sd,abs_tol=1e-7,rel_tol=0))) or
                row.get("measurement_class") != category or
                row.get("xiphoid_included") is not xiphoid or
                row.get("male_n") != n):
            raise ValueError("Anatomical endpoint/sex-cohort/source value mismatch: "+ident)
        if row.get("source_to_HGPT_registered") is not False or row.get("stature_182cm_conditioned") is not False:
            raise ValueError("Unsourced registration or stature normalization claim: "+ident)
        if (ident=="SELTHOFER2006_SUM_M_B" and
                row.get("source_measure")!="derived_sum_of_two_group_means_not_subject_aggregates"):
            raise ValueError("Arithmetic cohort mean conflated with individual direct length")
        if ident.startswith("A003_") and row.get("source_measure")!="legacy_candidate_geometry":
            raise ValueError("Unapproved mesh/model controls passed as primary human evidence")
    if not math.isclose(geo["current_a003"]["chord_length_mm"],by_id["A003_JUGULAR_TO_XIPHISTERNAL_CHORD"]["value_mm"],abs_tol=1e-9):
        raise ValueError("Canonical audit control source changed")
    z=old["a003"]["sternocostal_depth_mm"]
    if not math.isclose(z["3"]-z["2"],by_id["A003_LEVEL2_3_Z"]["value_mm"],abs_tol=1e-8):
        raise ValueError("Wrong model-Z difference")
    pairs=contract.get("forbidden_pairs",[])
    seen=set()
    for pair in pairs:
        key=frozenset((pair["left"],pair["right"]))
        if len(key)!=2 or key in seen or key not in EXPECTED_INCOMPATIBLE_PAIRS:
            raise ValueError("Unsafe cross-source pair list")
        seen.add(key)
        reason, gap=EXPECTED_INCOMPATIBLE_PAIRS[key]
        if pair["reason"]!=reason or pair.get("raw_numeric_gap_mm")!=gap:
            raise ValueError("Known source incompatibility was mislabeled")
    if seen != set(EXPECTED_INCOMPATIBLE_PAIRS):
        raise ValueError("Missing forbidden cross-source comparison")
    return {"measurement_rows":by_id,"forbidden_pairs":seen}

def compare_ids(a: str,b: str,checked: dict) -> dict:
    records=checked["measurement_rows"]
    if a not in records or b not in records or a==b:
        raise ValueError("Unknown or identical measurement ids; cannot establish independent comparison")
    pair=frozenset((a,b))
    reasons={
      key:value[0] for key,value in EXPECTED_INCOMPATIBLE_PAIRS.items()
    }
    if pair in reasons:
        reason=reasons[pair]
    else:
        ra,rb=records[a],records[b]
        reason=("DIFFERENT_BONE_MEASUREMENT_SEMANTICS"
                if ra["measurement_class"] != rb["measurement_class"]
                else "NO_MATCHED_ENDPOINT_METHOD_COHORT_PROVEN")
    return {
      "id_left":a,"id_right":b,
      "source_values_mm":[records[a]["value_mm"],records[b]["value_mm"]],
      "status":"REJECT_FOR_CANONICAL_TARGET",
      "reason":reason,
      "automatic_sternum_mesh_retarget_allowed":False,
    }

def demonstrate_3d_nondetermination(checked: dict) -> dict:
    r=checked["measurement_rows"]
    a,b,c=(r["THAI2022_ICL"+j]["value_mm"] for j in ("23","34","45"))
    # Two physically different three-link arrangements share all three local edge lengths.
    collinear=[(0.,0.,0.),(a,0.,0.),(a+b,0.,0.),(a+b+c,0.,0.)]
    turned=[(0.,0.,0.),(a,0.,0.),(a,b,0.),(a,b,c)]
    def segments(points):
        return [math.dist(points[i],points[i+1]) for i in range(3)]
    if not all(math.isclose(x,y,abs_tol=1e-10) for x,y in zip(segments(collinear),segments(turned))):
        raise ValueError("Constructive non-uniqueness proof invalid")
    return {
      "identical_three_local_facet_intervals_mm":[round(x,2) for x in segments(collinear)],
      "example_chains_not_anatomical_targets":True,
      "same_three_intervals_but_distinct_end_to_end_distance":True,
      "collinear_chain_end_to_end_mm":round(math.dist(collinear[0],collinear[-1]),4),
      "turned_chain_end_to_end_mm":round(math.dist(turned[0],turned[-1]),4),
      "nonunique_3d_geometry_from_three_distances":True,
      "source_3d_rib_contact_positions_selected":False,
    }

def audit(contract:dict,sel:dict,thai:dict,old:dict,geo:dict) -> dict:
    checked=check_contract(contract,sel,thai,old,geo)
    return {
      "schema_version":1,
      "kind":"HGPT_STERNUM_ENDPOINT_FAIL_CLOSED_RESULT",
      "source_measurement_rows":len(checked["measurement_rows"]),
      "forbidden_cross_source_comparisons":[
          compare_ids(pair["left"],pair["right"],checked)
          for pair in contract["forbidden_pairs"]],
      "nonunique_three_notch_3d_counterexample":demonstrate_3d_nondetermination(checked),
      "legacy_Turkey_154_1mm_includes_xiphoid":False,
      "legacy_Turkey_source_key_misnamed":True,
      "Selthofer_208_6mm_and_Turkey_154_1mm_are_not_comparable_totals":True,
      "Selthofer_sum_M_B_minus_Turkey_CL_diagnostic_mm":10.8,
      "all_automatic_sternum_targets_rejected":True,
      "no_canonical_geometry_changed":True,
      "no_CP1_gate_promotion":True,
    }

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract",type=Path,default=CONTRACT)
    p.add_argument("--compare",nargs=2,metavar=("ID_A","ID_B"),
                   help="Ask whether two source measurement terms can justify a canonical bone target")
    args=p.parse_args()
    verify_original_input_pins()
    checked=check_contract(read(args.contract),read(SELT),read(THAI),read(OLDER),read(GEO))
    if args.compare:
        report=compare_ids(*args.compare,checked)
    else:
        report=audit(read(args.contract),read(SELT),read(THAI),read(OLDER),read(GEO))
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
