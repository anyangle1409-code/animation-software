"""rest.npz for the solver: world rest coords, loop triangles, weights (r95-lineage groups only), bones."""
import sys, bpy, numpy as np
argv = sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
rig = bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
body = bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
me = body.data; n = len(me.vertices)
co = np.empty(n*3); me.vertices.foreach_get('co', co); co = co.reshape(-1,3)
Mw = np.array(body.matrix_world); co = co @ Mw[:3,:3].T + Mw[:3,3]
me.calc_loop_triangles(); tris = np.array([t.vertices[:] for t in me.loop_triangles])
Ma = np.array(rig.matrix_world)
bones = {b.name: (np.array(Ma @ b.head_local.to_4d())[:3], np.array(Ma @ b.tail_local.to_4d())[:3]) for b in rig.data.bones}
bonesset = set(bones)
names = [g.name for g in body.vertex_groups if g.name in bonesset]
col = {g.index: names.index(g.name) for g in body.vertex_groups if g.name in bonesset}
W = np.zeros((n, len(names)), np.float32)
for v in me.vertices:
    for g in v.groups:
        if g.group in col: W[v.index, col[g.group]] = g.weight
bn = list(bones); bh = np.array([bones[b][0] for b in bn]); bt = np.array([bones[b][1] for b in bn])
# integrity of interpolated rows
bonegroups = list(range(len(names)))
s = W[:, bonegroups].sum(1)
kb = me.shape_keys.key_blocks if me.shape_keys else []
print('DUMP', {'n': n, 'tris': tris.shape[0], 'weight_sum_minmax': [float(s.min()), float(s.max())], 'max_infl': int((W[:, bonegroups] > 0).sum(1).max()),
               'keys': len(kb)})
np.savez(argv[1], co=co, tris=tris, W=W, names=np.array(names), bn=np.array(bn), bh=bh, bt=bt)
