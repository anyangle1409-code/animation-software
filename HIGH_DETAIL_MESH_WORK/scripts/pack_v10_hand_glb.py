"""Transplant V10 Blender hand retopology into the accepted V8 GLB container.

All source nodes, skins, bind matrices, materials, shorts and metadata remain
as V8. Original body vertex records retain their IDs and all non-hand data.
Only a new body primitive's arrays and indices are selected in the output.
"""
from __future__ import annotations
import bpy,copy,hashlib,json,math,struct
from pathlib import Path
from collections import defaultdict
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb'
VERSION='v10_hand_retopology'
BLEND=ROOT/f'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{VERSION}.blend'
TARGET=ROOT/f'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{VERSION}.glb'
if TARGET.exists():raise SystemExit('Refusing to overwrite an existing V10 GLB')
data=SOURCE.read_bytes();n=struct.unpack_from('<I',data,12)[0]
doc=json.loads(data[20:20+n]);out=copy.deepcopy(doc)
binary=bytearray(data[28+n:])
assert doc['meshes'][0]['primitives'][0].get('mode',4)==4
oldprim=doc['meshes'][0]['primitives'][0]
prim=out['meshes'][0]['primitives'][0]
DT={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}
COLS={'VEC2':2,'VEC3':3,'VEC4':4,'SCALAR':1}
def source_array(ai):
    a=doc['accessors'][ai];v=doc['bufferViews'][a['bufferView']]
    dt=np.dtype(DT[a['componentType']]);cols=COLS[a['type']]
    return np.ndarray((a['count'],cols),dt,buffer=binary,
                      offset=v.get('byteOffset',0)+a.get('byteOffset',0),
                      strides=(v.get('byteStride',dt.itemsize*cols),dt.itemsize)).copy()
old={name:source_array(ai) for name,ai in oldprim['attributes'].items()}
old_pos=old['POSITION'].astype(float)
old_uv0=old['TEXCOORD_0'].astype(float)
old_uv1=old['TEXCOORD_1'].astype(float)
oldfaces=source_array(oldprim['indices']).reshape(-1,3).astype(int)

# V8 Blender mesh triangle order is exactly the V8 GLB order (verified before
# this edit). Record every UV-split GLB variant of an original Blender vertex.
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.blend'))
v8=bpy.data.objects['Mike_Freeman'].data
assert len(v8.polygons)==len(oldfaces) and len(v8.vertices)==33059
variants=defaultdict(set)
for fi,poly in enumerate(v8.polygons):
    for corner,loop in enumerate(poly.loop_indices):
        vi=v8.loops[loop].vertex_index;gi=int(oldfaces[fi,corner])
        variants[vi].add(gi)
assert len(variants)==len(v8.vertices)

bpy.ops.wm.open_mainfile(filepath=str(BLEND))
body=bpy.data.objects['Mike_Freeman'];mesh=body.data
source_attr=mesh.attributes['v8_source_id']
source_ids=np.asarray([d.value-1 for d in source_attr.data])
assert len(source_ids)==len(mesh.vertices)
assert int(np.count_nonzero(source_ids>=0))==33059
assert len(set(source_ids[source_ids>=0]))==33059
assert all(len(p.vertices)==3 for p in mesh.polygons)

skin_names=[doc['nodes'][node].get('name','') for node in doc['skins'][0]['joints']]
joint_by_name={name:i for i,name in enumerate(skin_names)}
group_to_joint={g.index:joint_by_name[g.name] for g in body.vertex_groups if g.name in joint_by_name}
new_vertices=np.flatnonzero(source_ids<0)
old_tree=KDTree(len(old_pos))
for i,p in enumerate(old_pos):
    old_tree.insert(Vector((float(p[0]),float(p[1]),float(p[2]))),i)
old_tree.balance()

extra={name:[] for name in old}
position=old['POSITION'].copy()
normal=old['NORMAL'].copy()
converted={}
for v in mesh.vertices:
    sid=source_ids[v.index]
    if sid<0:continue
    p=np.asarray((v.co.x,v.co.z,-v.co.y),dtype=np.float32)
    nn=np.asarray((v.normal.x,v.normal.z,-v.normal.y),dtype=np.float32)
    nn/=max(float(np.linalg.norm(nn)),1e-12)
    for gi in variants[int(sid)]:
        if np.linalg.norm(p-old_pos[gi])>1e-8:
            position[gi]=p;normal[gi]=nn
        converted[gi]=True
assert len(converted)==len(old_pos)

def skin_record(v):
    totals=defaultdict(float)
    for g in v.groups:
        j=group_to_joint.get(g.group)
        if j is not None:totals[j]+=float(g.weight)
    ranked=sorted(totals.items(),key=lambda item:-item[1])
    if not ranked:raise AssertionError(f'Unweighted V10 vertex {v.index}')
    kept=ranked[:12];loss=sum(w for _,w in ranked[12:])
    total=sum(w for _,w in kept)
    pairs=kept+[(0,0.)]*(12-len(kept))
    return ([j for j,_ in pairs],[w/total for _,w in pairs],loss)

