import sys, bpy, numpy as np, json
argv=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); s=np.load(argv[1]); W=s['W']; names=[str(x) for x in s['names']]
rig=bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']; body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('HGPT_ORIGINAL_V1_BODY'))
gi={g.name:g.index for g in body.vertex_groups}
F=np.zeros_like(W)
col={gi[n]:j for j,n in enumerate(names)}
for v in body.data.vertices:
    for g in v.groups:
        if g.group in col: F[v.index, col[g.group]]=g.weight
sc=bpy.context.scene
print(json.dumps({'max_weight_diff_vs_solution': float(np.abs(F-W).max()), 'bones': len(rig.data.bones), 'deform_bones': sum(b.use_deform for b in rig.data.bones), 'shape_key_values': [round(k.value,6) for k in body.data.shape_keys.key_blocks[1:]], 'corrective_driver_configs_present': [k for k in ('hgpt_shoulder_corrective','hgpt_flexion_corrective','hgpt_scapular_corrective') if k in sc], 'revision': sc['hgpt_candidate_revision'], 'rig_revision': sc['hgpt_rig_revision'], 'constraints': {pb.name:[c.type for c in pb.constraints] for pb in rig.pose.bones if pb.constraints}}))
