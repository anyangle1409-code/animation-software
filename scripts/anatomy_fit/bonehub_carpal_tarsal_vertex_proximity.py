#!/usr/bin/env python3
"""Read-only closest *surface vertex* evidence for adjacent actual BoneHub bones.

This is a **conservative upper bound** on minimum Euclidean surface distance,
NOT exact triangle-triangle spacing or joint/contact-centre identification.
Raw, immutable-SHA-verified source surfaces share a declared STL LPS frame,
but source units, image registration and canonical anatomy are NOT accepted.

No external geometry/numerical dependency, no Blender, CT or mesh writes.
Small detached legitimate face islands are retained; orphan vertices from
degenerate faces are excluded. No acceptance/promotion flags can be true.
"""
from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from pathlib import Path

if __package__:
    from .bonehub_54_surface_audit import (FROZEN_UPSTREAM_REV, build_report,
                                            get_bytes, select_bones)
    from .bonehub_surface_intake import private_location
else:
    from bonehub_54_surface_audit import (FROZEN_UPSTREAM_REV, build_report,
                                           get_bytes, select_bones)
    from bonehub_surface_intake import private_location

ROOT = Path(__file__).resolve().parents[2]
PAIR_NAMES = (
    ("HAND_{side}/SCAPHOID_{side}.stl",
     "HAND_{side}/LUNATE_{side}.stl", "scaphoid_lunate"),
    ("FOOT_{side}/TALUS_{side}.stl",
     "FOOT_{side}/CALCANEUS_{side}.stl", "talus_calcaneus"),
    ("FOOT_{side}/TALUS_{side}.stl",
     "FOOT_{side}/NAVICULAR_{side}.stl", "talus_navicular"),
    ("FOOT_{side}/CALCANEUS_{side}.stl",
     "FOOT_{side}/CUBOID_{side}.stl", "calcaneus_cuboid"),
)
MAX_TRIANGLES = 320_000
MAX_UNIQUE_VERTICES = 600_000


def vertices_from_binary_stl(raw: bytes) -> tuple[tuple[tuple[float,float,float],...],dict]:
    """Use vertices only when they belong to actual nonzero-area STL faces."""
    if len(raw) < 134:
        raise ValueError("Truncated STL")
    head = raw[:80].upper()
    if b"SPACE=LPS" not in head or b"SPACE=RAS" in head:
        raise ValueError("Expected pinned LPS source label; source coordinates not established")
    count = struct.unpack_from("<I", raw, 80)[0]
    if not 0 < count <= MAX_TRIANGLES or len(raw) != 84+50*count:
        raise ValueError("STL triangle count and length mismatch")
    verts: set[tuple[float,float,float]] = set()
    skipped = 0
    for i in range(count):
        t = struct.unpack_from("<12fH", raw, 84+50*i)
        a,b,c = (tuple(t[3:6]),tuple(t[6:9]),tuple(t[9:12]))
        if not all(math.isfinite(x) for p in (a,b,c) for x in p):
            raise ValueError("Nonfinite source surface coordinate")
        ab = tuple(b[j]-a[j] for j in range(3))
        ac = tuple(c[j]-a[j] for j in range(3))
        cross = (ab[1]*ac[2]-ab[2]*ac[1],
                 ab[2]*ac[0]-ab[0]*ac[2],
                 ab[0]*ac[1]-ab[1]*ac[0])
        if len({a,b,c}) < 3 or all(v==0 for v in cross):
            skipped += 1
            continue
        verts.update((a,b,c))
        if len(verts)>MAX_UNIQUE_VERTICES:
            raise ValueError("Source surface unexpectedly large")
    if len(verts)<3 or count==skipped:
        raise ValueError("No usable source surface")
    result=tuple(sorted(verts))
    return result, {
        "source_triangle_count": count,
        "source_degenerate_triangles_excluded":skipped,
        "source_unique_valid_face_vertices":len(result),
        "orphan_degenerate_only_points_excluded":True,
        "all_valid_face_islands_retained":True,
        "header_declared_frame":"LPS",
    }


def kd_tree(points: list[tuple[float,float,float]], level: int=0):
    """Balanced exact vertex tree, no low-resolution decimation/sampling."""
    if not points:
        return None
    axis=level%3
    points.sort(key=lambda x:(x[axis],x))
    mid=len(points)//2
    # Lists after slicing are intentional; this tree is private, not a patient output.
    return (points[mid],axis,
            kd_tree(points[:mid],level+1),
            kd_tree(points[mid+1:],level+1))


def dist2(a,b) -> float:
    return sum((a[i]-b[i])**2 for i in range(3))


def nearest_point(tree, point, best=None):
    """Deterministic exact 3D nearest-neighbour among vertices."""
    if tree is None:
        return best
    node,axis,left,right=tree
    proposal=(dist2(node,point),node)
    if best is None or proposal<best:
        best=proposal
    diff=point[axis]-node[axis]
    first,second=(left,right) if diff<=0 else (right,left)
    best=nearest_point(first,point,best)
    if diff*diff<=best[0]:
        best=nearest_point(second,point,best)
    return best


