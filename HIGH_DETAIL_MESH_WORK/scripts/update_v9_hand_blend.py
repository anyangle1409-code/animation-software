"""Apply the candidate-only V8-to-V9 hand sculpt to the copied V8 Blender asset."""
from pathlib import Path
import json,struct,sys
import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree
import numpy as np

root=Path(__file__).resolve().parents[1]
version=sys.argv[sys.argv.index("--")+1] if "--" in sys.argv else 'v9_hand_geometry_review'
blend=root/f'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.blend'
def positions(path):
    data=path.read_bytes();n=struct.unpack_from('<I',data,12)[0]
    doc=json.loads(data[20:20+n]);ai=doc['meshes'][0]['primitives'][0]['attributes']['POSITION']
    a=doc['accessors'][ai];v=doc['bufferViews'][a['bufferView']]
    return np.ndarray((a['count'],3),'<f4',buffer=data,offset=28+n+v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',12),4)).copy()
old=positions(root/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb')
new=positions(root/f'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.glb')
bpy.ops.wm.open_mainfile(filepath=str(blend))
body=max((o for o in bpy.data.objects if o.type=='MESH'),key=lambda o:len(o.data.vertices))
assert len(body.data.vertices)==33059
before_faces=len(body.data.polygons)
before_uv={x.name:len(x.data) for x in body.data.uv_layers}
tree=KDTree(len(old))
for i,p in enumerate(old):tree.insert(Vector((float(p[0]),float(-p[2]),float(p[1]))),i)
tree.balance()
changed=0;max_distance=0.
for v in body.data.vertices:
    _,i,distance=tree.find(v.co)
    max_distance=max(max_distance,distance)
    if distance>2e-5:raise RuntimeError(f'Unmatched V8 vertex {v.index}: {distance}')
    d=new[i]-old[i]
    if np.linalg.norm(d)>1e-8:
        v.co+=Vector((float(d[0]),float(-d[2]),float(d[1])));changed+=1
body.data.update()
assert len(body.data.polygons)==before_faces
assert {x.name:len(x.data) for x in body.data.uv_layers}==before_uv
body['hand_anatomy_note']='V9 hand-surface anatomy sculpt; accepted V8 knee topology retained.'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
report={'blend':blend.name,'body_vertices':len(body.data.vertices),'body_triangles':before_faces,
        'uv_loop_counts':before_uv,'moved_blend_vertices':changed,
        'max_source_mapping_distance_mm':max_distance*1000,
        'v8_knee_topology_retained':True}
(root/f'reports/blend_topology_{version}.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
