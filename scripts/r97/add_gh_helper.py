"""Rig mechanics (rotation-aware layer): add a glenohumeral half-rotation helper per side.
glenohumeral_half_<s>: child of scapula_<s>, rest frame identical to upperarm_<s> (head at the glenohumeral centre, same direction
and roll), COPY_ROTATION of upperarm_<s> in world space at influence 0.5 -> it carries exactly half of the humerus' rotation
relative to the scapula (swing and axial twist). Runtime equivalent: q_half = slerp(identity, q_upperarm_local, 0.5)."""
import sys, json, bpy
argv = sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
rig = bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
body = next(o for o in bpy.data.objects if o.type=='MESH' and o.find_armature()==rig and 'SHORTS' not in o.name)
bpy.context.view_layer.objects.active = rig
for o in bpy.context.view_layer.objects: o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
for s in 'lr':
    ua = eb[f'upperarm_{s}']
    h = eb.get(f'glenohumeral_half_{s}') or eb.new(f'glenohumeral_half_{s}')
    h.head = ua.head.copy(); h.tail = ua.head + (ua.tail - ua.head) * 0.35; h.roll = ua.roll
    h.parent = eb[f'scapula_{s}']; h.use_connect = False; h.use_deform = True
bpy.ops.object.mode_set(mode='OBJECT')
for s in 'lr':
    pb = rig.pose.bones[f'glenohumeral_half_{s}']
    for c in list(pb.constraints): pb.constraints.remove(c)
    c = pb.constraints.new('COPY_ROTATION'); c.name = 'HGPT_GH_HALF'
    c.target = rig; c.subtarget = f'upperarm_{s}'; c.target_space = 'WORLD'; c.owner_space = 'WORLD'
    c.mix_mode = 'REPLACE'; c.influence = 0.5
    if f'glenohumeral_half_{s}' not in body.vertex_groups: body.vertex_groups.new(name=f'glenohumeral_half_{s}')
sc = bpy.context.scene
sc['hgpt_rig_revision'] = 'rev2e_scapula_ac_pivot_gh_half_helpers'
sc['hgpt_gh_half_helpers'] = json.dumps([{'name': f'glenohumeral_half_{s}', 'parent': f'scapula_{s}', 'rest_frame': f'upperarm_{s}', 'rotation_fraction': 0.5, 'driver': 'COPY_ROTATION world, influence 0.5 (runtime: slerp(identity, upperarm local rotation, 0.5))'} for s in 'lr'])
print('bones', len(rig.data.bones))
bpy.ops.wm.save_as_mainfile(filepath=argv[1], compress=False)
