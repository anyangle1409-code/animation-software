"""Build a deterministic PRE-EDIT vertex declaration from strict P3B1 minimum-ratio regressions.

This is preparation only: it reads an ORIGINAL-v1 numpy dump plus a comparison JSON and writes a declaration JSON.
It never opens or edits a Blend.

The mask owns endpoints of the worst rest-mesh edges inside each requested pose/region whose posed/rest ratio
falls below the immutable P3B1 value by more than the comparator tolerance. The mask is mirror-closed and may
be dilated by a small number of topology rings. It is intended to make r83-style local weight restoration
auditable before any edit is attempted.

Example:
  python scripts/declare_original_v1_p3b1_minratio_zone.py dump.npz full_r81_comparison_vs_P3B1.json out.json \
    --targets press_top/arm pullup_hang/arm pullup_hang_rhythm/arm squat_bottom/arm squat_bottom/shoulder \
    --top-edges 8 --rings 1
"""
import argparse, hashlib, json
from pathlib import Path
import numpy as np

ap=argparse.ArgumentParser()
ap.add_argument("dump")
ap.add_argument("comparison")
ap.add_argument("out")
ap.add_argument("--targets", nargs="+", required=True, help="pose/region pairs")
ap.add_argument("--top-edges", type=int, default=8)
ap.add_argument("--rings", type=int, default=1)
a=ap.parse_args()

d=np.load(a.dump)
rest, E = d["rest"], d["edges"]
regions=np.asarray(d["region"])
region_names=[str(x) for x in d["region_names"]]
poses=[str(x) for x in d["poses"]]
evaluated=d["evaluated"]
cmp=json.loads(Path(a.comparison).read_text(encoding="utf-8-sig"))
tol=float(cmp["comparison_tolerances"]["region_min_ratio_drop"])
regrows={(x["name"],x["region"]):x for x in cmp["regressions"] if x["metric"]=="region_min_ratio"}

L0=np.linalg.norm(rest[E[:,0]]-rest[E[:,1]],axis=1)
if (L0<=1e-12).any(): raise SystemExit("zero-length rest edge")
key={tuple(np.round(rest[i],5)):i for i in range(len(rest))}
mirror=np.array([key[tuple(np.round(rest[i]*[-1,1,1],5))] for i in range(len(rest))])

owned=set(); evidence=[]
for item in a.targets:
    pose, region=item.split("/",1)
    row=regrows.get((pose,region))
    if row is None: raise SystemExit(f"target is not a region_min_ratio regression: {item}")
    p=poses.index(pose); rid=region_names.index(region)
    P=evaluated[p]
    ratio=np.linalg.norm(P[E[:,0]]-P[E[:,1]],axis=1)/L0
    # Match the project comparator exactly: by_region assigns an edge from its first endpoint.\n    emask=(regions[E[:,0]]==rid)
    ids=np.nonzero(emask)[0]
    ids=ids[np.argsort(ratio[ids])[:a.top_edges]]
    threshold=float(row["baseline"])-tol
    selected=[int(k) for k in ids if ratio[k] < threshold]
    for k in selected:
        owned.update((int(E[k,0]),int(E[k,1])))
    evidence.append({"target":item,"baseline":float(row["baseline"]),"candidate":float(row["candidate"]),
                     "comparator_threshold":threshold,
                     "edges":[{"edge_index":k,"vertices":[int(E[k,0]),int(E[k,1])],"ratio":float(ratio[k])} for k in selected]})

zone=np.zeros(len(rest),bool); zone[list(owned)]=True; zone[mirror[zone]]=True
seed=zone.copy()
for _ in range(a.rings):
    nxt=zone.copy()
    nxt[E[zone[E[:,0]],1]]=True; nxt[E[zone[E[:,1]],0]]=True
    zone=nxt
zone[mirror[zone]]=True
left=[int(v) for v in np.nonzero(zone & (rest[:,0]<-1e-8))[0]]
mid=[int(v) for v in np.nonzero(zone & (np.abs(rest[:,0])<=1e-8))[0]]
right=[int(v) for v in np.nonzero(zone & (rest[:,0]>1e-8))[0]]
rec={"schema_version":1,"purpose":"r83 pre-edit local anti-collapse/restoration declaration",
     "source_dump":Path(a.dump).name,"source_dump_sha256":hashlib.sha256(Path(a.dump).read_bytes()).hexdigest(),
     "comparison":Path(a.comparison).name,"comparison_sha256":hashlib.sha256(Path(a.comparison).read_bytes()).hexdigest(),
     "targets":a.targets,"top_edges":a.top_edges,"rings":a.rings,"seed_vertices":int(seed.sum()),"zone_vertices":int(zone.sum()),
     "left_owned_vertex_ids":left,"midline_vertex_ids":mid,"mirror_of_strict_left_vertex_ids":right,
     "evidence":evidence,
     "boundary":"Declaration only. No model/weights/corrective/baseline/gate is changed; IDs are permitted inspection/edit scope, not proof that an edit is required."}
Path(a.out).write_text(json.dumps(rec,indent=2)+"\n",encoding="utf-8")
print("DECLARED",json.dumps({"targets":len(a.targets),"seed_vertices":int(seed.sum()),"zone_vertices":int(zone.sum())}))
