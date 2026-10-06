import sys,bpy
argv=sys.argv[sys.argv.index('--')+1:]; bpy.ops.wm.open_mainfile(filepath=argv[0])
for k in ('hgpt_shoulder_corrective','hgpt_flexion_corrective','hgpt_scapular_corrective'):
    if k in bpy.context.scene: del bpy.context.scene[k]
bpy.ops.wm.save_as_mainfile(filepath=argv[1])
