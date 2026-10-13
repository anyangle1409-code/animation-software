"""Read-only six-joint/source-control comparison; no poses or file writes."""
import bpy,hashlib,json,sys,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import original_shoulder_joint_authority as authority
from original_shoulder_bind_semantics import bind_offset
SOURCE_HASH='ca8e6824ae54e5778a04409e00d32ae13ac23d9fce95e1f6d8207abbef265ca7'
path=Path(bpy.data.filepath)
assert hashlib.sha256(path.read_bytes()).hexdigest()==SOURCE_HASH
record_path=ROOT/authority.RECORD
report=authority.extract(json.loads(record_path.read_text()))
arms=[o for o in bpy.data.objects if o.type=='ARMATURE' and len(o.data.bones)==6 and 'scapula_left' in o.data.bones]
assert len(arms)==1,[o.name for o in arms]
arm=arms[0]
for key,joint in report['joints'].items():
    control=arm.matrix_world@arm.data.bones[joint['authored_control']].matrix_local
    rows=[list(row) for row in control]
    centre=[joint['world_frame_row_major'][r][3] for r in range(3)]
    gap=math.dist(centre,list(control.translation))*1000
    assert gap<0.002,(key,gap)
    joint['joint_to_authored_control_origin_mm']=gap
    joint['authored_control_world_rest_row_major']=rows
    joint['joint_frame_to_control_rest_offset']=bind_offset(joint['world_frame_row_major'],rows)
    if key.startswith('AC'):
        side=key.split('_')[1]
        joint['ac_to_source_scapular_glenoid_head_mm']=1000*math.dist(centre,json.loads(record_path.read_text())['bones']['scapula_'+side]['head_m'])
assert hashlib.sha256(path.read_bytes()).hexdigest()==SOURCE_HASH
report.update(source_model_filename=path.name,source_model_sha256=SOURCE_HASH,
    source_record_sha256=hashlib.sha256(record_path.read_bytes()).hexdigest(),
    source_work_commit='27e2dbf4424b878d8312cf346624e495720bba0a',
    native_blender_version=bpy.app.version_string,authored_guide_armature=arm.name,
    source_file_unchanged=True,source_scene_saved=False,
    body_vertices=len(bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE'].data.vertices),
    findings='SC, AC and GH match their intended authored control origins. AC is not the scapular glenoid head. Marker orientation is distinct from bone control orientation; offsets are diagnostic, not approved physiology or an installed retarget.')
out=Path(sys.argv[sys.argv.index('--')+1]);out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2)+'\n')
print('SIX_JOINT_AUTHORITY',[(k,round(v['joint_to_authored_control_origin_mm'],6)) for k,v in report['joints'].items()])
