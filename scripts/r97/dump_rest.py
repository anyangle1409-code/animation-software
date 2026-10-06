import sys, bpy, numpy as np
argv = sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
rig = bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
body = next(o for o in bpy.data.objects if o.type=='MESH' and o.find_armature()==rig)
me = body.data; n = len(me.vertices)
co = np.empty(n*3); me.vertices.foreach_get('co', co); co = co.reshape(-1,3)
Mw = np.array(body.matrix_world); co = co @ Mw[:3,:3].T + Mw[:3,3]
tris = np.array([p.vertices[:] for p in me.polygons])
names = [g.name for g in body.vertex_groups]
W = np.zeros((n, len(names)), np.float32)
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
Ma = np.array(rig.matrix_world)
bones = {b.name: (np.array(Ma @ b.head_local.to_4d())[:3], np.array(Ma @ b.tail_local.to_4d())[:3]) for b in rig.data.bones}
bn = list(bones); bh = np.array([bones[b][0] for b in bn]); bt = np.array([bones[b][1] for b in bn])
print('matrix_world body', Mw.round(3).tolist(), 'rig', Ma.round(3).tolist(), 'faces', tris.shape)
np.savez(argv[1], co=co, tris=tris, W=W, names=np.array(names), bn=np.array(bn), bh=bh, bt=bt)
