"""Independent synthetic mesh check of analytic clearance, never anatomy."""
import argparse,hashlib,json,math
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--scratch-blend',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
if a.scratch_blend.exists() or a.out.exists():raise FileExistsError('fresh immutable fixture required')
bpy.ops.wm.read_factory_settings(use_empty=True)
expected={}
for label,gap,sx,sy in [('INTERSECTING',5.,.4,.4),('SEPARATED',6.,0.,0.),('TOUCHING',4.,.4,0.)]:
 for surface in ['upper','lower']:
  vertices=[]
  for i in range(128):
   theta=2*math.pi*i/128;x=10*math.cos(theta);y=10*math.sin(theta)
   z=gap+sx*x+sy*y if surface=='upper' else 0.
   vertices.append([x/1000,y/1000,z/1000])
  name=f'SYNTHETIC_NOT_ANATOMY_{label}_{surface}'
  mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],[list(range(128))]);mesh.update()
  o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);o['not_canonical']=True
  expected[name]=vertices
bpy.ops.wm.save_as_mainfile(filepath=str(a.scratch_blend));bpy.ops.wm.open_mainfile(filepath=str(a.scratch_blend))
error=0.;gaps={}
for name,vertices in expected.items():
 o=bpy.data.objects[name];assert o['not_canonical'] and len(o.data.vertices)==128
 error=max(error,max(abs(v.co[j]-point[j]) for v,point in zip(o.data.vertices,vertices) for j in range(3)))
for label in ['INTERSECTING','SEPARATED','TOUCHING']:
 upper=bpy.data.objects[f'SYNTHETIC_NOT_ANATOMY_{label}_upper'].data.vertices
 lower=bpy.data.objects[f'SYNTHETIC_NOT_ANATOMY_{label}_lower'].data.vertices
 gaps[label]=min((u.co.z-l.co.z)*1000 for u,l in zip(upper,lower))
assert abs(gaps['INTERSECTING']-(5-math.sqrt(32)))<1e-6
assert abs(gaps['SEPARATED']-6)<1e-6 and abs(gaps['TOUCHING'])<1e-6
assert error<1e-7
report={'status':'VERIFIED_SYNTHETIC_PLANAR_MESH_CLEARANCE_ONLY','blender_version':bpy.app.version_string,'fixture_sha256':hashlib.sha256(a.scratch_blend.read_bytes()).hexdigest(),'helper_meshes':6,'rim_points_per_mesh':128,'max_coordinate_error_m':error,'independent_mesh_minimum_projected_gap_mm':gaps,'centre_and_four_cardinal_points_miss_intersection':True,'canonical_candidate_created':False,'anatomical_endplate_geometry_created':False,'completed_gates':[]}
a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
