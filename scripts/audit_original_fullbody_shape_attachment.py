"""Read-only native anchor comparison before PR80 shaped-guide attachment.

No scene deletion, pose/mesh/rig changes, retarget installation or fit operation.
Outputs geometric discrepancies, never chooses anatomy acceptance thresholds.
"""
import bpy,sys,json,hashlib,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import original_v1_functional_fullbody as bridge
src=Path(bpy.data.filepath)
assert hashlib.sha256(src.read_bytes()).hexdigest()=='670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56'
body=bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
runtime=bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
anatomy=bpy.data.objects['HGPT_ANATOMICAL_MASTER']
inv=bridge.validate_blender_bridge(anatomy,runtime,body)
assert not inv['errors'],inv['errors']
record=ROOT/'ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json'
rec=json.loads(record.read_text())
rows=[]
def endpoints(arm,name):
    b=arm.data.bones[name]
    return arm.matrix_world@b.head_local,arm.matrix_world@b.tail_local
for side,suffix in [('left','r'),('right','l')]:
    for part,target in [('clavicle','clavicle'),('scapula','scapula'),('humerus','upperarm')]:
        native=rec['bones'][part+'_'+side]
        h,t=Vector(native['head_m']),Vector(native['tail_m'])
        # PR72 pilot builder explicitly starts scapula control at AC.
        pilot_h=Vector(rec['bones']['clavicle_'+side]['tail_m']) if part=='scapula' else h
        ah,at=endpoints(anatomy,'anat_'+part+'_'+side)
        rh,rt=endpoints(runtime,target+'_'+suffix)
        rows.append({'anatomical_side':side,'part':part,'runtime_bone':target+'_'+suffix,
          'c004_record_head_m':list(h),'c004_pilot_head_m':list(pilot_h),'c004_tail_m':list(t),
          'a003_anatomical_head_m':list(ah),'a003_anatomical_tail_m':list(at),
          'runtime_head_m':list(rh),'runtime_tail_m':list(rt),
          'record_vs_anatomical_head_delta_mm':(h-ah).length*1000,
          'record_vs_anatomical_tail_delta_mm':(t-at).length*1000,
          'pilot_vs_runtime_head_delta_mm':(pilot_h-rh).length*1000,
          'pilot_vs_runtime_tail_delta_mm':(t-rt).length*1000,
          'pilot_vs_runtime_axis_angle_deg':math.degrees((t-pilot_h).angle(rt-rh)),
          'pilot_length_m':(t-pilot_h).length,'runtime_length_m':(rt-rh).length})
result={'source_model_commit':'2af63aedc3ff1c8c5de4974b4e826ec6ce26d81b',
 'source_model_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
 'shape_source_record':str(record.relative_to(ROOT)),
 'shape_source_record_sha256':hashlib.sha256(record.read_bytes()).hexdigest(),
 'native_blender':bpy.app.version_string,'coordinate_frame':'Original native Z-up; anatomical left +X; source lengths treated in recorded metres',
 'rows':rows,'automatic_attachment_allowed':False,'retarget_installed':False,
 'skeleton_changed':False,'mesh_changed':False,'anatomical_acceptance':False,
 'conclusion':'Different rest anchors/axes cannot be silently treated as one rig. Choose source authority and explicit bind/offset semantics before installing shaped-guide motion; never move source skeleton to old skin.',
 'many_to_one_limb_mappings':{k:v for k,v in bridge.MAJOR_BONE_MAPPING.items() if sum(x==v for x in bridge.MAJOR_BONE_MAPPING.values())>1}}
out=Path(sys.argv[sys.argv.index('--')+1]);out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(result,indent=2)+'\n')
for r in rows: print(r['anatomical_side'],r['part'],'head delta mm',round(r['pilot_vs_runtime_head_delta_mm'],3),'axis deg',round(r['pilot_vs_runtime_axis_angle_deg'],3))
print('READ_ONLY_ATTACHMENT_AUDIT_COMPLETE; no scene or canonical changes')
