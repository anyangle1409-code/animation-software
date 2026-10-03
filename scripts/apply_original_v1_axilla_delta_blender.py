"""Apply a declared LOCAL incremental shoulder-corrective delta to an existing corrective candidate."""
from __future__ import annotations
import copy, hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
import bpy
import numpy as np

args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(args)!=5: raise SystemExit("Usage: ... -- <solution.npz> <declaration.json> <parent_runtime_spec.json> <new.blend> <new_runtime_spec.json>")
sol_path,decl_path,parent_spec_path,new_path,spec_path=map(Path,args)
for p in (new_path,spec_path):
    if p.exists(): raise SystemExit(f"Refusing to overwrite {p}")
src=Path(bpy.data.filepath)
src_sha=hashlib.sha256(src.read_bytes()).hexdigest()
decl=json.loads(decl_path.read_text(encoding="utf-8"))
parent_spec=json.loads(parent_spec_path.read_text(encoding="utf-8"))
sol=np.load(sol_path)
def scalar_str(x):
    a=np.asarray(x); return str(a.item()) if a.shape==() else str(x)
if decl.get("source_candidate_sha256")!=src_sha: raise SystemExit("declaration source SHA mismatch")
if scalar_str(sol["source_sha256"])!=src_sha: raise SystemExit("solution source SHA mismatch")
if parent_spec.get("candidate")!=src.name: raise SystemExit("parent runtime spec candidate mismatch")
verts=[int(v) for v in sol["vertices"]]
if verts!=[int(v) for v in decl.get("left_owned_vertex_ids",[])]: raise SystemExit("solution vertices differ from declaration")
D=np.asarray(sol["delta"],dtype=float)
if D.shape!=(len(verts),3) or not np.isfinite(D).all(): raise SystemExit("invalid delta")

rig=bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]; body=bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; me=body.data
if me.shape_keys is None: raise SystemExit("source has no corrective keys")
cfg=json.loads(bpy.context.scene.get("hgpt_shoulder_corrective","{}"))
basis=me.shape_keys.key_blocks.get("Basis"); kl=me.shape_keys.key_blocks.get(cfg.get("keys",{}).get("l","")); kr=me.shape_keys.key_blocks.get(cfg.get("keys",{}).get("r",""))
if basis is None or kl is None or kr is None: raise SystemExit("corrective keys/config incomplete")
rest=np.array([d.co[:] for d in basis.data],dtype=float); nV=len(rest)
key={tuple(np.round(rest[i],5)):i for i in range(nV)}
mir=np.array([key.get(tuple(np.round(rest[i]*[-1,1,1],5)),-1) for i in range(nV)],dtype=int)
if (mir<0).any(): raise SystemExit("mesh is not exactly mirror symmetric")
S=np.array([-1.0,1.0,1.0])
expected=sorted(int(mir[v]) for v in verts if rest[v,0]<-1e-8)
if sorted(int(v) for v in decl.get("mirror_of_strict_left_vertex_ids",[]))!=expected: raise SystemExit("declaration mirror mismatch")

parent_ids=[int(v) for v in parent_spec["left"]["vertex_ids"]]; parent_delta=np.asarray(parent_spec["left"]["delta_m"],dtype=float)
if parent_delta.shape!=(len(parent_ids),3) or len(set(parent_ids))!=len(parent_ids): raise SystemExit("invalid parent runtime spec")
pos={v:i for i,v in enumerate(parent_ids)}
if any(v not in pos for v in verts): raise SystemExit("local mask extends outside existing corrective mask")
left0=np.array([d.co[:] for d in kl.data],dtype=float); right0=np.array([d.co[:] for d in kr.data],dtype=float)
for v,i in pos.items():
    if np.max(np.abs((left0[v]-rest[v])-parent_delta[i]))>2e-6: raise SystemExit("parent runtime spec disagrees with existing left key")
