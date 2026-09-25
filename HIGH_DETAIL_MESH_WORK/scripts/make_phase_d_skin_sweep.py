"""Generate verified skin/material-only variants from any accepted candidate pair.

Usage:
  python scripts/make_phase_d_skin_sweep.py --version v15a_deep_hand_rebuild
  python scripts/make_phase_d_skin_sweep.py --dressed path.glb --bare path_BARE.glb

Writes paired candidates under skin_material_trials/<source-stem>/ and a JSON report.
No source asset is overwritten.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import struct
from pathlib import Path
from collections import defaultdict

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MAGIC = 0x46546C67
JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942

DTYPE = {5120:"i1",5121:"u1",5122:"<i2",5123:"<u2",5125:"<u4",5126:"<f4"}
COMPONENTS = {"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4,"MAT4":16}
SKIN_LINEAR = np.asarray([0.5704, 0.3186, 0.2140], dtype=float)
ROUGHNESSES = (0.50, 0.58, 0.64)
RANGE = (0.86, 1.05)
TARGET = 0.12

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def load_glb(path):
    data=Path(path).read_bytes()
    if len(data)<28 or struct.unpack_from("<I",data,0)[0]!=MAGIC:
        raise ValueError(f"Not a GLB: {path}")
    version=struct.unpack_from("<I",data,4)[0]
    if version!=2: raise ValueError(f"Unsupported GLB version {version}")
    jlen,jtype=struct.unpack_from("<II",data,12)
    if jtype!=JSON_CHUNK: raise ValueError("Missing JSON chunk")
    doc=json.loads(data[20:20+jlen])
    off=20+jlen
    blen,btype=struct.unpack_from("<II",data,off)
    if btype!=BIN_CHUNK: raise ValueError("Missing BIN chunk")
    binary=bytearray(data[off+8:off+8+blen])
    return doc,binary

def accessor(doc,binary,ai):
    a=doc["accessors"][ai];v=doc["bufferViews"][a["bufferView"]]
    dt=np.dtype(DTYPE[a["componentType"]]);cols=COMPONENTS[a["type"]]
    stride=v.get("byteStride",dt.itemsize*cols)
    offset=v.get("byteOffset",0)+a.get("byteOffset",0)
    return np.ndarray((a["count"],cols),dt,buffer=binary,offset=offset,
                      strides=(stride,dt.itemsize))

def accessor_byte_mask(doc, ai, binary_len):
    a=doc["accessors"][ai];v=doc["bufferViews"][a["bufferView"]]
    dt=np.dtype(DTYPE[a["componentType"]]);cols=COMPONENTS[a["type"]]
    width=dt.itemsize*cols;stride=v.get("byteStride",width)
    start=v.get("byteOffset",0)+a.get("byteOffset",0)
    mask=np.zeros(binary_len,dtype=bool)
    for i in range(a["count"]):
        s=start+i*stride;mask[s:s+width]=True
    return mask

def write_glb(doc,binary,path):
    doc=copy.deepcopy(doc)
    doc["buffers"][0]["byteLength"]=len(binary)
    text=json.dumps(doc,separators=(",",":")).encode("utf-8")
    text+=b" "*((-len(text))%4)
    binary=bytes(binary)+b"\0"*((-len(binary))%4)
    total=28+len(text)+len(binary)
    out=(struct.pack("<III",MAGIC,2,total)
         +struct.pack("<II",len(text),JSON_CHUNK)+text
         +struct.pack("<II",len(binary),BIN_CHUNK)+binary)
    Path(path).write_bytes(out)

def body_primitive(doc):
    return doc["meshes"][0]["primitives"][0]

def position_key(p):
    return (float(p[0]),float(p[1]),float(p[2]))

def apply_skin(source, target, roughness):
    source=Path(source);target=Path(target)
    if target.exists(): raise SystemExit(f"Refusing to overwrite {target}")
    doc,binary=load_glb(source)
    original_doc=copy.deepcopy(doc)
    original_binary=bytes(binary)
    prim=body_primitive(doc)
    attrs=prim["attributes"]
    required=("POSITION","NORMAL","COLOR_0")
    missing=[x for x in required if x not in attrs]
    if missing: raise RuntimeError(f"{source.name}: body missing {missing}")

    pos=accessor(doc,binary,attrs["POSITION"])
    nor=accessor(doc,binary,attrs["NORMAL"])
    col=accessor(doc,binary,attrs["COLOR_0"])
    idx=accessor(doc,binary,prim["indices"]).reshape(-1)
    ca=doc["accessors"][attrs["COLOR_0"]]
    if ca["componentType"]!=5123 or ca["type"]!="VEC4" or not ca.get("normalized",False):
        raise RuntimeError(f"Unexpected COLOR_0 layout in {source.name}")

    groups=defaultdict(list)
    for i,p in enumerate(pos):
        groups[position_key(p)].append(i)

    neighbours=defaultdict(set)
    for t in range(0,len(idx),3):
        a,b,c=(int(idx[t]),int(idx[t+1]),int(idx[t+2]))
        ka,kb,kc=position_key(pos[a]),position_key(pos[b]),position_key(pos[c])
        neighbours[ka].update((kb,kc));neighbours[kb].update((ka,kc));neighbours[kc].update((ka,kb))

    raw={};magnitudes=[]
    for key,members in groups.items():
        v=members[0];near=neighbours.get(key)
        if not near:
            raw[key]=0.0;continue
        centroid=np.zeros(3,float);span=0.0
        for other in near:
            w=groups[other][0]
            centroid+=pos[w].astype(float)
            span+=float(np.linalg.norm(pos[w].astype(float)-pos[v].astype(float)))
        centroid/=len(near);span/=len(near)
        if span<=1e-15:
            raw[key]=0.0;continue
        h=float(np.dot(centroid-pos[v].astype(float),nor[v].astype(float))/span)
        raw[key]=h;magnitudes.append(abs(h))

    magnitudes.sort()
    p95=magnitudes[min(len(magnitudes)-1,int(len(magnitudes)*0.95))] if magnitudes else 1.0
    gain=TARGET/(p95 or 1.0)
    darkest,lightest=1.0,1.0
    for key,members in groups.items():
        shade=min(RANGE[1],max(RANGE[0],1.0-raw[key]*gain))
        darkest=min(darkest,shade);lightest=max(lightest,shade)
        rgb=np.rint(np.clip(SKIN_LINEAR*shade,0,1)*65535).astype(np.uint16)
        for v in members:
            col[v,0:3]=rgb
            col[v,3]=65535

    doc["materials"]=doc.get("materials") or []
    existing=next((i for i,m in enumerate(doc["materials"]) if m.get("name")=="HomeGymPT_Skin"),-1)
    material={
        "name":"HomeGymPT_Skin",
        "doubleSided":False,
        "pbrMetallicRoughness":{
            "baseColorFactor":[1,1,1,1],
            "metallicFactor":0,
            "roughnessFactor":float(roughness),
        },
    }
    if existing>=0:
        doc["materials"][existing]=material;prim["material"]=existing
    else:
        doc["materials"].append(material);prim["material"]=len(doc["materials"])-1

    # Binary safety: only COLOR_0 bytes may change.
    allowed=accessor_byte_mask(original_doc,attrs["COLOR_0"],len(binary))
    old=np.frombuffer(original_binary,dtype=np.uint8)
    new=np.frombuffer(bytes(binary),dtype=np.uint8)
    changed=np.flatnonzero(old!=new)
    outside=int(np.count_nonzero((old!=new)&~allowed))
    if outside:
        raise RuntimeError(f"{source.name}: {outside} non-COLOR_0 binary bytes changed")

    # JSON safety: geometry/rig/animation structures are protected. Materials
    # and only the body primitive material index are allowed to differ.
    protected=("nodes","skins","scenes","animations","accessors","bufferViews","buffers")
    changed_fields=[k for k in protected if original_doc.get(k)!=doc.get(k)]
    if changed_fields:
        raise RuntimeError(f"Protected GLB JSON changed: {changed_fields}")
    if len(original_doc.get("meshes",[]))!=len(doc.get("meshes",[])):
        raise RuntimeError("Mesh count changed")
    for mi,(a,b) in enumerate(zip(original_doc["meshes"],doc["meshes"])):
        aa=copy.deepcopy(a);bb=copy.deepcopy(b)
        if mi==0:
            aa["primitives"][0].pop("material",None)
            bb["primitives"][0].pop("material",None)
        if aa!=bb:
            raise RuntimeError(f"Mesh JSON changed outside body material assignment: mesh {mi}")

    target.parent.mkdir(parents=True,exist_ok=True)
    write_glb(doc,binary,target)
    return {
        "source":source.name,
        "target":target.name,
        "source_sha256":sha256(source),
        "target_sha256":sha256(target),
        "roughness":float(roughness),
        "metallic":0,
        "skin_linear":SKIN_LINEAR.tolist(),
        "curvature_p95":float(p95),
        "curvature_gain":float(gain),
        "shade_range":[float(darkest),float(lightest)],
        "body_vertices":int(len(pos)),
        "color_components_changed":int(len(changed)),
        "non_color_binary_bytes_changed":outside,
        "protected_json_unchanged":True,
    }

def color_bytes(path):
    doc,binary=load_glb(path);p=body_primitive(doc)
    return accessor(doc,binary,p["attributes"]["COLOR_0"]).copy().tobytes()

def main():
    ap=argparse.ArgumentParser()
    source=ap.add_mutually_exclusive_group(required=True)
    source.add_argument("--version")
    source.add_argument("--dressed",type=Path)
    ap.add_argument("--bare",type=Path)
    ap.add_argument("--roughness",type=float,nargs="*",default=list(ROUGHNESSES))
    args=ap.parse_args()

    if args.version:
        dressed=ROOT/f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{args.version}.glb"
        bare=ROOT/f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{args.version}_BARE.glb"
        tag=args.version
    else:
        dressed=args.dressed.resolve()
        if args.bare is None: raise SystemExit("--bare is required with --dressed")
        bare=args.bare.resolve();tag=dressed.stem

    for p in (dressed,bare):
        if not p.is_file(): raise SystemExit(f"Missing source candidate: {p}")

    outdir=ROOT/"skin_material_trials"/tag
    results=[]
    for roughness in args.roughness:
        if not 0<=roughness<=1: raise SystemExit(f"Invalid roughness {roughness}")
        code=f"r{int(round(roughness*100)):02d}"
        d=outdir/f"{dressed.stem}_SKIN_{code}.glb"
        b=outdir/f"{bare.stem}_SKIN_{code}.glb"
        dr=apply_skin(dressed,d,roughness)
        br=apply_skin(bare,b,roughness)
        equivalent=color_bytes(d)==color_bytes(b)
        if not equivalent:
            raise RuntimeError(f"Bare/dressed body COLOR_0 differs for roughness {roughness}")
        results.append({"roughness":roughness,"dressed":dr,"bare":br,"body_color_equivalent":True})

    report={
        "source_dressed":dressed.name,
        "source_bare":bare.name,
        "source_tag":tag,
        "variants":results,
        "scope":"skin material + body COLOR_0 only",
        "promotion":"none",
    }
    report_path=ROOT/"reports"/f"phase_d_skin_sweep_{tag}.json"
    report_path.parent.mkdir(parents=True,exist_ok=True)
    report_path.write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
