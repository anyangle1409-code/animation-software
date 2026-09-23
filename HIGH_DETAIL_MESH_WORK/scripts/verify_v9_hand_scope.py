"""Verify the V9 review GLB differs from accepted V8 only in hand positions/normals."""
from pathlib import Path
import hashlib,json
import numpy as np
from candidate_quick_check import load_glb,accessor,first_body_primitive

root=Path(__file__).resolve().parents[1]
base=root/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb'
candidate=root/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v9_hand_geometry_review.glb'
bd,bb=load_glb(base);cd,cb=load_glb(candidate)
assert bd==cd and len(bb)==len(cb)
p=first_body_primitive(bd)
a=p['attributes']
old=accessor(bd,bb,a['POSITION']).astype(float)
new=accessor(cd,cb,a['POSITION']).astype(float)
delta=np.linalg.norm(new-old,axis=1)
changed=np.flatnonzero(delta>1e-8)
names=[bd['nodes'][i].get('name','') for i in bd['skins'][0]['joints']]
joint=accessor(bd,bb,a['JOINTS_0']).astype(int)
weight=accessor(bd,bb,a['WEIGHTS_0']).astype(float)
hand_bones=np.asarray([any(term in name for term in ('hand','palm','thumb','f_')) for name in names])
hand_influence=(hand_bones[joint]*weight).sum(axis=1)
assert len(changed)>0 and np.all(hand_influence[changed]>.001)
protected=np.asarray(json.loads((root/'reports/hand_contact_guard_v5.json').read_text())['original_vertex_ids'])
assert np.all(delta[protected]==0)
assert np.all(old[delta==0]==new[delta==0])
assert np.array_equal(accessor(bd,bb,p['indices']),accessor(cd,cb,p['indices']))
for key,index in a.items():
    if key not in ('POSITION','NORMAL'):
        assert np.array_equal(accessor(bd,bb,index),accessor(cd,cb,index)),key
# The GLB JSON is exact, and no binary bytes outside the body POSITION/NORMAL
# bufferViews were touched. This covers the other mesh, inverse binds and images.
allowed=np.zeros(len(bb),dtype=bool)
for key in ('POSITION','NORMAL'):
    ai=a[key];acc=bd['accessors'][ai];v=bd['bufferViews'][acc['bufferView']]
    start=v.get('byteOffset',0)+acc.get('byteOffset',0)
    width=12;stride=v.get('byteStride',width)
    for i in range(acc['count']):allowed[start+i*stride:start+i*stride+width]=True
raw_old=np.frombuffer(bb,dtype=np.uint8);raw_new=np.frombuffer(cb,dtype=np.uint8)
assert np.array_equal(raw_old[~allowed],raw_new[~allowed])
report={
    'source_v8_sha256':hashlib.sha256(base.read_bytes()).hexdigest(),
    'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
    'changed_hand_vertices':int(len(changed)),
    'changed_non_hand_vertices':0,
    'protected_floor_vertices_unchanged':int(len(protected)),
    'max_rest_displacement_mm':float(delta.max()*1000),
    'glb_json_identical':True,
    'all_other_binary_bytes_identical':True,
    'uv_weight_index_and_inverse_bind_data_identical':True,
}
(root/'reports/verify_v9_hand_scope.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
