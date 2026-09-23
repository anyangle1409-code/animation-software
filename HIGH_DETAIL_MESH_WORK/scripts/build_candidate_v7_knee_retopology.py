"""Build V7 knee geometry with protected V6 GLB metadata and UV islands.

The anatomical smoothing uses a temporarily connected adjacency. The GLB retains
the UV0 vertex split, while the editable Blend welds these pairs and keeps UVs
per face corner. This preserves the existing atlas without a stretched UV seam.
"""
from pathlib import Path
import gzip, json, struct, sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.glb'
version=sys.argv[1] if len(sys.argv)>1 else 'v7_knee_retopology_rebuild'
target=ROOT/f'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.glb'
data=bytearray(source.read_bytes()); n=struct.unpack_from('<I',data,12)[0]
doc=json.loads(data[20:20+n]); base=28+n; prim=doc['meshes'][0]['primitives'][0]
def view(ai):
    a=doc['accessors'][ai]; b=doc['bufferViews'][a['bufferView']]
    dt=np.dtype({5126:'<f4',5125:'<u4'}[a['componentType']]); cols={'VEC3':3,'SCALAR':1}[a['type']]
    return np.ndarray((a['count'],cols),dt,buffer=data,offset=base+b.get('byteOffset',0)+a.get('byteOffset',0),strides=(b.get('byteStride',dt.itemsize*cols),dt.itemsize))
pos=view(prim['attributes']['POSITION']); normals=view(prim['attributes']['NORMAL'])
original_faces=view(prim['indices']).reshape(-1,3).astype(int)
faces=original_faces.copy()
with gzip.open(ROOT/'reports/squat_sculpt_reference_v5.json.gz','rt',encoding='utf-8') as stream:
    ref=json.load(stream)
posed=np.asarray(ref['points']); inverse=np.asarray(ref['inverse']).reshape(-1,4,4).transpose(0,2,1)
assert len(pos)==len(posed)==33089

seams=json.loads((ROOT/'reports/knee_seam_v5.json').read_text())['knees']
pair_map={b:a for side in seams.values() for a,b in zip(*side['paths'])}
for old,new in pair_map.items():faces[faces==old]=new

# Smooth the welded medial fold as a connected surface, with outer vertices held.
centre=posed[32515]
distance=np.linalg.norm(posed-centre,axis=1)
radial=np.clip((.105-distance)/.065,0,1)
mask=radial*radial*(3-2*radial)
centre2=posed[31995]
distance2=np.linalg.norm(posed-centre2,axis=1)
radial2=np.clip((.060-distance2)/.045,0,1)
mask=np.maximum(mask,radial2*radial2*(3-2*radial2))
mask*=((pos[:,0]>.025)&(pos[:,0]<.28)&(pos[:,1]>.40)&(pos[:,1]<.68))
ids=np.flatnonzero(mask>0)
adj={int(i):set() for i in ids}
for a,b,c in faces:
    if a in adj:adj[a].update((int(b),int(c)))
    if b in adj:adj[b].update((int(a),int(c)))
    if c in adj:adj[c].update((int(a),int(b)))
work=posed.copy()
for iteration in range(18):
    old=work.copy()
    for i in ids:
        if len(adj[int(i)])>=3:
            lap=old[list(adj[int(i)])].mean(axis=0)-old[i]
            work[i]+=0.50*mask[i]*lap
world_delta=work-posed
rest_delta=np.einsum('nij,nj->ni',inverse[:,:3,:3],world_delta)

right_ids=np.flatnonzero((pos[:,0]<-.025)&(pos[:,0]>-.28)&(pos[:,1]>.40)&(pos[:,1]<.68))
right_pos=pos[right_ids].astype(float)
mirrored=0
for i in ids:
    target_rest=pos[i].astype(float)*np.array([-1,1,1])
    j=right_ids[np.argmin(np.linalg.norm(right_pos-target_rest,axis=1))]
    if np.linalg.norm(pos[j]-target_rest)<.0002:
        rest_delta[j]=rest_delta[i]*np.array([-1,1,1]);mirrored+=1
changed=np.flatnonzero(np.linalg.norm(rest_delta,axis=1)>1e-7)
pos[:]=(pos.astype(float)+rest_delta).astype(np.float32)
for old,new in pair_map.items():pos[old]=pos[new]

normal_seeds=np.unique(np.concatenate((changed,np.fromiter(pair_map.keys(),dtype=int))))
affected=np.unique(original_faces[np.any(np.isin(original_faces,normal_seeds),axis=1)].reshape(-1))
area=np.cross(pos[original_faces[:,1]]-pos[original_faces[:,0]],pos[original_faces[:,2]]-pos[original_faces[:,0]])
acc=np.zeros_like(pos,dtype=float)
for k in range(3):np.add.at(acc,original_faces[:,k],area)
length=np.linalg.norm(acc[affected],axis=1);valid=affected[length>1e-12]
normals[valid]=(acc[valid]/np.linalg.norm(acc[valid],axis=1)[:,None]).astype(np.float32)
for old,new in pair_map.items():
    vec=normals[old].astype(float)+normals[new].astype(float)
    vec/=max(np.linalg.norm(vec),1e-12)
    normals[old]=vec.astype(np.float32);normals[new]=vec.astype(np.float32)
target.write_bytes(data)
report={'source':source.name,'candidate':target.name,'moved_vertices':int(len(changed)),
        'mirrored_pairs':int(mirrored),'max_rest_move_mm':float(np.linalg.norm(rest_delta,axis=1).max()*1000),
        'uv0_and_uv1_unchanged':True,'rig_skin_animation_material_fields_unchanged':True,
        'glb_uv_split_pairs':len(pair_map),
        'note':'Editable Blend welds pairs as one topology; GLB duplicates vertices at UV0 island seam.'}
(ROOT/f'reports/build_{version}.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
