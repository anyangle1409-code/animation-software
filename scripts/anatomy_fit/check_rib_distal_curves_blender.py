"""Synthetic bpy source-curve roundtrip, with no canonical skeleton or thorax pose."""
import argparse,hashlib,json,math
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--scratch-blend',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
source=ROOT/'ORIGINAL_V1_WORK/anatomy/rib_distal_source_mean_curves_v1.json'
d=json.loads(source.read_text());bpy.ops.wm.read_factory_settings(use_empty=True)
expected={}
for level,v in d['levels'].items():
 for side,sign in [('left',1),('right',-1)]:
  name=f'SOURCE_DISTAL_ONLY_rib_{level}_{side}'
  coords=[[sign*x/1000,y/1000,0.,1.] for x,y in v['points_mm']]
  data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D'
  spline=data.splines.new('POLY');spline.points.add(len(coords)-1)
  for point,co in zip(spline.points,coords):point.co=co
  obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
  obj['not_canonical']=True;obj['full_rib_reconstructed']=False;obj['costotransverse_joint_permitted']=v['costotransverse_joint_permitted']
  expected[name]=coords
bpy.ops.wm.save_as_mainfile(filepath=str(a.scratch_blend));bpy.ops.wm.open_mainfile(filepath=str(a.scratch_blend))
max_error=0.;mirror_error=0.
for name,coords in expected.items():
 obj=bpy.data.objects[name];actual=[list(pt.co) for pt in obj.data.splines[0].points]
 assert len(actual)==101 and obj['not_canonical'] and not obj['full_rib_reconstructed']
 for x,y in zip(actual,coords):max_error=max(max_error,max(abs(i-j) for i,j in zip(x,y)))
 level=int(name.split('_')[4]);assert bool(obj['costotransverse_joint_permitted'])==(level<=10)
for level in d['levels']:
 left=bpy.data.objects[f'SOURCE_DISTAL_ONLY_rib_{level}_left'].data.splines[0].points
 right=bpy.data.objects[f'SOURCE_DISTAL_ONLY_rib_{level}_right'].data.splines[0].points
 for l,r in zip(left,right):mirror_error=max(mirror_error,abs(l.co.x+r.co.x),abs(l.co.y-r.co.y),abs(l.co.z-r.co.z))
assert max_error<1e-7 and mirror_error<1e-7
report={'status':'VERIFIED_SYNTHETIC_DISTAL_CURVE_ROUNDTRIP_ONLY','blender_version':bpy.app.version_string,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'fixture_sha256':hashlib.sha256(a.scratch_blend.read_bytes()).hexdigest(),'curves':len(expected),'points_per_curve':101,'max_abs_coordinate_error_m':max_error,'bilateral_reflection_error_m':mirror_error,'floating_rib_costotransverse_exceptions_verified':True,'nonbone_curves_only':True,'full_ribs_constructed':False,'canonical_candidate_created':False,'completed_tracker_gates':[]}
a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
