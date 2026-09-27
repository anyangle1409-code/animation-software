#!/usr/bin/env python3
"""Compare a clean-room GLB against legacy GLBs for suspicious geometry reuse.

Standard-library only. Reads GLB JSON/BIN chunks and POSITION/index accessors.
This is an engineering provenance guard, not a legal determination.

Usage:
  python scripts/audit_original_geometry_independence.py ORIGINAL.glb LEGACY1.glb [LEGACY2.glb ...]
"""
from __future__ import annotations
import hashlib
import json
import math
import struct
import sys
from pathlib import Path
from typing import Any

COMPONENT = {
    5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2),
    5125: ("I", 4), 5126: ("f", 4),
}
TYPE_N = {"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4,"MAT2":4,"MAT3":9,"MAT4":16}

def read_glb(path: Path):
    raw=path.read_bytes()
    if len(raw)<20 or raw[:4]!=b"glTF":
        raise ValueError(f"{path}: not a GLB")
    version,total=struct.unpack_from("<II",raw,4)
    if version!=2 or total!=len(raw):
        raise ValueError(f"{path}: unsupported/corrupt GLB")
    off=12; js=None; bins=[]
    while off+8<=len(raw):
        length,kind=struct.unpack_from("<II",raw,off); off+=8
        data=raw[off:off+length]; off+=length
        if kind==0x4E4F534A: js=json.loads(data.decode("utf-8").rstrip(" \t\r\n\0"))
        elif kind==0x004E4942: bins.append(data)
    if js is None: raise ValueError(f"{path}: missing JSON")
    return js,bins

def accessor_values(doc:dict[str,Any], bins:list[bytes], idx:int):
    a=doc["accessors"][idx]
    if "sparse" in a:
        raise ValueError("Sparse accessors not supported by provenance audit")
    view=doc["bufferViews"][a["bufferView"]]
    buf=bins[view.get("buffer",0)]
    fmt,size=COMPONENT[a["componentType"]]
    n=TYPE_N[a["type"]]
    stride=view.get("byteStride",n*size)
    start=view.get("byteOffset",0)+a.get("byteOffset",0)
    out=[]
    for i in range(a["count"]):
        vals=struct.unpack_from("<"+fmt*n,buf,start+i*stride)
        out.append(vals if n>1 else vals[0])
    return out

def mesh_fingerprint(path:Path):
    doc,bins=read_glb(path)
    position_sets=[]
    index_streams=[]
    counts=[]
    for mesh in doc.get("meshes",[]):
        for prim in mesh.get("primitives",[]):
            attrs=prim.get("attributes",{})
            if "POSITION" not in attrs: continue
            pos=accessor_values(doc,bins,attrs["POSITION"])
            # Quantise only for comparison diagnostics, not identity.
            q=[tuple(round(float(v),6) for v in p) for p in pos]
            position_sets.extend(q)
            idx=accessor_values(doc,bins,prim["indices"]) if "indices" in prim else list(range(len(pos)))
            index_streams.extend(int(x) for x in idx)
            counts.append((len(pos),len(idx)//3))
    exact_positions=hashlib.sha256(repr(position_sets).encode()).hexdigest()
    exact_indices=hashlib.sha256(repr(index_streams).encode()).hexdigest()
    return {
        "path":str(path),
        "positions":position_sets,
        "indices":index_streams,
        "primitive_counts":counts,
        "position_hash":exact_positions,
        "index_hash":exact_indices,
    }

def compare(a,b):
    aset=set(a["positions"]); bset=set(b["positions"])
    shared=len(aset & bset)
    denom=max(1,min(len(aset),len(bset)))
    exact_vertex_overlap=shared/denom
    same_position_hash=a["position_hash"]==b["position_hash"]
    same_index_hash=a["index_hash"]==b["index_hash"]
    same_counts=a["primitive_counts"]==b["primitive_counts"]
    # A strict warning threshold. Coincidental coordinates can exist around
    # origin/axes; high exact overlap is what is suspicious.
    suspicious=(same_position_hash or (exact_vertex_overlap>=0.25 and same_counts))
    return {
        "legacy":b["path"],
        "same_position_hash":same_position_hash,
        "same_index_hash":same_index_hash,
        "same_primitive_counts":same_counts,
        "exact_quantized_vertex_overlap_ratio":exact_vertex_overlap,
        "shared_unique_positions":shared,
        "suspicious_reuse":suspicious,
    }

def main():
    if len(sys.argv)<3:
        raise SystemExit("Usage: audit_original_geometry_independence.py ORIGINAL.glb LEGACY.glb [LEGACY...]")
    original=mesh_fingerprint(Path(sys.argv[1]))
    comparisons=[compare(original,mesh_fingerprint(Path(x))) for x in sys.argv[2:]]
    result={
        "original": {
            k:v for k,v in original.items() if k not in ("positions","indices")
        },
        "comparisons":comparisons,
        "pass":not any(x["suspicious_reuse"] for x in comparisons),
        "note":"Engineering no-copy guard only; provenance records remain required."
    }
    print(json.dumps(result,indent=2))
    Path("reports").mkdir(exist_ok=True)
    Path("reports/original_geometry_independence.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    raise SystemExit(0 if result["pass"] else 1)

if __name__=="__main__":
    main()
