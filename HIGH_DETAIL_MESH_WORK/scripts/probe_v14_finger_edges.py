"""Read-only probe for safe local finger-shaft edge refinement."""
import bpy, bmesh, json, struct
import numpy as np
from pathlib import Path

root=Path(__file__).resolve().parents[1]
raw=(root/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb').read_bytes()
n=struct.unpack_from('<I',raw,12)[0]
doc=json.loads(raw[20:20+n]); base=28+n
a=doc['accessors'][doc['meshes'][0]['primitives'][0]['indices']]
view=doc['bufferViews'][a['bufferView']]
indices=np.ndarray(a['count'],dtype=np.dtype({5125:'<u4',5123:'<u2'}[a['componentType']]),buffer=raw,offset=base+view.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,3)
protected_glb=set(json.loads((root/'reports/hand_contact_guard_v5.json').read_text())['original_vertex_ids'])
bpy.ops.wm.open_mainfile(filepath=str(root/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.blend'))
v8=bpy.data.objects['Mike_Freeman'].data; mapping=[set() for _ in v8.vertices]
for i,p in enumerate(v8.polygons):
    for j,li in enumerate(p.loop_indices): mapping[v8.loops[li].vertex_index].add(int(indices[i,j]))
protected={i for i,ids in enumerate(mapping) if ids&protected_glb}
bpy.ops.wm.open_mainfile(filepath=str(root/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v13e_fingertip_retopology.blend'))
body=bpy.data.objects['Mike_Freeman']; bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table()
sid=bm.verts.layers.int['v8_source_id']; dlay=bm.verts.layers.deform.active
names={x.index:x.name for x in body.vertex_groups}
group_ids={side+'_'+digit:{gid for gid,name in names.items() if 'DEF-f_'+digit+'.' in name and name.endswith('.'+side)} for side in ('L','R') for digit in ('index','middle','ring','pinky')}
def owner(v):
    weights={key:sum(w for gid,w in v[dlay].items() if gid in ids) for key,ids in group_ids.items()}
    return max(weights,key=weights.get),max(weights.values())
counts={k:{'verts':0,'protected':0,'edges':0,'long2':0,'long3':0,'long4':0,'lengths':[]} for k in group_ids}
owners={}
for v in bm.verts:
    key,w=owner(v)
    if w<.65:continue
    owners[v]=key;counts[key]['verts']+=1
    if v[sid]>0 and v[sid]-1 in protected:counts[key]['protected']+=1
for e in bm.edges:
    a,b=e.verts
    if a not in owners or b not in owners or owners[a]!=owners[b] or e.is_boundary:continue
    if any(v[sid]>0 and v[sid]-1 in protected for v in e.verts):continue
    k=owners[a];d=e.calc_length()*1000
    counts[k]['edges']+=1;counts[k]['lengths'].append(d)
    for threshold,label in ((2,'long2'),(3,'long3'),(4,'long4')):
        if d>threshold:counts[k][label]+=1
for item in counts.values():
    lengths=item.pop('lengths')
    item['p50_mm']=round(float(np.percentile(lengths,50)),3) if lengths else None
    item['p90_mm']=round(float(np.percentile(lengths,90)),3) if lengths else None
print('V14_EDGE_PROBE',json.dumps(counts,indent=2),flush=True)
