"""Diagnostic only (not a candidate): in-memory skin-weight diffusion in the shoulder-top fold zone, measured on the
uncorrected coupled motion at 120/140/160 deg, then restored.  Run inside Blender with the a003 source blend open:

  blender --background ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend --python scripts/diagnose_shoulder_weight_diffusion_blender.py

Result recorded in docs/FUNCTIONAL_SHOULDER_COUPLED_CORRECTIVE_20261013.md: diffusion does not remove the 160 deg fold.
"""
import bpy, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/anatomy_fit')]
import build_functional_shoulder_correction_blender as C
import build_functional_shoulder_corrective_blender as K
res=C.build_corrected_scene(); body=res['body']; me=body.data
faces,inreg=C.region_faces(body)
C.apply_corrected_pose(res,0); V0,F=C._evaluated(body)
adj=K._adjacency(len(V0),F)
def metrics(tag):
    out=[]
    for a in (120,140,160):
        C.apply_corrected_pose(res,a); P=C._evaluated(body); m=C.deformation_metrics(body,(V0,F),P,faces)
        out.append((a,m['collapse_faces_ratio_lt_0_1'],m['self_intersecting_face_pairs_in_region'],round(m['body_volume_change_pct'],2),m['stretched_faces_ratio_gt_2']))
    C.apply_corrected_pose(res,0); print(tag,out,flush=True)
metrics('baseline')
names={g.index:g.name for g in body.vertex_groups}; idx={g.name:g.index for g in body.vertex_groups}
fold=[i for i,p in enumerate(V0) if inreg[i] and p.z>1.38 and 0.13<abs(p.x)<0.30]
print('fold verts',len(fold))
W=[{names[g.group]:g.weight for g in v.groups} for v in me.vertices]
for iters in (5,15):
    w=[dict(x) for x in W]
    fs=set(fold)
    for _ in range(iters):
        new={}
        for i in fold:
            acc={}
            for n in adj[i]+[i]:
                for k,val in w[n].items(): acc[k]=acc.get(k,0)+val
            tot=sum(acc.values()); new[i]={k:v/tot for k,v in acc.items()}
        for i,d in new.items(): w[i]=d
    # keep 4 largest, renormalise
    for i in fold:
        top=dict(sorted(w[i].items(),key=lambda kv:-kv[1])[:4]); t=sum(top.values()); w[i]={k:v/t for k,v in top.items()}
    for i in fold:
        v=me.vertices[i]
        for g in list(v.groups): body.vertex_groups[g.group].remove([i])
        for k,val in w[i].items(): body.vertex_groups[idx[k]].add([i],val,'REPLACE')
    bpy.context.view_layer.update()
    metrics(f'weight-diffusion x{iters}')
    for i in fold:   # restore
        v=me.vertices[i]
        for g in list(v.groups): body.vertex_groups[g.group].remove([i])
        for k,val in W[i].items(): body.vertex_groups[idx[k]].add([i],val,'REPLACE')
    bpy.context.view_layer.update()
metrics('restored')
