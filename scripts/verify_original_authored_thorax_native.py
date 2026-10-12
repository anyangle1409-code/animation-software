"""Reopen review scene and compare actual original immutable geometry/weights/rigs."""
import bpy, sys, json, hashlib
from pathlib import Path

def snapshot():
    body=bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
    return {'mesh': [list(v.co) for v in body.data.vertices],
        'weights': [[[g.group,g.weight] for g in v.groups] for v in body.data.vertices],
        'keys': {k.name:[list(v.co) for v in k.data] for k in body.data.shape_keys.key_blocks},
        'drivers': [(m.type, m.object.name if m.type=='ARMATURE' and m.object else None) for m in body.modifiers],
        'rigs': {name: {'world':[list(r) for r in bpy.data.objects[name].matrix_world],
            'rest':{b.name:[list(r) for r in b.matrix_local] for b in bpy.data.objects[name].data.bones}}
            for name in ('HGPT_ANATOMICAL_MASTER','HGPT_CANONICAL_V4_ORIGINAL')}}

args=sys.argv[sys.argv.index('--')+1:]
source,candidate,manifest=map(Path,args)
report=json.loads(manifest.read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest()==report['source_sha256']
assert hashlib.sha256(candidate.read_bytes()).hexdigest()==report['candidate_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));before=snapshot()
bpy.ops.wm.open_mainfile(filepath=str(candidate));after=snapshot()
assert before==after,'Original geometry/weights/shape keys/rig matrices or driver changed'
guides=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.get('hgpt_review_scope')]
assert len(guides)==43
assert len(bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE'].data.vertices)==17946
for name in ('HGPT_ANATOMICAL_MASTER','HGPT_CANONICAL_V4_ORIGINAL'):
    assert len(bpy.data.objects[name].data.bones)==(206 if 'MASTER' in name else 67)
print('NATIVE_REOPEN_PASS: original mesh/weights/all shape keys/world and rest bone matrices/driver unchanged;43 new guides')
