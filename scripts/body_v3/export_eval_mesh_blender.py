"""Export the evaluated (posed) body mesh of a blend to an .npz (V, F), optionally scaled to a stature.
usage: python3.13 export_eval_mesh_blender.py -- <blend> <out.npz> [stature_m] [object name]"""
import sys
import bpy
import numpy as np
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects[a[3]] if len(a) > 3 else max((o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render
                                                  and "FLOOR" not in o.name), key=lambda o: len(o.data.vertices))
dg = bpy.context.evaluated_depsgraph_get(); me = ob.evaluated_get(dg).to_mesh(); me.calc_loop_triangles()
V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
mw = np.array(ob.matrix_world); V = V @ mw[:3, :3].T + mw[:3, 3]
F = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get("vertices", F); F = F.reshape(-1, 3)
if len(a) > 2 and float(a[2]) > 0:
    z0 = V[:, 2].min(); k = float(a[2]) / (V[:, 2].max() - z0); V = (V - [0, 0, z0]) * k
np.savez_compressed(a[1], V=V.astype(np.float32), F=F); print("EXPORT", ob.name, len(V), round(float(np.ptp(V[:, 2])), 4))
