"""Glenohumeral helper = half of the humerus' swing + all of its axial twist, with standard constraints only:
  1. COPY_ROTATION (world) of upperarm_<s>, influence 1        -> helper = swing * twist
  2. DAMPED_TRACK to the tail of glenohumeral_ref_<s>, infl 0.5 -> slerp(swing*twist, twist, 0.5) = swing^0.5 * twist
glenohumeral_ref_<s>: non-deforming, child of scapula_<s>, rest frame of upperarm_<s> (the arm's rest direction carried by the
scapula). Runtime equivalent: q_helper = slerp(I, swing(q_upperarm_local), 0.5) * twist(q_upperarm_local), twist about bone Y."""
import sys, bpy, json
argv = sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
rig = bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
bpy.context.view_layer.objects.active = rig
for o in bpy.context.view_layer.objects: o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
for s in 'lr':
    ua = eb[f'upperarm_{s}']
    r = eb.get(f'glenohumeral_ref_{s}') or eb.new(f'glenohumeral_ref_{s}')
    r.head = ua.head.copy(); r.tail = ua.head + (ua.tail - ua.head) * 0.35; r.roll = ua.roll
    r.parent = eb[f'scapula_{s}']; r.use_connect = False; r.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
for s in 'lr':
    pb = rig.pose.bones[f'glenohumeral_half_{s}']
    for c in list(pb.constraints): pb.constraints.remove(c)
    c1 = pb.constraints.new('COPY_ROTATION'); c1.name = 'HGPT_GH_FOLLOW'
    c1.target = rig; c1.subtarget = f'upperarm_{s}'; c1.target_space = 'WORLD'; c1.owner_space = 'WORLD'; c1.mix_mode = 'REPLACE'; c1.influence = 1.0
    c2 = pb.constraints.new('DAMPED_TRACK'); c2.name = 'HGPT_GH_HALF_SWING'
    c2.target = rig; c2.subtarget = f'glenohumeral_ref_{s}'; c2.head_tail = 1.0; c2.track_axis = 'TRACK_Y'; c2.influence = 0.5
sc = bpy.context.scene
sc['hgpt_rig_revision'] = 'rev2e_scapula_ac_pivot_gh_helpers'
sc['hgpt_gh_half_helpers'] = json.dumps([{'name': f'glenohumeral_half_{s}', 'reference': f'glenohumeral_ref_{s}', 'parent': f'scapula_{s}', 'rest_frame': f'upperarm_{s}', 'swing_fraction': 0.5, 'twist_fraction': 1.0, 'blender': 'COPY_ROTATION(world, upperarm) then DAMPED_TRACK(ref tail, influence 0.5)', 'runtime': 'q = slerp(I, swing, 0.5) * twist of the upperarm local rotation, twist about bone Y'} for s in 'lr'])
print('bones', len(rig.data.bones))
bpy.ops.wm.save_as_mainfile(filepath=argv[1], compress=False)
