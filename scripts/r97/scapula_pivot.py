"""Rig mechanics: move each scapula bone's pivot (head) to the AC joint = clavicle tail, translating head and tail by the same
vector so the bone's direction and roll (its local rotation axes) are unchanged. Rest mesh and all other bones unchanged."""
import sys, json, bpy
from mathutils import Vector
argv = sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
rig = bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
bpy.context.view_layer.objects.active = rig
for o in bpy.context.view_layer.objects: o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
log = {}
for s in 'lr':
    sc, cl = eb[f'scapula_{s}'], eb[f'clavicle_{s}']
    before = (tuple(sc.head), tuple(sc.tail), sc.roll)
    off = cl.tail - sc.head
    sc.head += off; sc.tail += off
    log[s] = {'offset_m': [round(x, 5) for x in off], 'head_before': [round(x,5) for x in before[0]], 'head_after': [round(x,5) for x in sc.head], 'roll_unchanged': abs(sc.roll - before[2]) < 1e-9}
bpy.ops.object.mode_set(mode='OBJECT')
sc = bpy.context.scene
sc['hgpt_rig_revision'] = 'rev2d_scapula_pivot_at_ac_joint'
sc['hgpt_scapula_pivot_fraction'] = 0.0
sc['hgpt_scapula_pivot'] = 'ac_joint (clavicle tail); orientation and roll unchanged from rev2c'
print(json.dumps(log))
bpy.ops.wm.save_as_mainfile(filepath=argv[1], compress=False)
