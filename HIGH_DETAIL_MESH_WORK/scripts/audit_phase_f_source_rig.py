"""Audit a Phase F source-rig/weight candidate against its accepted geometry source.

This does NOT require the candidate to have exactly 63 skin joints. The final
character keeps its authored/source skeleton; hgpt_canonical_v3 is the driver.

Allowed differences:
- source-rig nodes/hierarchy where a deliberate palm/scapula rig repair added or
  corrected source deform controls;
- skin joint lists / inverse binds;
- JOINTS_* / WEIGHTS_*.

Required invariants:
- geometry/topology/UV/normal/colour/material appearance unchanged;
- no weighted reference helper/source bone silently disappears;
- candidate weights normalize;
- no newly unweighted body vertices.

Usage:
  python scripts/audit_phase_f_source_rig.py --reference accepted.glb --candidate final.glb
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
DTYPE={5120:"i1",5121:"u1",5122:"<i2",5123:"<u2",5125:"<u4",5126:"<f4"}
COMPONENTS={"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4,"MAT4":16}

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def load(path):
    data=Path(path).read_bytes()
    if len(data)<28 or struct.unpack_from("<I",data,0)[0]!=0x46546C67:
        raise ValueError(f"Not a GLB: {path}")
    jlen,jtype=struct.unpack_from("<II",data,12)
    if jtype!=0x4E4F534A:raise ValueError("Missing JSON chunk")
    doc=json.loads(data[20:20+jlen])
    off=20+jlen
    blen,btype=struct.unpack_from("<II",data,off)
    if btype!=0x004E4942:raise ValueError("Missing BIN chunk")
    return doc,data[off+8:off+8+blen]

def accessor(doc,binary,ai):
    a=doc["accessors"][ai];v=doc["bufferViews"][a["bufferView"]]
    dt=np.dtype(DTYPE[a["componentType"]]);cols=COMPONENTS[a["type"]]
    stride=v.get("byteStride",dt.itemsize*cols)
    offset=v.get("byteOffset",0)+a.get("byteOffset",0)
    return np.ndarray((a["count"],cols),dt,buffer=binary,offset=offset,
                      strides=(stride,dt.itemsize)).copy()

def first_body(doc):
    return doc["meshes"][0]["primitives"][0]

def node_parents(doc):
    parent={}
    for i,node in enumerate(doc.get("nodes",[])):
        for child in node.get("children",[]):
            parent[int(child)]=i
    return parent

def skin_joint_names(doc,skin_index=0):
    skin=doc["skins"][skin_index]
    return [doc["nodes"][i].get("name",f"<node:{i}>") for i in skin["joints"]]

def weight_attrs(prim):
    pairs=[]
    lane=0
    while f"JOINTS_{lane}" in prim["attributes"] and f"WEIGHTS_{lane}" in prim["attributes"]:
        pairs.append((prim["attributes"][f"JOINTS_{lane}"],prim["attributes"][f"WEIGHTS_{lane}"]))
        lane+=1
    if not pairs:raise RuntimeError("Body has no JOINTS/WEIGHTS attributes")
    return pairs

def weighted_bones(doc,binary,prim,skin_index=0):
    names=skin_joint_names(doc,skin_index)
    totals=defaultdict(float);vertices=defaultdict(int)
    pairs=weight_attrs(prim)
    count=doc["accessors"][pairs[0][0]]["count"]
    sums=np.zeros(count,float);influences=np.zeros(count,int)
    for jai,wai in pairs:
        joints=accessor(doc,binary,jai).astype(int)
        weights=accessor(doc,binary,wai).astype(float)
        for lane in range(joints.shape[1]):
            w=weights[:,lane]
            j=joints[:,lane]
            sums+=w
            influences+=(w>1e-8)
            for idx in np.flatnonzero(w>1e-8):
                ji=int(j[idx])
                if 0<=ji<len(names):
                    totals[names[ji]]+=float(w[idx])
                    vertices[names[ji]]+=1
    return {
        "names":names,
        "total_weight_by_bone":dict(totals),
        "weighted_vertices_by_bone":dict(vertices),
        "weight_sum":sums,
        "influence_count":influences,
    }

def same_accessor(a_doc,a_bin,a_ai,b_doc,b_bin,b_ai):
    a=accessor(a_doc,a_bin,a_ai);b=accessor(b_doc,b_bin,b_ai)
    return a.shape==b.shape and a.dtype==b.dtype and np.array_equal(a,b)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--reference",type=Path,required=True)
    ap.add_argument("--candidate",type=Path,required=True)
    ap.add_argument("--report",type=Path)
    args=ap.parse_args()
    reference=args.reference.resolve();candidate=args.candidate.resolve()
    for p in (reference,candidate):
        if not p.is_file():raise SystemExit(f"Missing GLB: {p}")

    rd,rb=load(reference);cd,cb=load(candidate)
    rp=first_body(rd);cp=first_body(cd)
    ra=rp["attributes"];ca=cp["attributes"]

    # Phase F must not alter accepted mesh data. Skin rows are deliberately excluded.
    protected_attrs=[
        name for name in ra
        if not name.startswith("JOINTS_") and not name.startswith("WEIGHTS_")
    ]
    missing_attrs=[name for name in protected_attrs if name not in ca]
    attr_equal={}
    for name in protected_attrs:
        if name not in ca:continue
        attr_equal[name]=same_accessor(rd,rb,ra[name],cd,cb,ca[name])
    indices_equal=same_accessor(rd,rb,rp["indices"],cd,cb,cp["indices"])

    # Other mesh primitives are appearance/garment data and should be identical.
    other_mesh_equal=True
    if len(rd.get("meshes",[]))!=len(cd.get("meshes",[])):
        other_mesh_equal=False
    else:
        for mi,(rm,cm) in enumerate(zip(rd["meshes"],cd["meshes"])):
            start=1 if mi==0 else 0
            if len(rm.get("primitives",[]))!=len(cm.get("primitives",[])):
                other_mesh_equal=False;break
            for pi in range(start,len(rm.get("primitives",[]))):
                rprim=rm["primitives"][pi];cprim=cm["primitives"][pi]
                if rprim!=cprim:
                    # JSON accessor indices can differ even if data is equal; compare common attributes.
                    if set(rprim.get("attributes",{}))!=set(cprim.get("attributes",{})):
                        other_mesh_equal=False;break
                    for name in rprim.get("attributes",{}):
                        if not same_accessor(rd,rb,rprim["attributes"][name],cd,cb,cprim["attributes"][name]):
                            other_mesh_equal=False;break
                    if not same_accessor(rd,rb,rprim["indices"],cd,cb,cprim["indices"]):
                        other_mesh_equal=False;break
            if not other_mesh_equal:break

    rw=weighted_bones(rd,rb,rp)
    cw=weighted_bones(cd,cb,cp)
    rweighted={k for k,v in rw["total_weight_by_bone"].items() if v>1e-8}
    cweighted={k for k,v in cw["total_weight_by_bone"].items() if v>1e-8}
    lost_weighted=sorted(rweighted-cweighted)
    new_weighted=sorted(cweighted-rweighted)

    candidate_weight_error=np.abs(cw["weight_sum"]-1.0)
    reference_weight_error=np.abs(rw["weight_sum"]-1.0)
    zero_candidate=np.flatnonzero(cw["weight_sum"]<1e-8)
    zero_reference=np.flatnonzero(rw["weight_sum"]<1e-8)

    rparents=node_parents(rd);cparents=node_parents(cd)
    def joint_parent_names(doc,parents):
        skin=doc["skins"][0];out={}
        for node_index in skin["joints"]:
            name=doc["nodes"][node_index].get("name",f"<node:{node_index}>")
            p=parents.get(node_index)
            out[name]=doc["nodes"][p].get("name",f"<node:{p}>") if p is not None else None
        return out
    rparent_names=joint_parent_names(rd,rparents)
    cparent_names=joint_parent_names(cd,cparents)
    hierarchy_changes={
        name:{"reference":rparent_names.get(name),"candidate":cparent_names.get(name)}
        for name in sorted(set(rparent_names)&set(cparent_names))
        if rparent_names.get(name)!=cparent_names.get(name)
    }

    checks={
        "protected_attributes_present":not missing_attrs,
        "accepted_mesh_attributes_exact":all(attr_equal.values()) if attr_equal else False,
        "topology_indices_exact":indices_equal,
        "other_mesh_primitives_unchanged":other_mesh_equal,
        "no_previously_weighted_source_bone_lost":not lost_weighted,
        "candidate_weights_normalized":float(candidate_weight_error.max(initial=0))<=1e-4,
        "no_new_unweighted_vertices":set(zero_candidate.tolist()).issubset(set(zero_reference.tolist())),
    }

    report={
        "reference":reference.name,
        "candidate":candidate.name,
        "reference_sha256":sha256(reference),
        "candidate_sha256":sha256(candidate),
        "reference_skin_joint_count":len(rw["names"]),
        "candidate_skin_joint_count":len(cw["names"]),
        "added_skin_joint_names":sorted(set(cw["names"])-set(rw["names"])),
        "removed_skin_joint_names":sorted(set(rw["names"])-set(cw["names"])),
        "lost_previously_weighted_bones":lost_weighted,
        "newly_weighted_bones":new_weighted,
        "source_joint_parent_changes":hierarchy_changes,
        "protected_attribute_equality":attr_equal,
        "topology_indices_exact":indices_equal,
        "reference_max_weight_sum_error":float(reference_weight_error.max(initial=0)),
        "candidate_max_weight_sum_error":float(candidate_weight_error.max(initial=0)),
        "reference_unweighted_vertices":int(len(zero_reference)),
        "candidate_unweighted_vertices":int(len(zero_candidate)),
        "candidate_influence_count_max":int(cw["influence_count"].max(initial=0)),
        "candidate_influence_count_p95":float(np.percentile(cw["influence_count"],95)),
        "checks":checks,
        "pass":all(checks.values()),
        "note":(
            "This is a source-rig asset audit. It intentionally does not require 63 skin joints. "
            "Canonical mapping/palm/scapula plausibility must be validated through the current "
            "retarget runtime against hgpt_canonical_v3."
        ),
    }
    out=args.report.resolve() if args.report else ROOT/"reports"/f"phase_f_source_rig_audit_{candidate.stem}.json"
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    if not report["pass"]:raise SystemExit(1)

if __name__=="__main__":
    main()
