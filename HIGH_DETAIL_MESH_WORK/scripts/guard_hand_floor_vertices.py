"""Audit protected push-up floor-contact vertices against reviewed V6.

This is a hand-work guard. It compares the protected original vertex IDs and
their first four skin influences against V6. It reports any position, joint or
weight change. Use --strict to return non-zero when protected data changed.

Usage:
    python scripts/guard_hand_floor_vertices.py candidate.glb
    python scripts/guard_hand_floor_vertices.py candidate.glb --strict
"""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.glb"
GUARD = ROOT / "reports" / "hand_contact_guard_v5.json"

DTYPE = {5120:"i1",5121:"u1",5122:"<i2",5123:"<u2",5125:"<u4",5126:"<f4"}
COMPONENTS = {"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4,"MAT4":16}

def load(path):
    data=path.read_bytes()
    if struct.unpack_from("<I",data,0)[0] != 0x46546C67:
        raise ValueError(f"Not a GLB: {path}")
    n=struct.unpack_from("<I",data,12)[0]
    doc=json.loads(data[20:20+n])
    off=20+n
    blen,btype=struct.unpack_from("<II",data,off)
    if btype != 0x004E4942:
        raise ValueError("Missing BIN chunk")
    return doc,data[off+8:off+8+blen]

def read(doc,binary,ai):
    a=doc["accessors"][ai];v=doc["bufferViews"][a["bufferView"]]
    dt=np.dtype(DTYPE[a["componentType"]]);cols=COMPONENTS[a["type"]]
    return np.ndarray((a["count"],cols),dt,buffer=binary,
        offset=v.get("byteOffset",0)+a.get("byteOffset",0),
        strides=(v.get("byteStride",dt.itemsize*cols),dt.itemsize)).copy()

def attrs(doc,binary):
    p=doc["meshes"][0]["primitives"][0]
    return {name:read(doc,binary,ai) for name,ai in p["attributes"].items()}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("candidate",type=Path)
    ap.add_argument("--strict",action="store_true")
    ap.add_argument("--tolerance-mm",type=float,default=0.001)
    args=ap.parse_args()

    ids=np.asarray(json.loads(GUARD.read_text())["original_vertex_ids"],dtype=int)
    bd,bb=load(BASELINE);cd,cb=load(args.candidate.resolve())
    ba=attrs(bd,bb);ca=attrs(cd,cb)
    needed=("POSITION","JOINTS_0","WEIGHTS_0")
    for name in needed:
        if name not in ca:
            raise SystemExit(f"Candidate missing {name}")
        if ids.max() >= len(ca[name]):
            raise SystemExit("Candidate no longer preserves the protected vertex index range")

    shift=np.linalg.norm(ca["POSITION"][ids].astype(float)-ba["POSITION"][ids].astype(float),axis=1)*1000
    joint_changed=np.any(ca["JOINTS_0"][ids] != ba["JOINTS_0"][ids],axis=1)
    weight_delta=np.max(np.abs(ca["WEIGHTS_0"][ids].astype(float)-ba["WEIGHTS_0"][ids].astype(float)),axis=1)

    report={
        "candidate":str(args.candidate),
        "guard_vertices":int(len(ids)),
        "max_position_shift_mm":float(shift.max(initial=0)),
        "moved_over_tolerance":int(np.count_nonzero(shift > args.tolerance_mm)),
        "joint_rows_changed":int(np.count_nonzero(joint_changed)),
        "max_weight_delta":float(weight_delta.max(initial=0)),
        "weight_rows_changed":int(np.count_nonzero(weight_delta > 1e-7)),
        "tolerance_mm":args.tolerance_mm,
    }
    report["protected_floor_guard_unchanged"]=(
        report["moved_over_tolerance"]==0 and
        report["joint_rows_changed"]==0 and
        report["weight_rows_changed"]==0
    )
    print(json.dumps(report,indent=2))
    out=ROOT/"reports"/f"hand_floor_guard_{args.candidate.stem}.json"
    out.write_text(json.dumps(report,indent=2))
    if args.strict and not report["protected_floor_guard_unchanged"]:
        raise SystemExit(1)

if __name__=="__main__":
    main()
