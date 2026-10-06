"""Declared-scope audit: candidate vs parent (topology, non-declared bone weights, shape keys, non-declared bone rest)."""
import sys, json, bpy, numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
DECL = {"spine_02", "spine_03", "clavicle_l", "clavicle_r", "scapula_l", "scapula_r", "upperarm_l", "upperarm_r",
        "glenohumeral_half_l", "glenohumeral_half_r", "glenohumeral_ref_l", "glenohumeral_ref_r"}
def load(f):
    bpy.ops.wm.open_mainfile(filepath=f)
    rig = bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
    body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('HGPT_ORIGINAL_V1_BODY'))
    me = body.data; n = len(me.vertices)
    co = np.empty(n * 3); me.vertices.foreach_get('co', co)
    faces = [tuple(p.vertices) for p in me.polygons]
    names = [g.name for g in body.vertex_groups]
    W = {}
    for v in me.vertices:
        for g in v.groups:
            if g.weight > 0: W[(v.index, names[g.group])] = g.weight
    keys = {k.name: np.array([d.co[:] for d in k.data]) for k in me.shape_keys.key_blocks} if me.shape_keys else {}
    bones = {b.name: (tuple(np.round(b.head_local, 6)), tuple(np.round(b.tail_local, 6)), b.parent.name if b.parent else None) for b in rig.data.bones}
    return dict(co=co, faces=faces, W=W, keys=keys, bones=bones, groups=set(names))
a, b = load(argv[0]), load(argv[1])
wd = [abs(a['W'].get(k, 0) - b['W'].get(k, 0)) for k in set(a['W']) | set(b['W']) if k[1] not in DECL]
nondecl_bone_changes = [n for n in a['bones'] if n not in DECL and (n not in b['bones'] or a['bones'][n] != b['bones'][n])]
out = {"parent": argv[0], "candidate": argv[1],
       "vertex_count": [len(a['co']) // 3, len(b['co']) // 3], "rest_positions_max_diff_m": float(np.abs(a['co'] - b['co']).max()),
       "faces_identical": a['faces'] == b['faces'],
       "nondeclared_weight_max_diff": float(max(wd) if wd else 0.0),
       "nondeclared_bone_rest_changes": nondecl_bone_changes,
       "added_bones": sorted(set(b['bones']) - set(a['bones'])), "removed_bones": sorted(set(a['bones']) - set(b['bones'])),
       "declared_bones_changed": sorted(n for n in DECL if n in a['bones'] and a['bones'][n] != b['bones'].get(n)),
       "shape_keys_identical": set(a['keys']) == set(b['keys']) and all(np.array_equal(a['keys'][k], b['keys'][k]) for k in a['keys']),
       "added_vertex_groups": sorted(b['groups'] - a['groups'])}
out["pass"] = (out["vertex_count"][0] == out["vertex_count"][1] and out["rest_positions_max_diff_m"] == 0.0 and out["faces_identical"]
               and out["nondeclared_weight_max_diff"] < 1e-6 and not out["nondeclared_bone_rest_changes"] and not out["removed_bones"]
               and set(out["added_bones"]) <= DECL and out["shape_keys_identical"])
print("AUDIT " + json.dumps(out))
