"""r101 rotation-driven fold-volume helpers on a fresh copy of r98.
usage: vol101.py -- <r98.blend> <params.json> <mirror_idx.npy> <out.blend> <receipt.json>"""
import sys, json, hashlib, bpy, numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
src, prm, mir, out, rec = argv[:5]
P = json.load(open(prm)); mirror = np.load(mir)
bpy.ops.wm.open_mainfile(filepath=src)
rig = bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']; body = bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']; me = body.data
n = len(me.vertices); co = np.empty(n * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
nrm = np.array([v.normal[:] for v in me.vertices]); left = co[:, 0] < -1e-6
names = [g.name for g in body.vertex_groups]; gi = {k: i for i, k in enumerate(names)}
W = np.zeros((n, len(names)))
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
W0 = W.copy(); hh = gi['glenohumeral_half_l']
# ---- bands (left), transfer fraction of half-helper weight, band normal
bands = {}
for key, F in P['folds'].items():
    O = np.array(F['origin']); I = np.array(F['insertion']); seg = I - O
    t = np.clip((co - O) @ seg / (seg @ seg), 0, 1); d = np.linalg.norm(co - (O + t[:, None] * seg), axis=1)
    r = np.clip(d / F['radius'], 0, 1); radial = 0.5 * (1 + np.cos(np.pi * r)); bump = np.sin(np.pi * t)
    side = (co[:, 1] < F['side'][1]) if F['side'][0] == 'y_lt' else (co[:, 1] > F['side'][1])
    f = P['band_max'] * radial * bump * side * left * (W[:, hh] > 0.02)
    nv = (nrm * (f * W[:, hh])[:, None]).sum(0); nv /= np.linalg.norm(nv)
    bands[key] = (f, nv)
tot = sum(b[0] for b in bands.values()); sc_ = np.where(tot > P['band_max'], P['band_max'] / np.maximum(tot, 1e-12), 1.0)
# ---- bones
bpy.context.view_layer.objects.active = rig
for o in bpy.context.view_layer.objects: o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT'); eb = rig.data.edit_bones
for s in 'lr':
    h = eb[f'glenohumeral_half_{s}']; ua = eb[f'upperarm_{s}']; dvec = (ua.tail - ua.head).normalized()
    for key in bands:
        b = eb.new(f'axvol_{key}_{s}'); b.head = h.head.copy(); b.tail = h.tail.copy(); b.roll = h.roll; b.parent = h; b.use_deform = True
    p1 = eb.new(f'axvol_probe_{s}'); p1.head = ua.head + dvec * 0.2; p1.tail = p1.head + dvec * 0.02; p1.parent = ua; p1.use_deform = False
    p2 = eb.new(f'axvol_probe_ref_{s}'); p2.head = ua.head + dvec * 0.2; p2.tail = p2.head + dvec * 0.02; p2.parent = eb[f'glenohumeral_ref_{s}']; p2.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
d0, d1, a = P['d0'], P['d1'], P['a_max']
tx = f"min(1,max(0,(d-{d0})/{d1 - d0}))"
for s in 'lr':
    for key, (f, nv) in bands.items():
        nw = nv * (np.array([-1, 1, 1]) if s == 'r' else 1)
        bone = rig.data.bones[f'axvol_{key}_{s}']; nl = bone.matrix_local.to_3x3().inverted() @ Vector(nw)
        pb = rig.pose.bones[f'axvol_{key}_{s}']
        for i in range(3):
            fc = pb.driver_add('location', i); drv = fc.driver; drv.type = 'SCRIPTED'
            v = drv.variables.new(); v.name = 'd'; v.type = 'LOC_DIFF'
            v.targets[0].id = rig; v.targets[0].bone_target = f'axvol_probe_{s}'; v.targets[0].transform_space = 'WORLD_SPACE'
            v.targets[1].id = rig; v.targets[1].bone_target = f'axvol_probe_ref_{s}'; v.targets[1].transform_space = 'WORLD_SPACE'
            drv.expression = f"{a * nl[i]:.6f}*{tx}*{tx}*(3-2*{tx})"
            for m in list(fc.modifiers): fc.modifiers.remove(m)
# ---- weights: move fraction of the half-helper weight to the fold helper (base motion unchanged)
for key in bands:
    for s in 'lr':
        if f'axvol_{key}_{s}' not in gi: body.vertex_groups.new(name=f'axvol_{key}_{s}')
names = [g.name for g in body.vertex_groups]; gi = {k: i for i, k in enumerate(names)}
W = np.c_[W, np.zeros((n, len(names) - W.shape[1]))]; W0 = np.c_[W0, np.zeros((n, len(names) - W0.shape[1]))]
for key, (f, nv) in bands.items():
    moved = f * sc_ * W[:, hh] if False else f * sc_ * W0[:, hh]
    W[:, gi[f'axvol_{key}_l']] = moved
W[:, hh] = W0[:, hh] * (1 - sum(b[0] for b in bands.values()) * sc_)
ed = np.nonzero(left & (np.abs(W - W0).max(1) > 1e-9))[0]
perm = np.arange(len(names))
for i, nm in enumerate(names):
    if nm.endswith('_l') and nm[:-2] + '_r' in gi: perm[i] = gi[nm[:-2] + '_r']; perm[gi[nm[:-2] + '_r']] = i
W[mirror[ed]] = W[ed][:, perm]
bonesset = {b.name for b in rig.data.bones}
infl = (W[:, [gi[x] for x in names if x in bonesset]] > 0).sum(1)
over = np.nonzero(infl > 4)[0]
for i in over:      # fold helper replaces part of the half helper: drop the smallest fold share into the half helper if >4
    ks = [gi[f'axvol_{k}_{"l" if co[i,0] < 0 else "r"}'] for k in bands]; hk = gi['glenohumeral_half_l' if co[i, 0] < 0 else 'glenohumeral_half_r']
    k = min(ks, key=lambda j: W[i, j] if W[i, j] > 0 else 9); W[i, hk] += W[i, k]; W[i, k] = 0
vg = {g.name: g for g in body.vertex_groups}
for i in np.r_[ed, mirror[ed]]:
    for j, nm in enumerate(names):
        if abs(W[i, j] - W0[i, j]) < 1e-12: continue
        if W[i, j] > 0: vg[nm].add([int(i)], float(W[i, j]), 'REPLACE')
        else: vg[nm].remove([int(i)])
sc = bpy.context.scene
sc['hgpt_candidate_revision'] = 'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r101'
sc['hgpt_r101_fold_volume'] = json.dumps({'params': P, 'band_normals': {k: b[1].round(4).tolist() for k, b in bands.items()}, 'runtime': 'axvol location = a_max*smoothstep(d0,d1,|probe-probe_ref|)*n_local; probe/probe_ref on the humerus axis 0.2 m from the GH centre under upperarm/glenohumeral_ref'})
sc['hgpt_r101_parent'] = json.dumps({'revision': 'r98', 'sha256': '89e98cc74cc7dfd17f6d5a0991a9f0f6954e8de4d99ea3d3b30be2ec617b2ce0'})
bpy.ops.wm.save_as_mainfile(filepath=out, compress=False)
R = {'params': P, 'band_vertices_per_side': {k: int((b[0] > 0.01).sum()) for k, b in bands.items()}, 'band_normals': {k: b[1].round(4).tolist() for k, b in bands.items()},
     'changed_vertices': int(2 * len(ed)), 'max_influences': int(((W[:, [gi[x] for x in names if x in bonesset]] > 0).sum(1)).max()),
     'nondeclared_unchanged': bool(np.abs((W - W0)[:, [j for j, nm in enumerate(names) if not (nm.startswith('glenohumeral_half') or nm.startswith('axvol_'))]]).max() < 1e-9),
     'out_sha256': hashlib.sha256(open(out, 'rb').read()).hexdigest()}
json.dump(R, open(rec, 'w'), indent=1); print('VOL', json.dumps({k: R[k] for k in ('band_vertices_per_side', 'band_normals', 'changed_vertices', 'max_influences', 'nondeclared_unchanged')}))