def closest_vertex_pair(a,b) -> tuple[float,tuple,tuple]:
    if not a or not b:
        raise ValueError("Empty surface")
    # Keep source A/B semantic order independent of tree choice.
    if len(a)>len(b):
        d,pb,pa=closest_vertex_pair(b,a)
        return d,pa,pb
    tree=kd_tree(list(b))
    result=None
    for pa in a:
        d2,pb=nearest_point(tree,pa)
        candidate=(d2,pa,pb)
        if result is None or candidate<result:
            result=candidate
    return math.sqrt(result[0]), result[1], result[2]


def bbox_lower_bound(a,b) -> float:
    axes=[]
    for i in range(3):
        alo,ahi=min(p[i] for p in a),max(p[i] for p in a)
        blo,bhi=min(p[i] for p in b),max(p[i] for p in b)
        axes.append(max(0.0,blo-ahi,alo-bhi))
    return math.sqrt(sum(d*d for d in axes))


def pair_diagnostic(a: tuple, b: tuple) -> dict:
    distance,_,_=closest_vertex_pair(a,b)
    lb=bbox_lower_bound(a,b)
    if not (math.isfinite(distance) and math.isfinite(lb) and
            0<=lb<=distance+1e-8):
        raise ValueError("Point-cloud nearest-neighbour bound failed")
    return {
        "minimum_source_face_vertex_pair_distance_source_units_unknown":round(distance,9),
        "bbox_separation_lower_bound_source_units_unknown":round(lb,9),
        "vertex_distance_is_upper_bound_on_true_triangle_surface_minimum":True,
        "bbox_distance_is_lower_bound_on_true_triangle_surface_minimum":True,
        "no_triangle_intersection_or_containment_test_performed":True,
        "contact_patch_or_joint_centre_identified":False,
        "real_physical_units_verified":False,
        "ct_to_stl_registration_accepted":False,
        "skeletal_geometry_accepted":False,
    }


def audit(index: dict, private_dir: Path, download:bool) -> dict:
    if private_dir.is_symlink():
        raise ValueError("Symlink private source directory refused")
    selected=select_bones(index)
    by_path={row["source_relpath"]:row for row in selected}
    cache={}
    records=[]
    for side in ("LEFT","RIGHT"):
        for a_template,b_template,name in PAIR_NAMES:
            a_path=a_template.format(side=side)
            b_path=b_template.format(side=side)
            if a_path not in by_path or b_path not in by_path:
                raise ValueError("Expected adjacent-file labels absent from 54-file cohort")
            record={"pair_family":name,"declared_side":side,
                    "source_files":[a_path,b_path],"items":[]}
            for path in (a_path,b_path):
                item=by_path[path]
                if path not in cache:
                    raw=get_bytes(item,private_dir,download)
                    points,properties=vertices_from_binary_stl(raw)
                    cache[path]=(points,properties,item["selected_verified_pin"])
                pts,properties,sha=cache[path]
                record["items"].append({
                    "source_relpath":path,
                    "immutable_raw_sha256_verified":sha,
                    **properties,
                })
            record["measurement"]=pair_diagnostic(cache[a_path][0],cache[b_path][0])
            records.append(record)
    return {
        "schema_version":1,
        "kind":"HGPT_NONCANONICAL_SOURCE_VERTICES_BILATERAL_CARPAL_TARSAL_GAP",
        "source_revision":FROZEN_UPSTREAM_REV,
        "distinct_CT_subjects":1,
        "source_subject_independent_of_NLM_visible_human_CT":False,
        "source_mesh_count_examined":len(cache),
        "adjacent_source_pair_count":len(records),
        "measurement_frame":"declared STL LPS only; source units NOT accepted",
        "primary_CT_rescale_and_registration_verified":False,
        "real_distance_units_in_mm_verified":False,
        "actual_triangle_distance_or_contact_centre_established":False,
        "canonical_targets_selected":False,
        "anatomical_region_readiness_changed":False,
        "cp1_gate6_passed":False,
        "source_pair_measurements":records,
    }


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-dir",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--download",action="store_true",
                        help="Explicitly allow downloading pinned STL source files to private cache")
    args=parser.parse_args()
    try:
        private=private_location(args.private_dir)
        out=private_location(args.output)
        if out.exists() or out.is_symlink():
            raise ValueError("Refusing to overwrite existing diagnostics")
        if out.parent != private and private not in out.parents:
            raise ValueError("Output must be inside private directory")
        out.parent.mkdir(parents=True,exist_ok=True)
        result=audit(build_report(),private,args.download)
        with out.open("x",encoding="utf-8") as f:
            json.dump(result,f,indent=2,sort_keys=True)
            f.write("\n")
        print(json.dumps({
            "source_sha256_checked_meshes":result["source_mesh_count_examined"],
            "side_paired_actual_source_surface_proximities":result["adjacent_source_pair_count"],
            "source_units_verified":False,"anatomical_contacts_accepted":False,
            "report":str(out)},indent=2))
        return 0
    except (ValueError,KeyError,OverflowError,OSError) as e:
        print("Fail-closed source proximity: "+str(e),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
