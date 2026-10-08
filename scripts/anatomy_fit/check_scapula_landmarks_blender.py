"""Run in a fresh bpy process; clears only its synthetic scene."""
import bpy,json,pathlib,hashlib,numpy as np
import argparse
parser=argparse.ArgumentParser(description='Synthetic measured-point roundtrip, never a canonical candidate')
parser.add_argument('--scratch-blend',type=pathlib.Path,required=True)
parser.add_argument('--out',type=pathlib.Path,required=True)
args=parser.parse_args()
root=pathlib.Path(__file__).resolve().parents[2]
p=root/'ORIGINAL_V1_WORK/anatomy/canonical_scapula_measured_landmark_model_v1.json'
d=json.loads(p.read_text()); template=d['relative_HGPT_landmarks_mm']
bpy.ops.wm.read_factory_settings(use_empty=True)
expected=np.array(template['right']+template['left'])/1000
mesh=bpy.data.meshes.new('PROVISIONAL_relative_scapula_points_NOT_CANONICAL')
mesh.from_pydata(expected.tolist(),[],[])
obj=bpy.data.objects.new(mesh.name,mesh);bpy.context.collection.objects.link(obj)
object_name=obj.name
blend=args.scratch_blend
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
bpy.ops.wm.open_mainfile(filepath=str(blend))
actual=np.array([list(v.co) for v in bpy.data.objects[object_name].data.vertices])
err=float(np.max(np.abs(actual-expected)))
assert len(actual)==58 and err<1e-7
assert np.allclose(actual[:29]*[-1,1,1],actual[29:],atol=1e-7)
report={'status':'VERIFIED_SYNTHETIC_MEASUREMENT_ROUNDTRIP_ONLY','blender_version':bpy.app.version_string,'source_report_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'points':58,'max_abs_coordinate_error_m':err,'bilateral_reflection_verified':True,'canonical_candidate_created':False,'gates_6_8_9_accepted':False,'note':'Sparse relative points at origin, no pose/translation or bone surface. No production or a003 assets opened or changed.'}
out=args.out
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
