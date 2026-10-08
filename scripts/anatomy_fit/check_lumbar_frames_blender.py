"""Local orientation fixture only: no absolute anatomical centres or candidate."""
import argparse,hashlib,json
from pathlib import Path
import bpy
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--scratch-blend',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
if a.scratch_blend.exists() or a.out.exists():raise FileExistsError('immutable new fixture/output required')
source=ROOT/'ORIGINAL_V1_WORK/anatomy/canonical_lumbar_body_disc_frames_p1.json'
d=json.loads(source.read_text());bpy.ops.wm.read_factory_settings(use_empty=True)
expected={}
for kind in ['superior_frames','inferior_frames']:
 for level,f in d['geometry'][kind].items():
  assert f['centre_m'] is None
  R=Matrix([f['left_axis'],f['AP_axis'],f['normal']]).transposed()
  name=f'LOCAL_ORIENTATION_ONLY_{level}_{kind}'
  o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o)
  o.matrix_world=R.to_4x4();o['not_canonical']=True;o['centre_unresolved']=True
  expected[name]=R
bpy.ops.wm.save_as_mainfile(filepath=str(a.scratch_blend));bpy.ops.wm.open_mainfile(filepath=str(a.scratch_blend))
error=0.;det_error=0.
for name,R in expected.items():
 o=bpy.data.objects[name];A=o.matrix_world.to_3x3()
 assert o['not_canonical'] and o['centre_unresolved']
 error=max(error,max(abs(A[i][j]-R[i][j]) for i in range(3) for j in range(3)))
 det_error=max(det_error,abs(A.determinant()-1))
 assert A.col[2].z>0 and A.col[0].x>0
assert error<1e-6 and det_error<1e-6
report={'status':'VERIFIED_LOCAL_ORIENTATION_FIXTURE_ONLY','blender_version':bpy.app.version_string,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'fixture_sha256':hashlib.sha256(a.scratch_blend.read_bytes()).hexdigest(),'frame_count':len(expected),'max_matrix_error':error,'max_determinant_error':det_error,'canonical_candidate_created':False,'absolute_centres_defined':False,'completed_gates':[]}
a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
