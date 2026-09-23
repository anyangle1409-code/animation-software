"""Correct V10 added loops for interpolation across adjacent finger bones.

The Blender subdivision interpolates positions and weights separately. Linear
blend skinning of both interpolants introduces a quadratic cross-term in a
posed finger. The preserved V8 curl surface provides the posed target for each
subdivision vertex; the local sculpt offset is transformed through its own
weights, then solved back to the bind position. Original vertices are fixed.
"""
import bpy,json,numpy as np
from pathlib import Path

R=Path(__file__).resolve().parents[1]
P=R/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v10_hand_retopology.blend'
bpy.ops.wm.open_mainfile(filepath=str(P))
body=bpy.data.objects['Mike_Freeman'];mesh=body.data
ids=mesh.attributes['v8_source_id'].data
rest=mesh.attributes['v8_interpolated_rest'].data
posed=mesh.attributes['v8_interpolated_curl_pose'].data
ref=json.loads((R/'reports/v10_actual_curl_skin_matrices.json').read_text())
T=np.array(ref['matrices'],dtype=float).reshape(-1,4,4).transpose(0,2,1)
import struct
b=(R/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb').read_bytes()
n=struct.unpack_from('<I',b,12)[0];doc=json.loads(b[20:20+n])
names=[doc['nodes'][i].get('name','') for i in doc['skins'][0]['joints']]
assert [x.replace('.','') for x in names]==ref['boneNames']
joint_by_name={name:i for i,name in enumerate(names)}
group_to_joint={g.index:joint_by_name[g.name] for g in body.vertex_groups if g.name in joint_by_name}
def to_glb(v):return np.array((v[0],v[2],-v[1]),dtype=float)
def to_blender(v):return (float(v[0]),float(-v[2]),float(v[1]))

changes=[];residual=[]
for v in mesh.vertices:
    if ids[v.index].value>0:continue
    pairs=[(group_to_joint[g.group],float(g.weight)) for g in v.groups if g.group in group_to_joint and g.weight>0]
    assert pairs,(v.index,v.co[:])
    total=sum(w for _,w in pairs)
    M=sum(T[j]*(w/total) for j,w in pairs)
    initial=to_glb(rest[v.index].vector)
    target=to_glb(posed[v.index].vector)
    current=to_glb(v.co)
    desired=target+M[:3,:3]@(current-initial)
    before=M[:3,:3]@current+M[:3,3]
    corrected=np.linalg.solve(M[:3,:3],desired-M[:3,3])
    delta=np.linalg.norm(corrected-current)
    changes.append(delta)
    residual.append(np.linalg.norm(before-desired))
    v.co=to_blender(corrected)
mesh.update()
report={'added_vertices_corrected':len(changes),'median_rest_correction_mm':float(np.median(changes)*1000),
        'p95_rest_correction_mm':float(np.quantile(changes,.95)*1000),
        'max_rest_correction_mm':float(np.max(changes)*1000),
        'max_posed_interpolation_error_before_mm':float(np.max(residual)*1000),
        'original_vertices_unchanged':sum(x.value>0 for x in ids)}
assert report['original_vertices_unchanged']==33059
assert report['max_rest_correction_mm']<20,report
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(P))
(R/'reports/v10_hand_skin_interpolation.json').write_text(json.dumps(report,indent=2))
print('V10_SKIN_CORRECTION',json.dumps(report),flush=True)