before={kb.name:np.array([d.co[:] for d in kb.data],dtype=float) for kb in me.shape_keys.key_blocks}
weights0={v.index:sorted((g.group,round(g.weight,9)) for g in v.groups) for v in me.vertices}
polys0=[tuple(p.vertices) for p in me.polygons]
bones0=[(b.name,tuple(b.head_local),tuple(b.tail_local)) for b in rig.data.bones]

for k,v in enumerate(verts):
    kl.data[v].co=tuple(left0[v]+D[k])
    rv=int(mir[v]); kr.data[rv].co=tuple(right0[rv]+D[k]*S)

L=set(verts); R=set(int(mir[v]) for v in verts)
for kb in me.shape_keys.key_blocks:
    after=np.array([d.co[:] for d in kb.data],dtype=float); changed=set(int(i) for i in np.nonzero(np.max(np.abs(after-before[kb.name]),axis=1)>1e-12)[0])
    allowed=L if kb.name==kl.name else R if kb.name==kr.name else set()
    if not changed.issubset(allowed): raise SystemExit(f"shape-key edit escaped declaration: {kb.name}")
if weights0!={v.index:sorted((g.group,round(g.weight,9)) for g in v.groups) for v in me.vertices}: raise SystemExit("weights changed")
if polys0!=[tuple(p.vertices) for p in me.polygons]: raise SystemExit("topology changed")
if bones0!=[(b.name,tuple(b.head_local),tuple(b.tail_local)) for b in rig.data.bones]: raise SystemExit("bones changed")
if np.max(np.abs(np.array([d.co[:] for d in basis.data])-rest))>1e-12: raise SystemExit("Basis changed")

new_spec=copy.deepcopy(parent_spec); new_spec["generated_utc"]=datetime.now(timezone.utc).isoformat(); new_spec["candidate"]=new_path.name
new_spec["parent_candidate"]=src.name; new_spec["parent_candidate_sha256"]=src_sha; new_spec["incremental_declaration"]=decl_path.name
new_spec["incremental_solution_sha256"]=hashlib.sha256(sol_path.read_bytes()).hexdigest()
nd=parent_delta.copy()
for k,v in enumerate(verts): nd[pos[v]]+=D[k]
new_spec["left"]["delta_m"]=[[round(float(c),7) for c in row] for row in nd]
new_spec["local_increment"]={"left_owned_vertex_ids":verts,"max_abs_delta_m":round(float(np.abs(D).max()),7),"declaration_ids_sha256":decl.get("ids_sha256")}

bpy.context.scene["hgpt_candidate_revision"]=new_path.stem; bpy.context.scene["hgpt_candidate_parent_sha256"]=src_sha
bpy.ops.wm.save_as_mainfile(filepath=str(new_path),copy=True)
spec_path.write_text(json.dumps(new_spec)+"\n",encoding="utf-8")
manifest={"generated_utc":datetime.now(timezone.utc).isoformat(),"stage":"O4 candidate: local axilla-pit incremental corrective (not production)",
"source_candidate":src.name,"source_sha256":src_sha,"candidate":new_path.name,"candidate_sha256":hashlib.sha256(new_path.read_bytes()).hexdigest(),
"declaration":decl_path.name,"declaration_sha256":hashlib.sha256(decl_path.read_bytes()).hexdigest(),"solution":sol_path.name,
"solution_sha256":hashlib.sha256(sol_path.read_bytes()).hexdigest(),"parent_runtime_spec":parent_spec_path.name,
"parent_runtime_spec_sha256":hashlib.sha256(parent_spec_path.read_bytes()).hexdigest(),"runtime_spec":spec_path.name,
"runtime_spec_sha256":hashlib.sha256(spec_path.read_bytes()).hexdigest(),"left_owned_vertices":len(verts),
"max_incremental_delta_m":round(float(np.abs(D).max()),7),"incremental_corrective":True,"weights_changed":False,"topology_changed":False,
"bones_changed":False,"rest_geometry_changed":False,"production_approved":False}
new_path.with_suffix(".json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
print("AXILLA DELTA APPLIED",json.dumps({"candidate":manifest["candidate"],"candidate_sha256":manifest["candidate_sha256"],"left_owned_vertices":len(verts)}))
