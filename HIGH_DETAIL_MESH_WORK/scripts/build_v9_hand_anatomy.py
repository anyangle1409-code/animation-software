"""Candidate-only hand surface sculpt from accepted V8 geometry.

The V8 rig/weights/UV/index data stay fixed. Original floor-contact vertices
stay fixed; a hand-specific review checks any intentional original-hand sculpt.
"""
from pathlib import Path
import json,struct,hashlib,sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
VERSION=sys.argv[1] if len(sys.argv)>1 else 'v9_hand_anatomy'
LAP_GAIN=float(sys.argv[2]) if len(sys.argv)>2 else 0.0
EDGE_FRACTION=float(sys.argv[3]) if len(sys.argv)>3 else .30
ALLOW_ORIGINAL=bool(int(sys.argv[4])) if len(sys.argv)>4 else True
SHAPE_GAIN=float(sys.argv[5]) if len(sys.argv)>5 else 1.0
source=ROOT/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb'
target=ROOT/f'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{VERSION}.glb'
if target.exists():raise SystemExit(f'Refusing overwrite: {target}')
data=bytearray(source.read_bytes());n=struct.unpack_from('<I',data,12)[0]
doc=json.loads(data[20:20+n]);base=28+n;prim=doc['meshes'][0]['primitives'][0]
def view(ai):
    a=doc['accessors'][ai];b=doc['bufferViews'][a['bufferView']]
    dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']])
    cols={'VEC3':3,'VEC4':4,'SCALAR':1,'MAT4':16}[a['type']]
    return np.ndarray((a['count'],cols),dt,buffer=data,offset=base+b.get('byteOffset',0)+a.get('byteOffset',0),strides=(b.get('byteStride',dt.itemsize*cols),dt.itemsize))
pos=view(prim['attributes']['POSITION']);normal=view(prim['attributes']['NORMAL'])
old=pos.copy().astype(float);faces=view(prim['indices']).reshape(-1,3).astype(int)
names=[doc['nodes'][i].get('name','') for i in doc['skins'][0]['joints']]
joints=view(prim['attributes']['JOINTS_0']);weights=view(prim['attributes']['WEIGHTS_0'])
idx=np.arange(len(old));new=idx>=10839
def influence(term,side=None):
    selected=np.array([term in name and (side is None or name.endswith('.'+side)) for name in names])
    return (selected[joints]*weights).sum(axis=1)
hand=np.zeros(len(old))
for word in ('hand','f_','thumb','palm'):hand+=influence(word)
hand=np.minimum(hand,1)
eligible=(new|ALLOW_ORIGINAL)&(hand>.001)
protected=np.zeros(len(old),dtype=bool)
protected[json.loads((ROOT/'reports/hand_contact_guard_v5.json').read_text())['original_vertex_ids']]=True
eligible[protected]=False

# Guard the original contact vertices and the lower hand surface. The
# existing push-up floor solution has at least an 8 mm margin from this patch.
floor=np.full(len(old),np.inf)
for label in ('bottom','peak'):
    p=np.asarray(json.loads((ROOT/f'reports/poses_v8_knee_anatomy/push_up_{label}_candidate.json').read_text())['meshes'][0]['positions'])
    for side in ('L','R'):
        sidehand=(old[:,0]>0 if side=='L' else old[:,0]<0)&(hand>.001)
        floor[sidehand]=np.minimum(floor[sidehand],p[sidehand,1]-p[sidehand,1].min())
def smooth(t):
    t=np.clip(t,0,1);return t*t*(3-2*t)
safety=smooth((floor-.008)/.012)
safety[~new]=smooth((floor[~new]-.025)/.015)
safety[~eligible]=0

# Optional adjacency smoothing. The reviewed V9 run sets LAP_GAIN to zero
# because smoothing produced visible slits in the inherited wrist surface.
adj=[set() for _ in old]
for a,b,c in faces:
    adj[a].update((int(b),int(c)))
    adj[b].update((int(a),int(c)))
    adj[c].update((int(a),int(b)))
lap=np.zeros_like(old)
for i in np.flatnonzero(eligible):
    if len(adj[i])>=3:lap[i]=old[list(adj[i])].mean(axis=0)-old[i]
