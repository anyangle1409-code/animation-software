"""Candidate-only finger-body edge refinement with pinned floor contacts."""
from __future__ import annotations
import bpy,bmesh,json,struct,math
import numpy as np
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
VERSION='v14e_finger_body_trial'
SRC=ROOT/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v13e_fingertip_retopology.blend'
OUT=ROOT/f'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{VERSION}.blend'
REPORT=ROOT/f'reports/build_{VERSION}_blender.json'
assert SRC.is_file() and not OUT.exists()
raw=(ROOT/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb').read_bytes()
n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);base=28+n
a=doc['accessors'][doc['meshes'][0]['primitives'][0]['indices']];view=doc['bufferViews'][a['bufferView']]
indices=np.ndarray(a['count'],dtype=np.dtype({5125:'<u4',5123:'<u2'}[a['componentType']]),buffer=raw,offset=base+view.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,3)
protected_glb=set(json.loads((ROOT/'reports/hand_contact_guard_v5.json').read_text())['original_vertex_ids'])
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.blend'))
v8=bpy.data.objects['Mike_Freeman'].data;mapping=[set() for _ in v8.vertices]
for i,p in enumerate(v8.polygons):
    for j,li in enumerate(p.loop_indices):mapping[v8.loops[li].vertex_index].add(int(indices[i,j]))
protected_ids={i for i,ids in enumerate(mapping) if ids&protected_glb}
bpy.ops.wm.open_mainfile(filepath=str(SRC))
body=bpy.data.objects['Mike_Freeman'];mesh=body.data
bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table();bm.normal_update()
sid=bm.verts.layers.int['v8_source_id'];dlay=bm.verts.layers.deform.active
groups={x.index:x.name for x in body.vertex_groups}
keys={side+'_'+digit:{gid for gid,name in groups.items() if 'DEF-f_'+digit+'.' in name and name.endswith('.'+side)} for side in ('L','R') for digit in ('index','middle','ring','pinky')}
origin=bm.verts.layers.float_vector.new('v14_origin')
for v in bm.verts:v[origin]=v.co.copy()
def is_protected(v):return v[sid]>0 and v[sid]-1 in protected_ids
def owner(v):
    values={key:sum(w for gid,w in v[dlay].items() if gid in ids) for key,ids in keys.items()}
    key=max(values,key=values.get)
    return key,values[key]
owners={}
for v in bm.verts:
    key,w=owner(v)
    if w>.65:owners[v]=key
old_verts=set(bm.verts)
fixed={v for v in bm.verts if is_protected(v) or v.is_boundary}
# Keep a four-edge transition around exact contact points and patch seams.
distance={v:0 for v in fixed};front=fixed
for depth in range(1,5):
    nxt={e.other_vert(v) for v in front for e in v.link_edges if e.other_vert(v) not in distance}
    for v in nxt:distance[v]=depth
    front=nxt
edges=[];per_digit={key:0 for key in keys};filters={'all':0,'not_boundary':0,'a_owned':0,'both_owned':0,'same_owner':0,'owned':0,'away':0,'long':0,'height':0}
for e in bm.edges:
    a,b=e.verts
    filters['all']+=1
    if not e.is_boundary:filters['not_boundary']+=1
    if a in owners:filters['a_owned']+=1
    if a in owners and b in owners:filters['both_owned']+=1
    if a in owners and b in owners and owners[a]==owners[b]:filters['same_owner']+=1
    if e.is_boundary or a not in owners or b not in owners or owners[a]!=owners[b]:continue
    filters['owned']+=1
    if distance.get(a,5)<2 or distance.get(b,5)<2:continue
    filters['away']+=1
    length=e.calc_length()
    if length<.00305:continue
    filters['long']+=1
    # Distal caps were already refined in V13e. Exclude them from this pass.
    if (a.co.z+b.co.z)*.5<1.087:continue
    filters['height']+=1
    edges.append(e);per_digit[owners[a]]+=1
print('V14_EDGE_FILTERS',filters,flush=True)
assert edges,'No qualifying edges; inspect filter counts instead of saving a no-op candidate.'
before_verts=len(bm.verts);before_faces=len(bm.faces)
result=bmesh.ops.subdivide_edges(bm,edges=edges,cuts=1,use_grid_fill=True)
bm.verts.ensure_lookup_table();bm.normal_update()
new_verts=list(bm.verts[before_verts:])
print('V14_SPLIT',{'reported_new':len(new_verts),'actual_growth':len(bm.verts)-before_verts,'source_ids_before_zero':sum(v[sid]>0 for v in bm.verts)},flush=True)
assert len(new_verts)==len(bm.verts)-before_verts
for v in new_verts:v[sid]=0
assert sum(v[sid]>0 for v in bm.verts)==33059
# A light Taubin relaxation on the refined finger surface removes the planar
# midpoint kink without the volume loss or segmented bands of V10's sculpt.
# Existing vertices move only in the free digit interior; contact anchors,
# their transition rings and all patch borders remain at the source positions.
fixed={v for v in bm.verts if is_protected(v) or v.is_boundary}
distance={v:0 for v in fixed};front=fixed
for depth in range(1,5):
    nxt={e.other_vert(v) for v in front for e in v.link_edges if e.other_vert(v) not in distance}
    for v in nxt:distance[v]=depth
    front=nxt
active={v for v in bm.verts if v not in fixed and distance.get(v,5)>=2 and owner(v)[1]>.65}
max_step=.00060
for factor in (.42,-.435)*14:
    changes={}
    for v in active:
        neighbours=[e.other_vert(v).co for e in v.link_edges]
        if len(neighbours)<3:continue
        avg=sum(neighbours,Vector())/len(neighbours)
        shift=factor*(avg-v.co)
        if shift.length>max_step:shift.length=max_step
        target=v.co+shift
        source=Vector(v[origin])
        if (target-source).length>.0012:
            target=source+(target-source).normalized()*.0012
        changes[v]=target
    for v,p in changes.items():v.co=p
bm.normal_update()
assert sum(is_protected(v) for v in bm.verts)>0
protected_max=max((v.co-v[origin]).length for v in bm.verts if is_protected(v))
boundary_max=max((v.co-v[origin]).length for v in bm.verts if v.is_boundary)
outside_max=max(((v.co-v[origin]).length for v in bm.verts if owner(v)[1]<=.65),default=0.)
max_original_move=max((v.co-v[origin]).length for v in bm.verts)
assert protected_max<1e-9 and boundary_max<1e-9 and outside_max<1e-9
bm.verts.layers.float_vector.remove(origin)
bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3])
bm.normal_update();bm.to_mesh(mesh);bm.free();mesh.update()
body['v14_finger_note']='V13e source; local finger shaft refinement; protected floor and patch boundaries fixed.'
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
report={'source':SRC.name,'blend':OUT.name,'edges_subdivided':len(edges),'per_digit':per_digit,
        'new_vertices':len(new_verts),'faces_before':before_faces,'faces_after':len(mesh.polygons),
        'active_vertices':len(active),'max_original_move_mm':max_original_move*1000,
        'protected_max_move_mm':protected_max*1000,'boundary_max_move_mm':boundary_max*1000,
        'outside_digit_max_move_mm':outside_max*1000,'body_vertices':len(mesh.vertices),'body_faces':len(mesh.polygons)}
REPORT.parent.mkdir(parents=True,exist_ok=True);REPORT.write_text(json.dumps(report,indent=2))
print('V14_FINGER_BODY',json.dumps(report),flush=True)
