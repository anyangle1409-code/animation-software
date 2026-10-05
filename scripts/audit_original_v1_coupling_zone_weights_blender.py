"""Read-only generic shared-tissue weight ownership audit.

Never saves the Blend.

Usage:
  blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
    --python scripts/audit_original_v1_coupling_zone_weights_blender.py -- ^
    <declaration.json> <out.json>

The declaration names a coupling system, an exact candidate SHA, a vertex zone,
and two or more anatomical anchor groups (bone names). The audit reports:
  * normalized per-vertex total weight and influence count;
  * weight share of each anatomical anchor group;
  * residual weight outside all declared anchor groups;
  * strongest single-anchor dominance;
  * anchor-share jumps across mesh edges inside the zone;
  * top vertices/edges by ownership discontinuity.

This is diagnostic evidence, not anatomy acceptance. It does not infer that a
particular numeric distribution is "human"; it identifies where ownership is
concentrated or discontinuous so visual/motion evidence can target the actual
boundary.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np

args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(args)!=2:
    raise SystemExit("Usage: ... -- <declaration.json> <out.json>")
DECL_PATH=Path(args[0]).resolve()
OUT=Path(args[1]).resolve()
if OUT.exists():
    raise SystemExit(f"Refusing to overwrite {OUT}")

decl=json.loads(DECL_PATH.read_text(encoding="utf-8"))
candidate=Path(bpy.data.filepath)
if not candidate.is_file():
    raise SystemExit("candidate filepath missing")
candidate_sha=hashlib.sha256(candidate.read_bytes()).hexdigest()
if decl.get("candidate_sha256")!=candidate_sha:
    raise SystemExit("declaration candidate_sha256 does not match loaded Blend")
if not decl.get("coupling_system_id"):
    raise SystemExit("coupling_system_id missing")
ids=[int(x) for x in decl.get("vertex_ids") or []]
if not ids:
    raise SystemExit("vertex_ids empty")

rig=bpy.data.objects.get("HGPT_CANONICAL_V4_ORIGINAL")
if rig is None:
    raise SystemExit("HGPT_CANONICAL_V4_ORIGINAL rig missing")
body=next((o for o in bpy.data.objects if o.type=="MESH" and o.find_armature()==rig and "SHORTS" not in o.name.upper()),None)
if body is None:
    raise SystemExit("body mesh bound to canonical rig not found")
me=body.data
if min(ids)<0 or max(ids)>=len(me.vertices):
    raise SystemExit("declared vertex id outside body mesh")

bone_names=[b.name for b in rig.data.bones]
bone_set=set(bone_names)
vg_name={vg.index:vg.name for vg in body.vertex_groups}
anchor_groups=decl.get("anchor_groups") or []
if len(anchor_groups)<2:
    raise SystemExit("at least two anchor_groups are required")
anchor_names=[]
anchor_bones=[]
for row in anchor_groups:
    name=row.get("name")
    bones=row.get("bones") or []
    if not isinstance(name,str) or not name or not bones:
        raise SystemExit("every anchor group requires name and bones")
    unknown=set(bones)-bone_set
    if unknown:
        raise SystemExit(f"anchor group {name} contains unknown bones: {sorted(unknown)}")
    anchor_names.append(name)
    anchor_bones.append(set(bones))
if len(anchor_names)!=len(set(anchor_names)):
    raise SystemExit("duplicate anchor group name")

nV=len(me.vertices)
zone=np.zeros(nV,dtype=bool)
zone[ids]=True

# Sparse per-vertex group map avoids a large all-bone dense matrix.
rows=[]
for vid in ids:
    v=me.vertices[vid]
    weights={}
    total=0.0
    for g in v.groups:
        name=vg_name.get(g.group)
        if not name or name not in bone_set:
            continue
        w=float(g.weight)
        weights[name]=w
        total+=w
    group_share={}
    for name,bones in zip(anchor_names,anchor_bones):
        group_share[name]=sum(weights.get(b,0.0) for b in bones)
    declared=sum(group_share.values())
    residual=max(0.0,total-declared)
    strongest=max(group_share.items(),key=lambda kv:kv[1]) if group_share else ("",0.0)
    rows.append({
        "vertex_id":vid,
        "total_deform_weight":total,
        "deform_influence_count":sum(1 for w in weights.values() if w>1e-12),
        "anchor_share":group_share,
        "declared_anchor_total":declared,
        "residual_other_bone_weight":residual,
        "strongest_anchor":strongest[0],
        "strongest_anchor_weight":strongest[1],
        "rest_xyz_m":[float(c) for c in v.co],
    })

by_id={r["vertex_id"]:r for r in rows}
edge_rows=[]
for e in me.edges:
    a,b=map(int,e.vertices)
    if not (zone[a] and zone[b]):
        continue
    diffs={name:abs(by_id[a]["anchor_share"][name]-by_id[b]["anchor_share"][name]) for name in anchor_names}
    edge_rows.append({
        "edge":[a,b],
        "max_anchor_share_jump":max(diffs.values()) if diffs else 0.0,
        "anchor_share_jump":diffs,
    })

def pct(vals,q):
    return float(np.percentile(np.asarray(vals,dtype=float),q)) if vals else 0.0

summary_groups={}
for name in anchor_names:
    vals=[r["anchor_share"][name] for r in rows]
    summary_groups[name]={
        "mean":float(np.mean(vals)),
        "p05":pct(vals,5),
        "p50":pct(vals,50),
        "p95":pct(vals,95),
        "max":float(max(vals)),
        "n_over_0_90":sum(v>0.90 for v in vals),
        "n_over_0_98":sum(v>0.98 for v in vals),
    }
residual=[r["residual_other_bone_weight"] for r in rows]
total=[r["total_deform_weight"] for r in rows]
jumps=[r["max_anchor_share_jump"] for r in edge_rows]
top_vertices=sorted(rows,key=lambda r:(-r["strongest_anchor_weight"],r["vertex_id"]))[:30]
top_edges=sorted(edge_rows,key=lambda r:(-r["max_anchor_share_jump"],r["edge"]))[:40]

result={
    "schema_version":1,
    "status":"READ_ONLY_COUPLING_ZONE_WEIGHT_AUDIT",
    "candidate":candidate.name,
    "candidate_sha256":candidate_sha,
    "coupling_system_id":decl["coupling_system_id"],
    "declaration":DECL_PATH.name,
    "declaration_sha256":hashlib.sha256(DECL_PATH.read_bytes()).hexdigest(),
    "side":decl.get("side","unspecified"),
    "vertex_count":len(ids),
    "zone_edge_count":len(edge_rows),
    "anchor_groups":[{"name":n,"bones":sorted(b)} for n,b in zip(anchor_names,anchor_bones)],
    "anchor_weight_summary":summary_groups,
    "total_deform_weight":{
        "min":float(min(total)),"mean":float(np.mean(total)),"max":float(max(total)),
        "n_below_0_999":sum(v<0.999 for v in total),
        "n_above_1_001":sum(v>1.001 for v in total),
    },
    "residual_other_bone_weight":{
        "mean":float(np.mean(residual)),"p95":pct(residual,95),"max":float(max(residual))
    },
    "ownership_edge_jump":{
        "p50":pct(jumps,50),"p95":pct(jumps,95),"p99":pct(jumps,99),"max":float(max(jumps)) if jumps else 0.0
    },
    "top_strongest_anchor_vertices":top_vertices,
    "top_ownership_jump_edges":top_edges,
    "source_saved_or_modified":False,
    "interpretation_rule":"Report ownership concentration/discontinuity only. Human validity requires motion, visual and attachment evidence; no weight percentage alone is anatomy acceptance."
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print("COUPLING ZONE WEIGHT AUDIT WRITTEN",OUT)