lap_length=np.linalg.norm(lap,axis=1)
lap*=np.minimum(1,.002/np.maximum(lap_length,1e-12))[:,None]
delta=.25*LAP_GAIN*lap*safety[:,None]

# Skeleton positions are read-only dimensional guides for the existing hand
# rig. They are not moved and no new controls or weights are introduced.
invbind=view(doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
joint_pos=np.linalg.inv(invbind)[:,:3,3]
def gaussian(value,centre,sigma):return np.exp(-.5*((value-centre)/sigma)**2)
digit_counts={}
for side in ('L','R'):
    side_ids=np.flatnonzero(eligible&(old[:,0]>0 if side=='L' else old[:,0]<0))
    for digit in ('index','middle','ring','pinky','thumb'):
        key=('DEF-thumb.' if digit=='thumb' else f'DEF-f_{digit}.')
        bone_ids=[names.index(key+f'{k:02d}.'+side) for k in (1,2,3)]
        a,b,c=joint_pos[bone_ids]
        lead=(b-a)/np.linalg.norm(b-a);tail=(c-b)/np.linalg.norm(c-b)
        chain=np.asarray((a-.014*lead,a,b,c,c+.011*tail))
        starts=chain[:-1];ends=chain[1:]
        spans=np.linalg.norm(ends-starts,axis=1);cumulative=np.r_[0,np.cumsum(spans)]
        weight=influence('thumb' if digit=='thumb' else f'f_{digit}',side)[side_ids]
        chosen=side_ids[weight>.12]
        if not len(chosen):continue
        p=old[chosen];v=ends-starts
        t=np.clip(np.einsum('nkj,kj->nk',p[:,None,:]-starts,v)/np.maximum(spans**2,1e-12),0,1)
        closest=starts[None,:,:]+t[:,:,None]*v[None,:,:]
        dist=np.linalg.norm(p[:,None,:]-closest,axis=2)
        segment=np.argmin(dist,axis=1)
        nearest=closest[np.arange(len(chosen)),segment]
        arc=cumulative[segment]+t[np.arange(len(chosen)),segment]*spans[segment]
        radial=p-nearest;radius=np.linalg.norm(radial,axis=1)
        radial/=np.maximum(radius[:,None],1e-12)
        pip=cumulative[2];dip=cumulative[3]
        # Modest joint pads with a gradual distal taper.
        profile=(.00125*gaussian(arc,pip,.006)
                 +.00072*gaussian(arc,dip,.005)
                 -.00055*smooth((arc-pip-.004)/.045))
        falloff=smooth((.025-radius)/.012)
        strength=np.clip(weight[weight>.12],0,1)*falloff*safety[chosen]
        delta[chosen]+=SHAPE_GAIN*profile[:,None]*radial*strength[:,None]
        distal=smooth((arc-dip)/.015)
        delta[chosen]+=.00065*SHAPE_GAIN*distal[:,None]*tail[None,:]*strength[:,None]*gaussian(radius,0,.010)[:,None]
        digit_counts[f'{digit}_{side}']=int(np.count_nonzero(strength>.05))

# Candidate-side soft tissue definition around the thumb web, palm pads and
# wrist. The smooth fields fade at the floor-contact guard.
for side in ('L','R'):
    sign=1 if side=='L' else -1
    x=old[:,0]*sign;y=old[:,1];z=old[:,2]
    web=gaussian(x,.757,.022)*gaussian(y,1.190,.026)*gaussian(z,.192,.025)
    thenar=gaussian(x,.742,.032)*gaussian(y,1.193,.040)*gaussian(z,.145,.030)
    hypothenar=gaussian(x,.747,.034)*gaussian(y,1.202,.043)*gaussian(z,.065,.034)
    wrist=gaussian(x,.706,.037)*gaussian(y,1.196,.044)*gaussian(z,.111,.053)
    nrm=normal.astype(float)
    nrm/=np.maximum(np.linalg.norm(nrm,axis=1)[:,None],1e-12)
    field=SHAPE_GAIN*(.0014*web+.0009*thenar+.00065*hypothenar+.00045*wrist)
    side_mask=(old[:,0]*sign>0)&eligible
    delta[side_mask]+=nrm[side_mask]*field[side_mask,None]*safety[side_mask,None]
    delta[side_mask]+=.12*LAP_GAIN*lap[side_mask]*wrist[side_mask,None]*safety[side_mask,None]

# Exact mirrored sculpt where the inherited hand vertices have paired samples.
left=np.flatnonzero(eligible&(old[:,0]>0));right=np.flatnonzero(eligible&(old[:,0]<0))
right_pos=old[right];mirrored=0
for i in left:
    target_pos=old[i]*[-1,1,1]
    j=right[np.argmin(np.linalg.norm(right_pos-target_pos,axis=1))]
    if np.linalg.norm(old[j]-target_pos)<.0001:
        delta[j]=delta[i]*[-1,1,1];mirrored+=1
delta[~eligible]=0
length=np.linalg.norm(delta,axis=1)
min_edge=np.full(len(old),np.inf)
for k in range(3):
    a=faces[:,k];b=faces[:,(k+1)%3]
    edge_length=np.linalg.norm(old[a]-old[b],axis=1)
    np.minimum.at(min_edge,a,edge_length)
    np.minimum.at(min_edge,b,edge_length)
# Several inherited hand triangles are sub-millimetre slivers. Limit a new
# vertex's shift to a fraction of its shortest incident edge so the sculpt
# cannot fold those triangles around an untouched original corner.
cap=np.minimum(.003,EDGE_FRACTION*min_edge)
delta*=np.minimum(1,cap/np.maximum(length,1e-12))[:,None]
moved=np.flatnonzero(np.linalg.norm(delta,axis=1)>1e-8)
assert len(moved)>0
assert np.all(eligible[moved]) and np.all(floor[moved]>.008)
assert not np.any(protected[moved])
pos[:]=(old+delta).astype(np.float32)

area=np.cross(pos[faces[:,1]]-pos[faces[:,0]],pos[faces[:,2]]-pos[faces[:,0]])
base_area=np.cross(old[faces[:,1]]-old[faces[:,0]],old[faces[:,2]]-old[faces[:,0]])
original_length=np.linalg.norm(base_area,axis=1)
orientation=np.einsum('ij,ij->i',area,base_area)/np.maximum(np.linalg.norm(area,axis=1)*original_length,1e-14)
if np.min(orientation)<=.05:
    worst=np.argsort(orientation)[:12]
    print('ORIENTATION_DIAGNOSTIC',[(int(i),float(orientation[i]),faces[i].tolist(),
          np.round(old[faces[i]],5).tolist(),
          np.round(delta[faces[i]]*1000,2).tolist()) for i in worst],flush=True)
    raise AssertionError('Hand sculpt inverted a triangle')
affected=np.unique(faces[np.any(np.isin(faces,moved),axis=1)].reshape(-1))
acc=np.zeros_like(old)
for k in range(3):np.add.at(acc,faces[:,k],area)
valid=affected[np.linalg.norm(acc[affected],axis=1)>1e-12]
normal[valid]=(acc[valid]/np.linalg.norm(acc[valid],axis=1)[:,None]).astype(np.float32)
target.write_bytes(data)
report={'source':source.name,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'candidate':target.name,'changed_hand_vertices':len(moved),
        'changed_original_hand_vertices':int(np.count_nonzero(moved<10839)),
        'changed_added_hand_vertices':int(np.count_nonzero(moved>=10839)),
        'left_right_changed':[int(np.count_nonzero(old[moved,0]>0)),int(np.count_nonzero(old[moved,0]<0))],
        'mirrored_exact_pairs':mirrored,'max_rest_move_mm':float(np.linalg.norm(delta,axis=1).max()*1000),
        'minimum_floor_clearance_of_changed_vertices_mm':float(floor[moved].min()*1000),
        'digit_support':digit_counts,'lap_gain':LAP_GAIN,'edge_fraction':EDGE_FRACTION,
        'allow_original_hand_vertices':ALLOW_ORIGINAL,'shape_gain':SHAPE_GAIN,
        'minimum_triangle_orientation_cosine':float(np.min(orientation)),
        'unchanged':'protected floor-contact positions; non-hand positions; UVs, weights, indices, rig, animations, materials and mechanics'}
(ROOT/f'reports/build_{VERSION}.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
