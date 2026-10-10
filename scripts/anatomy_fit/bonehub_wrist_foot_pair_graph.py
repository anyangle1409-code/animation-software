#!/usr/bin/env python3
"""Audit all 8+7 labelled carpal/tarsal bones and an anatomical adjacency *hypothesis*.

This is SOURCE-ONLY, not verified actual articular surface contact. All original
bone bytes are independently re-hashed and remain outside the repo. Exactly one
NLM Visible Human male (180cm) is used, not 30 independent subjects.
The numeric gap is the exact minimum valid-face VERTEX pair distance, merely
an UPPER bound on minimum triangle-surface separation, in UNACCEPTED source
coordinates. No CT registration, unit, clinical normality or promotion.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

if __package__:
    from .bonehub_carpal_tarsal_vertex_proximity import (
        FROZEN_UPSTREAM_REV, bbox_lower_bound, kd_tree, nearest_point,
        vertices_from_binary_stl, build_report, get_bytes, select_bones)
    from .bonehub_surface_intake import private_location
else:
    from bonehub_carpal_tarsal_vertex_proximity import (
        FROZEN_UPSTREAM_REV, bbox_lower_bound, kd_tree, nearest_point,
        vertices_from_binary_stl, build_report, get_bytes, select_bones)
    from bonehub_surface_intake import private_location

# Anatomical textbook-level relationships are candidate LABEL connections, not
# bone-surface cartilage patches identified for this particular patient.
# The lunate/hamate and cuboid/navicular relationships vary among individuals:
# they remain CONTEXT_CANDIDATE rather than universally compulsory topology.
# Source: IMAIOS e-Anatomy Intercarpal / Intertarsal joint descriptions.
# No figures, trained models, patient data or article text are reproduced.
CARPAL_LABELS=(
    "SCAPHOID","LUNATE","TRIQUETRUM","PISIFORM",
    "TRAPEZIUM","TRAPEZOID","CAPITATE","HAMATE"
)
TARSAL_LABELS=(
    "TALUS","CALCANEUS","NAVICULAR","CUBOID",
    "MEDIAL_CUNEIFORM","INTERMEDIATE_CUNEIFORM","LATERAL_CUNEIFORM"
)
# Each pair is unordered but deliberately retained in first-party source.
CARPAL_CANDIDATES=(
    ("SCAPHOID","LUNATE","PROXIMAL_ROW"),
    ("LUNATE","TRIQUETRUM","PROXIMAL_ROW"),
    ("TRIQUETRUM","PISIFORM","PISOTRIQUETRAL"),
    ("TRAPEZIUM","TRAPEZOID","DISTAL_ROW"),
    ("TRAPEZOID","CAPITATE","DISTAL_ROW"),
    ("CAPITATE","HAMATE","DISTAL_ROW"),
    ("SCAPHOID","TRAPEZIUM","MIDCARPAL"),
    ("SCAPHOID","TRAPEZOID","MIDCARPAL"),
    ("SCAPHOID","CAPITATE","MIDCARPAL"),
    ("LUNATE","CAPITATE","MIDCARPAL"),
    ("LUNATE","HAMATE","CONTEXT_CANDIDATE"),
    ("TRIQUETRUM","HAMATE","MIDCARPAL")
)
TARSAL_CANDIDATES=(
    ("TALUS","CALCANEUS","SUBTALAR"),
    ("TALUS","NAVICULAR","TALONAVICULAR"),
    ("CALCANEUS","CUBOID","CALCANEOCUBOID"),
    ("NAVICULAR","MEDIAL_CUNEIFORM","NAVICULOCUNEIFORM"),
    ("NAVICULAR","INTERMEDIATE_CUNEIFORM","NAVICULOCUNEIFORM"),
    ("NAVICULAR","LATERAL_CUNEIFORM","NAVICULOCUNEIFORM"),
    ("MEDIAL_CUNEIFORM","INTERMEDIATE_CUNEIFORM","INTERCUNEIFORM"),
    ("INTERMEDIATE_CUNEIFORM","LATERAL_CUNEIFORM","INTERCUNEIFORM"),
    ("LATERAL_CUNEIFORM","CUBOID","CUNEOCUBOID"),
    ("NAVICULAR","CUBOID","CONTEXT_CANDIDATE"),
)
RAW_GRAPH_URLS=(
    "https://www.imaios.cn/en/e-anatomy/anatomical-structures/intercarpal-joints-1162088",
    "https://www.imaios.cn/en/e-anatomy/anatomical-structures/intertarsal-joints-1537028712",
)
PAIR_COUNT=2*(len(CARPAL_CANDIDATES)+len(TARSAL_CANDIDATES))
MESH_COUNT=2*(len(CARPAL_LABELS)+len(TARSAL_LABELS))
# Independently already measured on previous PR #38 / CI 38086284050.
# Three decimal places only; do not claim additional exact precision.
PR38_REFERENCE_ROUNDED={
    ("LEFT","SCAPHOID","LUNATE"):0.875,
    ("RIGHT","SCAPHOID","LUNATE"):0.910,
    ("LEFT","TALUS","CALCANEUS"):0.382,
    ("RIGHT","TALUS","CALCANEUS"):0.590,
    ("LEFT","TALUS","NAVICULAR"):0.347,
    ("RIGHT","TALUS","NAVICULAR"):0.907,
    ("LEFT","CALCANEUS","CUBOID"):0.590,
    ("RIGHT","CALCANEUS","CUBOID"):1.057,
}

def label_path(region:str, side:str, bone:str)->str:
    if region=="carpus":
        if bone not in CARPAL_LABELS:
            raise ValueError("Unknown carpal label")
        return f"HAND_{side}/{bone}_{side}.stl"
    if region=="tarsus":
        if bone not in TARSAL_LABELS:
            raise ValueError("Unknown tarsal label")
        return f"FOOT_{side}/{bone}_{side}.stl"
    raise ValueError("Invalid anatomical region")

def verify_graph()->None:
    """Fail-closed, no guessed extra joints or missing named individual bones."""
    if (len(CARPAL_CANDIDATES)!=12 or len(TARSAL_CANDIDATES)!=10 or
        PAIR_COUNT!=44 or MESH_COUNT!=30 or
        len(PR38_REFERENCE_ROUNDED)!=8):
        raise ValueError("Expected historical patient source graph changed")
    for region, labels, edges in (
        ("carpus",CARPAL_LABELS,CARPAL_CANDIDATES),
        ("tarsus",TARSAL_LABELS,TARSAL_CANDIDATES)
    ):
        seen=set()
        discovered=set()
        for a,b,kind in edges:
            if a==b or a not in labels or b not in labels or not kind:
                raise ValueError("Unexpected or self-connected candidate edge")
            key=tuple(sorted((a,b)))
            if key in seen:
                raise ValueError("Duplicate anatomical candidate pair")
            seen.add(key)
            discovered.update((a,b))
        if discovered!=set(labels):
            raise ValueError(f"Missing some {region} labelled source bones")

def min_vertex_distance_with_cached_tree(a:tuple,b:tuple,tree_a,tree_b)->float:
    if not a or not b or tree_a is None or tree_b is None:
        raise ValueError("Incomplete actual valid-face source points")
    if len(a)<=len(b):
        small=a
        tree=tree_b
    else:
        small=b
        tree=tree_a
    lowest=math.inf
    for vertex in small:
        d2,_ = nearest_point(tree,vertex)
        if d2<lowest:
            lowest=d2
            if lowest==0:
                break
    d=math.sqrt(lowest)
    if not math.isfinite(d) or d<0:
        raise ValueError("Bad closest source-face-vertex result")
    return d

def audit_graph(index:dict, private_dir:Path, allow_download:bool=False)->dict:
    verify_graph()
    if private_dir.is_symlink():
        raise ValueError("Refuse private cache symlink")
    selected={i["source_relpath"]:i for i in select_bones(index)}
    paths={
       label_path(region,side,bone)
       for side in ("LEFT","RIGHT")
       for region,labels in (("carpus",CARPAL_LABELS),("tarsus",TARSAL_LABELS))
       for bone in labels
    }
    if len(paths)!=MESH_COUNT or not paths.issubset(selected):
        raise ValueError("Missing at least one of the exact 30 source mesh paths")
    cached={}
    for path in sorted(paths):
        item=selected[path]
        raw=get_bytes(item,private_dir,allow_download)  # checks immutable SHA+size
        points,properties=vertices_from_binary_stl(raw)
        cached[path]={
            "vertices":points,
            "tree":kd_tree(list(points)),
            "sha256":item["selected_verified_pin"],
            "triangles":properties["source_triangle_count"],
            "degenerate_excluded":properties["source_degenerate_triangles_excluded"],
            "all_real_face_islands_preserved":properties["all_valid_face_islands_retained"],
        }
    measurements=[]
    for region,edges in (("carpus",CARPAL_CANDIDATES),("tarsus",TARSAL_CANDIDATES)):
        for side in ("LEFT","RIGHT"):
            for a,b,group in edges:
                first=label_path(region,side,a)
                second=label_path(region,side,b)
                ca,cb=cached[first],cached[second]
                dist=min_vertex_distance_with_cached_tree(
                    ca["vertices"],cb["vertices"],ca["tree"],cb["tree"])
                lb=bbox_lower_bound(ca["vertices"],cb["vertices"])
                if lb<0 or lb>dist+1e-8:
                    raise ValueError("Bounding-box lower bound exceeds valid-vertex gap")
                measurements.append({
                    "region":region,
                    "source_side_label":side,
                    "a":a,"b":b,
                    "anatomical_relation_hypothesis":group,
                    "source_files":[first,second],
                    "source_sha256_pins":[ca["sha256"],cb["sha256"]],
                    "bbox_lower_bound_unapproved_source_units":round(lb,9),
                    "closest_valid_face_vertex_upper_bound_unapproved_source_units":round(dist,9),
                    "this_is_not_triangle_surface_or_cartilage_contact":True,
                    "anatomical_joint_candidate_identity_accepted":False
                })
    if len(measurements)!=PAIR_COUNT:
        raise ValueError("Missing source pair measurements")
    checks=[]
    for (side,a,b),expected in PR38_REFERENCE_ROUNDED.items():
        found=[m for m in measurements
               if m["source_side_label"]==side and m["a"]==a and m["b"]==b]
        if len(found)!=1:
            raise ValueError("Missing prior verified PR38 source pair")
        actual=found[0]["closest_valid_face_vertex_upper_bound_unapproved_source_units"]
        if not abs(actual-expected)<0.00051:
            raise ValueError("Prior independently checked source-pair distance changed")
        checks.append({"side":side,"source_pair":[a,b],"matches_original_3dp":True})
    return {
        "schema_version":1,
        "kind":"HGPT_NONCANONICAL_BILATERAL_30_BONE_GRAPH_SOURCE_VERTEX_BOUNDS",
        "official_original_source_revision":FROZEN_UPSTREAM_REV,
        "source_same_single_NLM_visible_human_subject":True,
        "source_n_subjects":1,
        "source_meshes_full_SHA256_and_size_verified":MESH_COUNT,
        "expected_bone_labels_per_side":{"carpus":8,"tarsus":7},
        "source_pair_count":PAIR_COUNT,
        "original_PR38_source_pair_regression_checks":checks,
        "all_original_source_triangles_modified":False,
        "all_actual_nonzero_face_islands_preserved":True,
        "used_no_source_vertex_decimation":True,
        "source_frame_declared_LPS_not_NLM_CT_registration":True,
        "native_source_coordinates_physical_mm_accepted":False,
        "source_to_CT_registration_completed":False,
        "independent_normal_population_validation_completed":False,
        "joint_cartilage_patches_or_bone_contact_centres_accepted":False,
        "all_source_label_edges_were_true_this_subject_articulations_verified":False,
        "canonical_bone_centres_or_mesh_updated":False,
        "CP1_gate6_ready":False,
        "regional_freeze_readiness_changed":False,
        "source_joint_graph_context_links":list(RAW_GRAPH_URLS),
        "pair_measurements":measurements,
    }

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-dir",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--download",action="store_true",
                        help="Explicit consent to download SHA-frozen public original STLs to external private cache")
    args=parser.parse_args()
    try:
        private=private_location(args.private_dir)
        out=private_location(args.output)
        if out.exists() or out.is_symlink():
            raise ValueError("No report overwrite allowed")
        if out.parent!=private and private not in out.parents:
            raise ValueError("Report must be inside private directory")
        result=audit_graph(build_report(),private,args.download)
        out.parent.mkdir(parents=True,exist_ok=True)
        with out.open("x",encoding="utf-8") as f:
            json.dump(result,f,indent=2,sort_keys=True)
            f.write("\n")
        print(json.dumps({
            "source_sha256_verified_unique_STLs":result["source_meshes_full_SHA256_and_size_verified"],
            "bilateral_labelled_source_pairs":result["source_pair_count"],
            "reference_PR38_pair_checks":len(result["original_PR38_source_pair_regression_checks"]),
            "source_mm_or_joint_centres_accepted":False,
            "report":str(out)
        },indent=2))
        return 0
    except (ValueError,KeyError,OverflowError,OSError) as e:
        print("No-acceptance full carpus/tarsus source pair audit: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
