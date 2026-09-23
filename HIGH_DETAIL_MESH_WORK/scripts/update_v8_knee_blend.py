"""Apply knee-only V7-to-V8 coordinates to a copied, welded V7 Blend."""
from pathlib import Path
import json, struct
import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree
import numpy as np

root=Path(__file__).resolve().parents[1]
version='v8_knee_anatomy'
blend=root/f'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.blend'
def points(path):
    data=path.read_bytes(); n=struct.unpack_from('<I',data,12)[0]
    doc=json.loads(data[20:20+n]); ai=doc['meshes'][0]['primitives'][0]['attributes']['POSITION']
    a=doc['accessors'][ai]; b=doc['bufferViews'][a['bufferView']]
    return np.ndarray((a['count'],3),'<f4',buffer=data,offset=28+n+b.get('byteOffset',0)+a.get('byteOffset',0),strides=(b.get('byteStride',12),4)).copy()
old=points(root/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v7_knee_retopology.glb')
new=points(root/f'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.glb')
bpy.ops.wm.open_mainfile(filepath=str(blend))
body=max((obj for obj in bpy.data.objects if obj.type=='MESH'),key=lambda obj:len(obj.data.vertices))
assert len(body.data.vertices)==33059
count=len(body.data.vertices); faces=len(body.data.polygons)
uv={x.name:len(x.data) for x in body.data.uv_layers}
tree=KDTree(len(old))
for i,p in enumerate(old):tree.insert(Vector((float(p[0]),float(-p[2]),float(p[1]))),i)
tree.balance()
max_distance=0.; moved=0
for v in body.data.vertices:
    _,index,distance=tree.find(v.co)
    max_distance=max(max_distance,distance)
    if distance>2e-5:raise RuntimeError(f'Unmatched V7 Blend vertex {v.index}: {distance}')
    d=new[index]-old[index]
    if np.linalg.norm(d)>1e-8:
        v.co+=Vector((float(d[0]),float(-d[2]),float(d[1])));moved+=1
body.data.update()
assert len(body.data.vertices)==count and len(body.data.polygons)==faces
assert {x.name:len(x.data) for x in body.data.uv_layers}==uv
body['knee_anatomy_note']='V8 local patella, medial notch and tendon shape pass; V7 welded topology retained.'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
report={'blend':blend.name,'vertices':count,'triangles':faces,'uv_loop_counts':uv,
        'moved_blend_vertices':moved,'max_v7_mapping_distance_mm':max_distance*1000,
        'v7_welded_topology_retained':True}
(root/f'reports/blend_topology_{version}.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
