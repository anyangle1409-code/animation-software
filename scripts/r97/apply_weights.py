import sys, bpy, numpy as np
argv = sys.argv[sys.argv.index('--')+1:]
src, wfile, out = argv[:3]
bpy.ops.wm.open_mainfile(filepath=src)
rig = bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
body = next(o for o in bpy.data.objects if o.type=='MESH' and o.find_armature()==rig and 'SHORTS' not in o.name)
d = np.load(wfile); W = d['W']; names = [str(x) for x in d['names']]; changed = np.unique(d['changed'])
for nm in names:
    if nm not in body.vertex_groups: body.vertex_groups.new(name=nm)
vg = {g.name: g for g in body.vertex_groups}
for i in changed:
    i = int(i)
    for j, nm in enumerate(names):
        g = vg[nm]
        if W[i, j] > 0: g.add([i], float(W[i, j]), 'REPLACE')
        else:
            try: g.remove([i])
            except RuntimeError: pass
if body.data.shape_keys:
    for kb in body.data.shape_keys.key_blocks[1:]: kb.value = 0.0
bpy.ops.wm.save_as_mainfile(filepath=out, compress=False)
print('applied', len(changed))
