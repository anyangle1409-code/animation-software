"""r99 axillary fold soft-tissue helpers on a copy of r98.
usage: fold99.py -- <r98.blend> <params.json> <mirror_idx.npy> <out.blend>
params: {"folds": {"ant": {...}, "post": {...}}} each: origin, insertion (left side, world), parent, radius, wmax, side ("y_lt"/"y_gt", value),
        s_pow (taper of the along-segment bump), z_max optional."""
import sys, json, bpy, numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
src, prm, mir, out = argv[:4]
P = json.load(open(prm)); mirror = np.load(mir)
bpy.ops.wm.open_mainfile(filepath=src)
rig = bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']; body = bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']; me = body.data
X = np.array([-1.0, 1, 1])
bpy.context.view_layer.objects.active = rig
for o in bpy.context.view_layer.objects: o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT'); eb = rig.data.edit_bones
for key, F in P['folds'].items():
    for s in 'lr':
        m = np.array([1.0, 1, 1]) if s == 'l' else X
        O = np.array(F['origin']) * m; I = np.array(F['insertion']) * m
        b = eb.new(f'axfold_{key}_{s}'); b.head = O; b.tail = I; b.roll = 0.0; b.use_deform = True; b.use_connect = False
        b.parent = eb[F['parent'].replace('<s>', s)]
        t = eb.new(f'axfold_{key}_ins_{s}'); ua = eb[f'upperarm_{s}']
        d = (np.array(ua.tail) - np.array(ua.head)); d /= np.linalg.norm(d)
        t.head = I; t.tail = I + d * 0.03; t.roll = 0.0; t.use_deform = False; t.parent = eb[F.get('target_parent', 'upperarm_<s>').replace('<s>', s)]
bpy.ops.object.mode_set(mode='OBJECT')
for key in P['folds']:
    for s in 'lr':
        pb = rig.pose.bones[f'axfold_{key}_{s}']
        c = pb.constraints.new('STRETCH_TO'); c.name = 'HGPT_AXFOLD_STRETCH'; c.target = rig; c.subtarget = f'axfold_{key}_ins_{s}'
        c.head_tail = 0.0; c.volume = P.get('volume', 'NO_VOLUME'); c.keep_axis = 'SWING_Y'; c.rest_length = rig.data.bones[f'axfold_{key}_{s}'].length
# ---- weights
n = len(me.vertices); co = np.empty(n * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
names = [g.name for g in body.vertex_groups]
for key in P['folds']:
    for s in 'lr':
        if f'axfold_{key}_{s}' not in names: body.vertex_groups.new(name=f'axfold_{key}_{s}')
names = [g.name for g in body.vertex_groups]; gi = {nm: i for i, nm in enumerate(names)}
W = np.zeros((n, len(names)))
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
W0 = W.copy()
DECL = ["spine_02", "spine_03", "clavicle_l", "scapula_l", "upperarm_l", "glenohumeral_half_l"]
dl = [gi[b] for b in DECL]
left = co[:, 0] < -1e-6
info = {}
fold_f = {}
for key, F in P['folds'].items():
    O = np.array(F['origin']); I = np.array(F['insertion']); seg = I - O; L2 = seg @ seg
    t = np.clip((co - O) @ seg / L2, 0, 1); d = np.linalg.norm(co - (O + t[:, None] * seg), axis=1)
    r = np.clip(1 - d / F['radius'], 0, 1); radial = r * r * (3 - 2 * r)
    bump = np.sin(np.pi * t) ** F.get('s_pow', 1.0)
    side = (co[:, 1] < F['side'][1]) if F['side'][0] == 'y_lt' else (co[:, 1] > F['side'][1])
    f = F['wmax'] * radial * bump * left * side
    if 'z_max' in F: f *= co[:, 2] < F['z_max']
    if F.get('smooth_iters'):                         # diffuse the band field over the surface graph (no step at the band edge)
        import scipy.sparse as sp
        E = np.array([e.vertices[:] for e in me.edges])
        A = sp.coo_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr()
        deg = np.asarray(A.sum(1)).ravel()
        for _ in range(F['smooth_iters']):
            f = 0.5 * f + 0.5 * (A @ f) / deg
        f *= left
    fold_f[key] = f
# overlapping bands share: total capped at the larger of the two wmax
tot = sum(fold_f.values()); cap = max(F['wmax'] for F in P['folds'].values())
scale = np.where(tot > cap, cap / np.maximum(tot, 1e-12), 1.0)
decl_share = W[:, dl].sum(1)
for key, f in fold_f.items():
    W[:, gi[f'axfold_{key}_l']] = f * scale * decl_share
moved = sum(fold_f.values()) * scale * decl_share
W[:, dl] *= np.where(decl_share > 0, (decl_share - moved) / np.maximum(decl_share, 1e-12), 0)[:, None]
fold_cols = [gi[f'axfold_{k}_l'] for k in P['folds']]
# protected pruning to 4: drop smallest declared/fold influences, refill declared+fold share
dm = np.zeros(len(names), bool); dm[dl] = True; dm[fold_cols] = True
rows = np.nonzero(left & ((W > 0).sum(1) > 4))[0]
for i in rows:
    extra = int((W[i] > 0).sum()) - 4; c = np.nonzero(dm & (W[i] > 0))[0]
    share = W[i, dm].sum(); W[i, c[np.argsort(W[i, c])[:extra]]] = 0; W[i, dm] *= share / max(W[i, dm].sum(), 1e-12)
# mirror left -> right for every edited row
perm = np.arange(len(names))
for i, nm in enumerate(names):
    if nm.endswith('_l') and nm[:-2] + '_r' in gi: perm[i] = gi[nm[:-2] + '_r']; perm[gi[nm[:-2] + '_r']] = i
ed = np.nonzero(left & (np.abs(W - W0).max(1) > 1e-9))[0]
W[mirror[ed]] = W[ed][:, perm]
changed = np.r_[ed, mirror[ed]]
vg = {g.name: g for g in body.vertex_groups}
for i in changed:
    for j, nm in enumerate(names):
        if abs(W[i, j] - W0[i, j]) < 1e-9: continue
        if W[i, j] > 0: vg[nm].add([int(i)], float(W[i, j]), 'REPLACE')
        else: vg[nm].remove([int(i)])
sc = bpy.context.scene
sc['hgpt_candidate_revision'] = 'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r99'
sc['hgpt_rig_revision'] = 'rev2f_scapula_ac_pivot_gh_helpers_axillary_fold_helpers'
sc['hgpt_r99_fold_helpers'] = json.dumps({'params': P, 'runtime': 'axfold bone: parent frame at origin, Y aimed at and scaled to the insertion target (child of upperarm); Blender STRETCH_TO', 'changed_vertices': int(len(changed))})
sc['hgpt_r99_parent'] = json.dumps({'revision': 'r98', 'sha256': '89e98cc74cc7dfd17f6d5a0991a9f0f6954e8de4d99ea3d3b30be2ec617b2ce0'})
bpy.ops.wm.save_as_mainfile(filepath=out, compress=False)
print('FOLD', json.dumps({'changed': int(len(changed)), 'max_fold_w': {k: float((f * scale * decl_share).max()) for k, f in fold_f.items()}, 'banded': {k: int((f > 0.01).sum()) for k, f in fold_f.items()}, 'max_infl': int((W[:, [gi[x] for x in names if x in {b.name for b in rig.data.bones}]] > 0).sum(1).max())}))
