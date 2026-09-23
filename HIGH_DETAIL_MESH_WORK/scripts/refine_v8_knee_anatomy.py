"""Small symmetric anatomical sculpt from accepted V7 knee topology."""
from pathlib import Path
import json, struct, hashlib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
VERSION = 'v8_knee_anatomy'
source = ROOT/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v7_knee_retopology.glb'
target = ROOT/f'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{VERSION}.glb'
if target.exists():
    raise SystemExit(f'Refusing overwrite: {target}')
data=bytearray(source.read_bytes()); n=struct.unpack_from('<I',data,12)[0]
doc=json.loads(data[20:20+n]); base=28+n; prim=doc['meshes'][0]['primitives'][0]
def view(ai):
    a=doc['accessors'][ai]; b=doc['bufferViews'][a['bufferView']]
    dt=np.dtype({5126:'<f4',5125:'<u4'}[a['componentType']])
    cols={'VEC3':3,'SCALAR':1}[a['type']]
    return np.ndarray((a['count'],cols),dt,buffer=data,offset=base+b.get('byteOffset',0)+a.get('byteOffset',0),strides=(b.get('byteStride',dt.itemsize*cols),dt.itemsize))
pos=view(prim['attributes']['POSITION']); normals=view(prim['attributes']['NORMAL'])
faces=view(prim['indices']).reshape(-1,3).astype(int)
oldpos=pos.copy()
posed=np.asarray(json.loads((ROOT/'reports/poses_v7_knee_retopology/air_squat_peak_candidate.json').read_text())['meshes'][0]['positions'],dtype=float)
with __import__('gzip').open(ROOT/'reports/squat_sculpt_reference_v5.json.gz','rt',encoding='utf-8') as f:
    reference=json.load(f)
inverse=np.asarray(reference['inverse']).reshape(-1,4,4).transpose(0,2,1)
assert len(pos)==len(posed)==33089
seams=json.loads((ROOT/'reports/knee_seam_v5.json').read_text())['knees']
pair_map={b:a for side in seams.values() for a,b in zip(*side['paths'])}
joined=faces.copy()
for b,a in pair_map.items(): joined[joined==b]=a

# Read the accepted V7 surface in the actual deepest-squat pose. The patch
# attenuates the rounded central dome, blends the small medial dimple, and
# leaves a modest taper towards the upper shin. All displacements are millimetric.
x,y,z=posed.T
def bump(value,centre,radius): return np.exp(-.5*((value-centre)/radius)**2)
front=np.clip((z-.105)/.050,0,1)
front=front*front*(3-2*front)
region=(oldpos[:,0]>.025)&(oldpos[:,0]<.28)&(oldpos[:,1]>.40)&(oldpos[:,1]<.68)
dome=bump(x,.185,.031)*bump(y,.397,.033)*front*region
medial=bump(x,.132,.019)*bump(y,.370,.020)*bump(z,.142,.042)*region
tendon=bump(x,.163,.021)*bump(y,.339,.016)*front*region

# Smooth just the medial pinching, using the connected V7 surface adjacency.
ids=np.flatnonzero(medial>1e-3)
adj={int(i):set() for i in ids}
for a,b,c in joined:
    if a in adj:adj[a].update((int(b),int(c)))
    if b in adj:adj[b].update((int(a),int(c)))
    if c in adj:adj[c].update((int(a),int(b)))
work=posed.copy()
for _ in range(4):
    previous=work.copy()
    for i in ids:
        if len(adj[int(i)])>=3:
            work[i]+=.24*medial[i]*(previous[list(adj[int(i)])].mean(axis=0)-previous[i])
posed_delta=work-posed
posed_delta[:,2]+=-.0055*dome+.0018*tendon
rest_delta=np.einsum('nij,nj->ni',inverse[:,:3,:3],posed_delta)

# Mirror the left-side rest sculpt to the right, preserving accepted symmetry.
left=np.flatnonzero(region)
right_ids=np.flatnonzero((oldpos[:,0]<-.025)&(oldpos[:,0]>-.28)&(oldpos[:,1]>.40)&(oldpos[:,1]<.68))
left_pos=oldpos[left].astype(float)
left_delta=rest_delta[left].copy()
matched=0
for j in right_ids:
    mirrored=oldpos[j].astype(float)*[-1,1,1]
    distance=np.linalg.norm(left_pos-mirrored,axis=1)
    nearest=np.argmin(distance)
    if distance[nearest]<.0002:
        value=left_delta[nearest]; matched+=1
    elif distance[nearest]<.018:
        near=np.argpartition(distance,12)[:12]
        weight=np.exp(-.5*(distance[near]/.012)**2)
        value=np.average(left_delta[near],axis=0,weights=weight)
    else:
        value=np.zeros(3)
    rest_delta[j]=value*[-1,1,1]
for duplicate,canonical in pair_map.items():
    rest_delta[duplicate]=rest_delta[canonical]
changed=np.flatnonzero(np.linalg.norm(rest_delta,axis=1)>1e-8)
pos[:]=(oldpos.astype(float)+rest_delta).astype(np.float32)
for duplicate,canonical in pair_map.items():pos[duplicate]=pos[canonical]

# Recompute only normals adjacent to the sculpt, with smooth UV border pairs.
affected=np.unique(faces[np.any(np.isin(faces,changed),axis=1)].reshape(-1))
area=np.cross(pos[faces[:,1]]-pos[faces[:,0]],pos[faces[:,2]]-pos[faces[:,0]])
acc=np.zeros_like(pos,dtype=float)
for k in range(3):np.add.at(acc,faces[:,k],area)
valid=affected[np.linalg.norm(acc[affected],axis=1)>1e-12]
normals[valid]=(acc[valid]/np.linalg.norm(acc[valid],axis=1)[:,None]).astype(np.float32)
for duplicate,canonical in pair_map.items():
    if duplicate in affected or canonical in affected:
        unit=normals[duplicate].astype(float)+normals[canonical].astype(float)
        unit/=max(np.linalg.norm(unit),1e-12)
        normals[duplicate]=unit.astype(np.float32);normals[canonical]=unit.astype(np.float32)

target.write_bytes(data)
report={'source':source.name,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'candidate':target.name,'changed_vertices':len(changed),'mirrored_pairs':matched,
        'max_rest_move_mm':float(np.linalg.norm(rest_delta,axis=1).max()*1000),
        'dome_peak_reduction_mm':5.5,'medial_smoothing_iterations':4,
        'tendon_peak_definition_mm':1.8,
        'unchanged':'indices, UVs, weights, rig, animations, material, equipment, all non-knee body positions'}
(ROOT/f'reports/build_{VERSION}.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
