"""Create a local restoration solution inside a DECLARED r83 zone (numpy only; never touches a Blend).

For every declared vertex, blend CURRENT weights toward REFERENCE weights by alpha. Outside the declaration no
vertex is emitted/changed. The reference must have identical rest coordinates and bone columns. Output is compatible
with apply_original_v1_o4_weight_solution_blender.py. This is deliberately simpler than diffusion: r82 showed that
additional smoothing can remove intersections while worsening strict min-ratio regressions.

python scripts/restore_original_v1_weights_zone.py current_dump.npz reference_dump.npz declaration.json out.npz --alpha 0.25

REFERENCE is evidence, not automatically P3B1: callers must record what candidate/dump it represents and validate
the resulting candidate against P3B1, r81, development gates and r81 shoulder-intersection sentinels.
"""
import argparse, hashlib, json
from pathlib import Path
import numpy as np

ap=argparse.ArgumentParser()
ap.add_argument("current"); ap.add_argument("reference"); ap.add_argument("declaration"); ap.add_argument("out")
ap.add_argument("--alpha",type=float,required=True)
a=ap.parse_args()
if not (0.0 <= a.alpha <= 1.0): raise SystemExit("alpha must be in [0,1]")
cur=np.load(a.current); ref=np.load(a.reference)
for k in ("rest","W","bones"):
    if k not in cur or k not in ref: raise SystemExit(f"missing {k}")
if cur["rest"].shape!=ref["rest"].shape or np.max(np.abs(cur["rest"]-ref["rest"]))>1e-9:
    raise SystemExit("current/reference rest meshes differ")
bones=[str(x) for x in cur["bones"]]; rb=[str(x) for x in ref["bones"]]
if bones!=rb: raise SystemExit("current/reference bone columns differ")
W0=cur["W"]; WR=ref["W"]
decl=json.loads(Path(a.declaration).read_text(encoding="utf-8"))
ids=sorted(set(decl["left_owned_vertex_ids"]+decl.get("midline_vertex_ids",[])+decl["mirror_of_strict_left_vertex_ids"]))
Z=np.array(ids,dtype=np.int64)
if len(Z)==0: raise SystemExit("empty declaration")
if Z.min()<0 or Z.max()>=len(W0): raise SystemExit("declaration vertex out of range")
W=(1-a.alpha)*W0[Z]+a.alpha*WR[Z]
# exact top-4 + normalise
order=np.argsort(-W,axis=1); keep=np.zeros_like(W,bool); keep[np.arange(len(W))[:,None],order[:,:4]]=True
W=np.where(keep,W,0.0); sums=W.sum(1)
if (sums<=1e-12).any(): raise SystemExit("zero weight row")
W/=sums[:,None]; W[W<1e-6]=0; W/=W.sum(1)[:,None]
# enforce exact bilateral symmetry after blending/pruning
rest=cur["rest"]; key={tuple(np.round(rest[i],5)):i for i in range(len(rest))}
mir=np.array([key[tuple(np.round(rest[i]*[-1,1,1],5))] for i in range(len(rest))])
pos={v:i for i,v in enumerate(Z)}
swap=np.array([bones.index(n[:-2]+("_r" if n.endswith("_l") else "_l")) if n[-2:] in ("_l","_r") else bones.index(n) for n in bones])
for i,v in enumerate(Z):
    mv=int(mir[v])
    if mv not in pos: raise SystemExit("declaration is not mirror closed")
# average once from a copy to avoid order dependence
old=W.copy(); W=np.array([0.5*(old[i]+old[pos[int(mir[v])]][swap]) for i,v in enumerate(Z)])
order=np.argsort(-W,axis=1); keep=np.zeros_like(W,bool); keep[np.arange(len(W))[:,None],order[:,:4]]=True
W=np.where(keep,W,0.0); W/=W.sum(1)[:,None]
np.savez_compressed(a.out,vertices=Z,bones=np.array(bones),weights=W)
rec={"schema_version":1,"tool":"restore_original_v1_weights_zone.py","alpha":a.alpha,"zone_vertices":len(Z),
     "current":Path(a.current).name,"current_sha256":hashlib.sha256(Path(a.current).read_bytes()).hexdigest(),
     "reference":Path(a.reference).name,"reference_sha256":hashlib.sha256(Path(a.reference).read_bytes()).hexdigest(),
     "declaration":Path(a.declaration).name,"declaration_sha256":hashlib.sha256(Path(a.declaration).read_bytes()).hexdigest(),
     "max_weight_change":float(np.max(np.abs(W-W0[Z]))),"max_influences":int(np.max((W>1e-8).sum(1))),
     "boundary":"Research solution only. Applying it does not clear 3A or authorise Phase 4; full focused and 15-pose evidence is required."}
Path(a.out).with_suffix(".json").write_text(json.dumps(rec,indent=2)+"\n",encoding="utf-8")
print("RESTORATION SOLUTION",json.dumps(rec))
