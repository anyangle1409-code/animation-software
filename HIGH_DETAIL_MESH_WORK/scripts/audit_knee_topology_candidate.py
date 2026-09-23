"""Spatial audit for medial-knee boundary topology in a candidate GLB.

This is an advisory topology metric intended for the knee-retopology task. It
counts open body-mesh boundary edges near the left/right V6 medial-knee seam
regions, so it remains useful even if vertex indices change.

Usage:
    python scripts/audit_knee_topology_candidate.py candidate.glb
"""

from __future__ import annotations

import argparse
import json
import struct
from collections import Counter
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
BASELINE=ROOT/"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.glb"
SEAM=ROOT/"reports"/"knee_seam_v5.json"
DTYPE={5121:"u1",5123:"<u2",5125:"<u4",5126:"<f4"}
COMP={"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4}

def load(path):
    data=path.read_bytes();n=struct.unpack_from("<I",data,12)[0]
    doc=json.loads(data[20:20+n]);off=20+n
    blen,btype=struct.unpack_from("<II",data,off)
    if btype != 0x004E4942: raise ValueError("Missing BIN chunk")
    return doc,data[off+8:off+8+blen]

def read(doc,binary,ai):
    a=doc["accessors"][ai];v=doc["bufferViews"][a["bufferView"]]
    dt=np.dtype(DTYPE[a["componentType"]]);cols=COMP[a["type"]]
    return np.ndarray((a["count"],cols),dt,buffer=binary,
      offset=v.get("byteOffset",0)+a.get("byteOffset",0),
      strides=(v.get("byteStride",dt.itemsize*cols),dt.itemsize)).copy()

def body(doc,binary):
    p=doc["meshes"][0]["primitives"][0]
    pos=read(doc,binary,p["attributes"]["POSITION"]).astype(float)
    tri=read(doc,binary,p["indices"]).reshape(-1,3).astype(int)
    return pos,tri

def boundary_edges(tri):
    counts=Counter(tuple(sorted((int(a),int(b)))) for f in tri for a,b in
      ((f[0],f[1]),(f[1],f[2]),(f[2],f[0])))
    return np.asarray([e for e,c in counts.items() if c==1],dtype=int)

def local_counts(pos,tri,centres,radius=.18):
    edges=boundary_edges(tri)
    if not len(edges):
        return {side:0 for side in centres}
    mids=(pos[edges[:,0]]+pos[edges[:,1]])*.5
    return {side:int(np.count_nonzero(np.linalg.norm(mids-centre,axis=1)<radius))
            for side,centre in centres.items()}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("candidate",type=Path)
    ap.add_argument("--radius",type=float,default=.18)
    args=ap.parse_args()

    bd,bb=load(BASELINE);bp,bt=body(bd,bb)
    seam=json.loads(SEAM.read_text())["knees"]
    centres={}
    for side in ("L","R"):
        ids=[i for path in seam[side]["paths"] for i in path]
        centres[side]=bp[np.asarray(ids,dtype=int)].mean(axis=0)

    cd,cb=load(args.candidate.resolve());cp,ct=body(cd,cb)
    before=local_counts(bp,bt,centres,args.radius)
    after=local_counts(cp,ct,centres,args.radius)
    result={
        "candidate":str(args.candidate),
        "radius_m":args.radius,
        "baseline_v6_local_boundary_edges":before,
        "candidate_local_boundary_edges":after,
        "delta":{side:after[side]-before[side] for side in ("L","R")},
        "candidate_vertices":int(len(cp)),
        "candidate_triangles":int(len(ct)),
        "note":"Lower local open-boundary counts are expected from a true connected knee retopology, but visual deformation and the full guards remain authoritative."
    }
    print(json.dumps(result,indent=2))
    out=ROOT/"reports"/f"knee_topology_{args.candidate.stem}.json"
    out.write_text(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
