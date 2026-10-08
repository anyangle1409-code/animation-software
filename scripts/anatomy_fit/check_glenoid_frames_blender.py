"""Immutable relative measured-rim helpers; no SC/AC/GH bone/joint candidate."""
import argparse,hashlib,json
from pathlib import Path
import bpy
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--scratch-blend',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
if a.scratch_blend.exists() or a.out.exists():raise FileExistsError('new immutable output required')
source=ROOT/'ORIGINAL_V1_WORK/anatomy/canonical_glenoid_rim_frame_v1.json';d=json.loads(source.read_text())
bpy.ops.wm.read_factory_settings(use_empty=True);expected={}
for side,f in d['bilateral_relative_frames'].items():
 if side not in ('left','right'):continue
 name='RELATIVE_RIM_NOT_GH_'+side;R=Matrix(f['axes_HGPT']);centre=Vector([x/1000 for x in f['rim_centroid_relative_mm']])
 o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o)
 o.matrix_world=R.to_4x4();o.location=centre;o['not_canonical']=True;o['not_GH_centre']=True
 expected[name]=(R,centre)
bpy.ops.wm.save_as_mainfile(filepath=str(a.scratch_blend));bpy.ops.wm.open_mainfile(filepath=str(a.scratch_blend))
error=0.;det_error=0.;position_error=0.
for name,(R,centre) in expected.items():
 o=bpy.data.objects[name];A=o.matrix_world.to_3x3()
 assert o['not_canonical'] and o['not_GH_centre']
 error=max(error,max(abs(A[i][j]-R[i][j]) for i in range(3) for j in range(3)));det_error=max(det_error,abs(A.determinant()-1));position_error=max(position_error,(o.location-centre).length)
left=bpy.data.objects['RELATIVE_RIM_NOT_GH_left'];right=bpy.data.objects['RELATIVE_RIM_NOT_GH_right']
L=left.matrix_world.to_3x3();R=right.matrix_world.to_3x3()
assert L.col[2].x>0 and R.col[2].x<0
mirror_error=max(abs(left.location.x+right.location.x),abs(left.location.y-right.location.y),abs(left.location.z-right.location.z))
assert max(error,det_error,position_error,mirror_error)<1e-6
report={'status':'VERIFIED_RELATIVE_RIM_FIXTURE_ONLY','blender_version':bpy.app.version_string,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'fixture_sha256':hashlib.sha256(a.scratch_blend.read_bytes()).hexdigest(),'frame_count':2,'max_matrix_error':error,'max_determinant_error':det_error,'max_position_error_m':position_error,'bilateral_centroid_error_m':mirror_error,'canonical_candidate_created':False,'GH_centres_defined':False,'absolute_thorax_pose_defined':False,'completed_gates':[]}
a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