newmap={};max_weight_loss=0.;max_old_uv_error=0.
tri=[]
for poly in mesh.polygons:
    row=[]
    for loopid in poly.loop_indices:
        loop=mesh.loops[loopid];v=mesh.vertices[loop.vertex_index]
        uv0=mesh.uv_layers[0].data[loopid].uv
        uv1=mesh.uv_layers[1].data[loopid].uv
        u0=np.asarray((uv0.x,1.-uv0.y),dtype=np.float32)
        u1=np.asarray((uv1.x,1.-uv1.y),dtype=np.float32)
        sid=int(source_ids[v.index])
        if sid>=0:
            possibilities=list(variants[sid])
            gi=min(possibilities,key=lambda k:float(np.linalg.norm(old_uv0[k]-u0)+np.linalg.norm(old_uv1[k]-u1)))
            err=float(np.linalg.norm(old_uv0[gi]-u0)+np.linalg.norm(old_uv1[gi]-u1))
            max_old_uv_error=max(max_old_uv_error,err)
            if err>.0002:raise AssertionError(f'Original UV changed: {sid} {err}')
            row.append(gi);continue
        key=(v.index,tuple(np.round(u0,6)),tuple(np.round(u1,6)))
        if key not in newmap:
            gltfid=len(old_pos)+len(extra['POSITION'])
            newmap[key]=gltfid
            p=np.asarray((v.co.x,v.co.z,-v.co.y),dtype=np.float32)
            nn=np.asarray((v.normal.x,v.normal.z,-v.normal.y),dtype=np.float32)
            nn/=max(float(np.linalg.norm(nn)),1e-12)
            _,nearest,_=old_tree.find(Vector(p))
            joints,weights,loss=skin_record(v)
            max_weight_loss=max(max_weight_loss,loss)
            extra['POSITION'].append(p);extra['NORMAL'].append(nn)
            extra['TEXCOORD_0'].append(u0);extra['TEXCOORD_1'].append(u1)
            extra['COLOR_0'].append(old['COLOR_0'][nearest])
            for lane in range(3):
                extra[f'JOINTS_{lane}'].append(joints[lane*4:(lane+1)*4])
                extra[f'WEIGHTS_{lane}'].append(weights[lane*4:(lane+1)*4])
        row.append(newmap[key])
    assert len(row)==3 and len(set(row))==3
    tri.append(row)
assert max_weight_loss<.05,max_weight_loss
assert len(newmap)>=len(new_vertices)
assert len(tri)>len(oldfaces)

updated={}
for name,original in old.items():
    source_accessor=doc['accessors'][oldprim['attributes'][name]]
    dt=np.dtype(DT[source_accessor['componentType']])
    first=position if name=='POSITION' else normal if name=='NORMAL' else original
    appended=np.asarray(extra[name],dtype=dt).reshape(-1,original.shape[1])
    updated[name]=np.concatenate((first.astype(dt),appended),axis=0)
    assert len(updated[name])==len(old_pos)+len(newmap)

def append(arr,template,target):
    while len(binary)%4:binary.append(0)
    offset=len(binary);binary.extend(np.asarray(arr).tobytes())
    view={'buffer':0,'byteOffset':offset,'byteLength':int(np.asarray(arr).nbytes),'target':target}
    vi=len(out['bufferViews']);out['bufferViews'].append(view)
    a={k:v for k,v in template.items() if k not in ('bufferView','byteOffset','count','min','max')}
    a.update(bufferView=vi,count=len(arr))
    if 'min' in template:a['min']=np.min(arr,axis=0).tolist()
    if 'max' in template:a['max']=np.max(arr,axis=0).tolist()
    ai=len(out['accessors']);out['accessors'].append(a)
    return ai
for name,arr in updated.items():
    template=doc['accessors'][oldprim['attributes'][name]]
    prim['attributes'][name]=append(arr,template,34962)
index_template=doc['accessors'][oldprim['indices']]
indices=np.asarray(tri,dtype=np.uint32).reshape(-1,1)
prim['indices']=append(indices,index_template,34963)
out['buffers'][0]['byteLength']=len(binary)
text=json.dumps(out,separators=(',',':')).encode()
text+=b' '*((-len(text))%4)
binary.extend(b'\0'*(-len(binary)%4))
glb=(struct.pack('<III',0x46546C67,2,28+len(text)+len(binary))
     +struct.pack('<II',len(text),0x4E4F534A)+text
     +struct.pack('<II',len(binary),0x004E4942)+binary)
TARGET.write_bytes(glb)
report={
    'source_v8_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'candidate_sha256':hashlib.sha256(TARGET.read_bytes()).hexdigest(),
    'candidate':TARGET.name,'bytes':len(glb),
    'body_vertices':len(updated['POSITION']),'body_triangles':len(tri),
    'original_vertices_preserved_as_prefix':len(old_pos),
    'new_blender_vertices':len(new_vertices),'new_gltf_vertices':len(newmap),
    'new_vertex_max_lost_weight':max_weight_loss,
    'original_uv_mapping_max_error':max_old_uv_error,
    'nodes_skins_animations_materials_equal_v8':all(out.get(k)==doc.get(k) for k in
        ('nodes','skins','animations','materials','scenes','images','textures','samplers'))
}
(ROOT/'reports/build_v10_hand_glb.json').write_text(json.dumps(report,indent=2))
print('V10_HAND_GLB',json.dumps(report),flush=True)
