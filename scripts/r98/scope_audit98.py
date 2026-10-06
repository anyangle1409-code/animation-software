"""r98 declared-scope audit vs r95 working parent (weights, topology, rest shape region/cap, shape-key deltas) and vs r97 (rig)."""
import sys, json, bpy, numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
r95p, r97p, cand = argv[:3]
DECL = {"spine_02", "spine_03", "clavicle_l", "clavicle_r", "scapula_l", "scapula_r", "upperarm_l", "upperarm_r", "glenohumeral_half_l", "glenohumeral_half_r"}
def load(f):
    bpy.ops.wm.open_mainfile(filepath=f)
    rig = bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']; body = bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']; me = body.data
    n = len(me.vertices); co = np.empty(n * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    names = [g.name for g in body.vertex_groups]; W = {}
    for v in me.vertices:
        for g in v.groups:
            if g.weight > 0: W[(v.index, names[g.group])] = g.weight
    keys = {k.name: np.array([d.co[:] for d in k.data]) for k in me.shape_keys.key_blocks}
    bones = {b.name: (tuple(np.round(b.head_local, 6)), tuple(np.round(b.tail_local, 6)), b.parent.name if b.parent else None, b.use_deform) for b in rig.data.bones}
    cons = {p.name: [(c.type, getattr(c, 'subtarget', None), round(c.influence, 4)) for c in p.constraints] for p in rig.pose.bones if p.constraints}
    return dict(co=co, faces=[tuple(p.vertices) for p in me.polygons], W=W, keys=keys, bones=bones, cons=cons, n=n)
a, r7, c = load(r95p), load(r97p), load(cand)
disp = np.linalg.norm(c['co'] - a['co'], axis=1); moved = disp > 1e-7; mc = a['co'][moved]
wd = [abs(a['W'].get(k, 0) - c['W'].get(k, 0)) for k in set(a['W']) | set(c['W']) if k[1] not in DECL]
key_delta_err = max(float(np.abs((c['keys'][k] - c['keys']['Basis']) - (a['keys'][k] - a['keys']['Basis'])).max()) for k in a['keys'])
out = {"r95_parent": r95p, "r97_reference": r97p, "candidate": cand,
  "vertex_count": [a['n'], c['n']], "faces_identical_to_r95": a['faces'] == c['faces'], "new_vertices": c['n'] - a['n'],
  "rest_moved_vertices": int(moved.sum()), "rest_max_displacement_m": float(disp.max()),
  "rest_moved_region": {"abs_x_min": float(np.abs(mc[:, 0]).min()) if len(mc) else None, "z_min": float(mc[:, 2].min()) if len(mc) else None, "z_max": float(mc[:, 2].max()) if len(mc) else None},
  "rest_mirror_symmetry_max_err_m": None,
  "shape_key_delta_preserved_max_err_m": key_delta_err,
  "nondeclared_weight_max_diff_vs_r95": float(max(wd) if wd else 0.0),
  "rig_identical_to_r97": c['bones'] == r7['bones'], "constraints_identical_to_r97": c['cons'] == r7['cons'],
  "max_influences": int(max(np.bincount([k[0] for k in c['W'] if k[1] in c['bones']])))}
from mathutils.kdtree import KDTree
kd = KDTree(c['n'])
for i, p in enumerate(c['co']): kd.insert(p, i)
kd.balance()
out["rest_mirror_symmetry_max_err_m"] = float(max(kd.find((-p[0], p[1], p[2]))[2] for p in c['co']))
out["pass"] = bool(out["faces_identical_to_r95"] and out["rest_max_displacement_m"] <= 0.012 and out["rest_moved_region"]["abs_x_min"] >= 0.09
  and out["rest_moved_region"]["z_min"] >= 1.15 and out["rest_moved_region"]["z_max"] <= 1.46 and key_delta_err < 1e-6
  and out["nondeclared_weight_max_diff_vs_r95"] < 1e-6 and out["rig_identical_to_r97"] and out["constraints_identical_to_r97"]
  and out["rest_mirror_symmetry_max_err_m"] < 1e-5 and out["max_influences"] <= 4)
print("AUDIT " + json.dumps(out))
