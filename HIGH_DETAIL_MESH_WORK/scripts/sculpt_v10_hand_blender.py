"""Build V10 hand topology and anatomical sculpt in Blender from accepted V8.

The hand-only mesh edit is saved as an editable .blend. A separate packer reads
this scene to transplant the new body primitive into the V8 GLB document.
"""
from __future__ import annotations
import bpy,bmesh,json,math,struct
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree

ROOT=Path(__file__).resolve().parents[1]
VERSION='v10_hand_retopology'
SOURCE=ROOT/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb'
BLEND=ROOT/f'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{VERSION}.blend'
POSE_SOURCE=ROOT/'reports/poses_v10_hand_retopology/push_up_bottom_baseline.json'
CURL_POSE_SOURCE=ROOT/'reports/poses_v10_hand_retopology/dumbbell_bicep_curl_bottom_baseline.json'

data=SOURCE.read_bytes();n=struct.unpack_from('<I',data,12)[0]
doc=json.loads(data[20:20+n]);base=28+n;prim=doc['meshes'][0]['primitives'][0]
def view(ai):
    a=doc['accessors'][ai];v=doc['bufferViews'][a['bufferView']]
    dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']])
    cols={'VEC3':3,'VEC4':4,'SCALAR':1}[a['type']]
    return np.ndarray((a['count'],cols),dt,buffer=data,offset=base+v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',dt.itemsize*cols),dt.itemsize)).copy()
old_pos=view(prim['attributes']['POSITION'])
faces=view(prim['indices']).reshape(-1,3).astype(int)
protected_glb=set(json.loads((ROOT/'reports/hand_contact_guard_v5.json').read_text())['original_vertex_ids'])
posed=np.asarray(json.loads(POSE_SOURCE.read_text())['meshes'][0]['positions'],dtype=float)
curl_posed=np.asarray(json.loads(CURL_POSE_SOURCE.read_text())['meshes'][0]['positions'],dtype=float)
assert len(posed)>=len(old_pos)
names=[doc['nodes'][i].get('name','') for i in doc['skins'][0]['joints']]
joint=view(prim['attributes']['JOINTS_0']).astype(int)
weight=view(prim['attributes']['WEIGHTS_0']).astype(float)
hand_bones=np.asarray([any(s in name for s in ('hand','palm','thumb','f_')) for name in names])
hand_owner=(hand_bones[joint]*weight).sum(axis=1)
floor=np.full(len(old_pos),np.inf)
for sign in (1,-1):
    side=(old_pos[:,0]*sign>0)&(hand_owner>.001)
    floor[side]=posed[:len(old_pos),1][side]-posed[:len(old_pos),1][side].min()

bpy.ops.wm.open_mainfile(filepath=str(ROOT/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.blend'))
body=bpy.data.objects['Mike_Freeman'];mesh=body.data
assert len(mesh.polygons)==len(faces)==62961 and len(mesh.vertices)==33059
source_ids=[set() for _ in mesh.vertices]
for i,poly in enumerate(mesh.polygons):
    for corner,loopid in enumerate(poly.loop_indices):
        vi=mesh.loops[loopid].vertex_index;gi=int(faces[i,corner])
        v=mesh.vertices[vi].co;p=old_pos[gi]
        assert (Vector((v.x,v.z,-v.y))-Vector(p)).length<2e-5
        source_ids[vi].add(gi)
assert all(source_ids)
floor_vertex=np.asarray([min(floor[list(ids)]) for ids in source_ids])
protected_vertex=np.asarray([bool(ids&protected_glb) for ids in source_ids])

groups={g.index:g.name for g in body.vertex_groups}
hand_groups={i for i,n in groups.items() if any(s in n for s in ('DEF-hand.','DEF-palm.','DEF-thumb.','DEF-f_'))}
digit_groups={d:{i for i,n in groups.items() if ('DEF-thumb.' if d=='thumb' else 'DEF-f_'+d+'.') in n}
              for d in ('index','middle','ring','pinky','thumb')}
def influence(deform,selected):return sum(deform.get(i,0.) for i in selected)
def fade(v,a,b):
    t=max(0.,min(1.,(v-a)/(b-a)))
    return t*t*(3.-2.*t)
def gauss(v,mu,sigma):return math.exp(-.5*((v-mu)/sigma)**2)

bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table()
dlay=bm.verts.layers.deform.active
assert dlay is not None
idlay=bm.verts.layers.int.new('v8_source_id')
floorlay=bm.verts.layers.float.new('v8_floor_clearance')
restlay=bm.verts.layers.float_vector.new('v8_interpolated_rest')
posedlay=bm.verts.layers.float_vector.new('v8_interpolated_curl_pose')
original=list(bm.verts)
original_coords=[v.co.copy() for v in original]
source_tree=KDTree(len(original_coords))
for i,p in enumerate(original_coords):source_tree.insert(p,i)
source_tree.balance()
for i,v in enumerate(original):
    v[idlay]=i+1;v[floorlay]=float(floor_vertex[i]) if math.isfinite(floor_vertex[i]) else 1.
    v[restlay]=v.co.copy()
    gi=next(iter(source_ids[i]));q=curl_posed[gi]
    v[posedlay]=Vector((float(q[0]),-float(q[2]),float(q[1])))

def local_strength(v,margin=.016):
    hand=influence(v[dlay],hand_groups)
    p=v.co
    if abs(p.x)<.62 or p.z<1.06 or p.z>1.33:return 0.
    return min(1.,hand)*fade(v[floorlay],margin,margin+.025)*fade(abs(p.x),.63,.69)
def is_protected(v):
    sid=v[idlay]-1
    return sid>=0 and protected_vertex[sid]
def eligible(v):return not is_protected(v) and local_strength(v)>.08
def edge_length(e):return (e.verts[0].co-e.verts[1].co).length

before_verts=len(bm.verts);before_faces=len(bm.faces)
# Interior hand/wrist edges are split in Blender. Finger and thumb edges get a
# second local pass to add real joint/tip loops instead of merely moving old
# vertices. Protected floor vertices and their incident edges never split.
first=[e for e in bm.edges if all(eligible(v) for v in e.verts) and edge_length(e)>.0035]
result=bmesh.ops.subdivide_edges(bm,edges=first,cuts=1,use_grid_fill=True)
first_new=set(result.get('geom_inner',[]))
bm.verts.ensure_lookup_table()
second=[]
for e in bm.edges:
    if not all(eligible(v) for v in e.verts) or edge_length(e)<.0038:continue
    mid=(e.verts[0].co+e.verts[1].co)*.5
    digit=max(influence(e.verts[0][dlay],digit_groups[d])+
              influence(e.verts[1][dlay],digit_groups[d])
              for d in digit_groups)
    thumb_web=abs(mid.x)>.735 and mid.z>1.17 and mid.z<1.24 and mid.y<-.17
    if digit>.65 or thumb_web:second.append(e)
if second:bmesh.ops.subdivide_edges(bm,edges=second,cuts=1,use_grid_fill=True)
for v in bm.verts:
    _,sid,d=source_tree.find(v.co)
    if d<1e-6:
        saved=v[idlay]-1
        if not (0<=saved<before_verts and (original_coords[saved]-v.co).length<1e-6):
            saved=sid
        v[idlay]=saved+1
        v[floorlay]=float(floor_vertex[saved]) if math.isfinite(floor_vertex[saved]) else 1.
    else:
        v[idlay]=0
        nearest=source_tree.find_n(v.co,4)
        v[floorlay]=min(float(floor_vertex[i]) for _,i,_ in nearest)
bm.verts.ensure_lookup_table();bm.normal_update()
retopo_verts=len(bm.verts);retopo_faces=len(bm.faces)

# Constrained Taubin smoothing removes inherited faceted wrist/finger bands
# without shrinking the overall hand. It acts on the newly connected Blender
# topology and leaves every floor vertex fixed.
rest={v:v.co.copy() for v in bm.verts}
for coefficient in (.40,-.42,.32,-.34,.25,-.27):
    updates={}
    for v in bm.verts:
        s=local_strength(v,.018)
        if s<.02 or is_protected(v) or len(v.link_edges)<3:continue
        nb=[e.other_vert(v).co for e in v.link_edges]
        avg=sum(nb,Vector())/len(nb)
        shift=coefficient*s*(avg-v.co)
        if shift.length>.0018:shift.length=.0018
        updates[v]=v.co+shift
    for v,p in updates.items():v.co=p

# The frozen source has stepped dorsal wrist and squared distal phalanges.
# Relax those local loops after subdivision while the floor sole stays fixed.
for _ in range(2):
    updates={}
    for v in bm.verts:
        if is_protected(v) or len(v.link_edges)<3:continue
        finger=max(influence(v[dlay],digit_groups[d]) for d in digit_groups)
        wrist=gauss(abs(v.co.x),.704,.044)*gauss(v.co.z,1.206,.062)
        s=local_strength(v,.012)*max(min(1.,finger)*.85,wrist*.65)
        if s<.06:continue
        nb=[e.other_vert(v).co for e in v.link_edges]
        avg=sum(nb,Vector())/len(nb)
        shift=.22*s*(avg-v.co)
        if shift.length>.0008:shift.length=.0008
        updates[v]=v.co+shift
    for v,p in updates.items():v.co=p
bm.normal_update()

arm=bpy.data.objects['HomeGymPT_Male_Rig']
bones=arm.data.bones
def closest_chain(point,chain):
    distances=[];length=0.
    for a,b in zip(chain[:-1],chain[1:]):
        ab=b-a;seg=ab.length;t=max(0.,min(1.,(point-a).dot(ab)/(seg*seg)))
        q=a+t*ab;distances.append(((point-q).length,q,length+t*seg))
        length+=seg
    return min(distances,key=lambda x:x[0])

digit_changed=0
for side in ('L','R'):
    for digit in ('index','middle','ring','pinky','thumb'):
        prefix='DEF-thumb.' if digit=='thumb' else 'DEF-f_'+digit+'.'
        chain_bones=[bones[prefix+f'{i:02d}.'+side] for i in (1,2,3)]
        chain=[chain_bones[0].head_local.copy()]+[b.tail_local.copy() for b in chain_bones]
        seg=[(b-a).length for a,b in zip(chain[:-1],chain[1:])]
        pip=seg[0];dip=seg[0]+seg[1];end=sum(seg)
        tail_dir=(chain[-1]-chain[-2]).normalized()
        selected={i for i,n in groups.items() if prefix in n and n.endswith('.'+side)}
        for v in bm.verts:
            w=influence(v[dlay],selected)
            if w<.15 or is_protected(v):continue
            s=min(1.,w)*local_strength(v,.012)
            if s<.025:continue
            dist,q,arc=closest_chain(v.co,chain)
            if dist>.030:continue
            radial=v.co-q
            if radial.length<1e-8:continue
            radial.normalize()
            # Joint pads, narrower phalange shafts, distal taper and a domed
            # terminal cap. The cap uses added fingertip vertices from Blender.
            profile=(.0012*gauss(arc,pip,.010)
                     +.0008*gauss(arc,dip,.008)
                     -.0005*gauss(arc,(pip+dip)*.5,.011)
                     -.0015*fade(arc,end-.018,end-.002))
            cap=.0055*fade(arc,end-.018,end-.004)*max(0.,1.-(dist/.018)**2)
            v.co+=s*(profile*radial+cap*tail_dir)
            digit_changed+=1
bm.normal_update()

# Sculpt the thumb metacarpal, thenar/web, central palm arch and ulnar edge.
# Fields are mirrored, strongest away from the protected push-up sole.
palm_changed=0
for v in bm.verts:
    s=local_strength(v,.015)
    if s<.02 or is_protected(v):continue
    x=abs(v.co.x);y=v.co.y;z=v.co.z
    thenar=gauss(x,.749,.035)*gauss(y,-.145,.041)*gauss(z,1.196,.040)
    web=gauss(x,.759,.026)*gauss(y,-.191,.026)*gauss(z,1.197,.029)
    hypothenar=gauss(x,.745,.031)*gauss(y,-.069,.033)*gauss(z,1.188,.044)
    arch=gauss(x,.768,.044)*gauss(y,-.115,.062)*gauss(z,1.176,.046)
    wrist=gauss(x,.702,.026)*gauss(y,-.112,.055)*gauss(z,1.194,.057)
    height=(.004*thenar+.0026*web+.0032*hypothenar+.0022*arch+.0012*wrist)
    if height<.00001:continue
    v.co+=s*height*v.normal
    palm_changed+=1
bm.normal_update()

# Restore mirrored pairs to the same anatomy within Blender's float precision.
right=[v for v in bm.verts if v.co.x<-.62 and local_strength(v)>.02 and not is_protected(v)]
left=[v for v in bm.verts if v.co.x>.62 and local_strength(v)>.02 and not is_protected(v)]
tree=KDTree(len(right))
for i,v in enumerate(right):
    p=rest[v];tree.insert(Vector((-p.x,p.y,p.z)),i)
tree.balance();paired=0
for v in left:
    p=rest[v];_,ri,d=tree.find(p)
    if d>.00025:continue
    r=right[ri];avg=(v.co+Vector((-r.co.x,r.co.y,r.co.z)))*.5
    v.co=avg;r.co=Vector((-avg.x,avg.y,avg.z));paired+=1
bm.normal_update()

survivors=[v for v in bm.verts if v[idlay]>0]
assert len(survivors)==before_verts,(len(survivors),before_verts)
assert len({v[idlay] for v in survivors})==before_verts
for v in survivors:
    i=v[idlay]-1
    if protected_vertex[i]:
        assert (v.co-rest[v]).length<1e-7
protected_max=max((v.co-rest[v]).length for v in survivors if protected_vertex[v[idlay]-1])
nonhand_max=max((v.co-rest[v]).length for v in survivors if local_strength(v)==0)
assert protected_max<1e-9 and nonhand_max<1e-9

bmesh.ops.triangulate(bm,faces=list(bm.faces))
bm.normal_update();bm.to_mesh(mesh);bm.free();mesh.update()
assert len(mesh.polygons)>before_faces and len(mesh.vertices)>before_verts
source_attr=mesh.attributes.get('v8_source_id')
assert source_attr is not None and source_attr.domain=='POINT'
ids=[a.value for a in source_attr.data]
assert sum(x>0 for x in ids)==before_verts
body['hand_retopology_note']='V10 local Blender finger/thumb/palm/wrist retopology and sculpt from accepted V8; no rig edits.'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))

report={
    'source_v8':SOURCE.name,'blend':BLEND.name,
    'body_vertices_before':before_verts,'body_vertices_after':len(mesh.vertices),
    'body_faces_before':before_faces,'body_faces_after':len(mesh.polygons),
    'first_split_edges':len(first),'second_split_edges':len(second),
    'finger_sculpt_vertices':digit_changed,'palm_sculpt_vertices':palm_changed,
    'mirrored_pairs':paired,'protected_floor_vertices':int(protected_vertex.sum()),
    'protected_original_max_move_mm':protected_max*1000,
    'nonhand_original_max_move_mm':nonhand_max*1000
}
(ROOT/'reports/build_v10_hand_blender.json').write_text(json.dumps(report,indent=2))
print('V10_HAND_BLENDER',json.dumps(report),flush=True)
