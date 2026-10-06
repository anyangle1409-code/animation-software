"""Which blocker: (1) membrane weight composition at flexion 170 (r98): share on trunk / half helper / humerus for membrane vertices;
(2) helper offset direction vs the band's posed surface normal (cap variant)."""
import sys, json; sys.path.insert(0, '/home/user/r97/tools')
import bpy, numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
out = {}
bpy.ops.wm.open_mainfile(filepath=argv[0])
from hgpt_pose import Poser
P = Poser(); P.set_correctives(0)
for m in P.body.modifiers:
    if m.type == 'MASK': m.show_viewport = False
me = P.body.data; rest = P.evaluated(); E = np.array([e.vertices[:] for e in me.edges]); rl = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
names = [g.name for g in P.body.vertex_groups]; gi = {k: i for i, k in enumerate(names)}; n = len(rest)
W = np.zeros((n, len(names)))
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
for spec in [('flexion', 170), ('abduction', 150)]:
    P.reset(); P.elevate('l', *spec); P.elevate('r', *spec); X = P.evaluated()
    r = np.linalg.norm(X[E[:, 0]] - X[E[:, 1]], axis=1) / rl
    mem = np.zeros(n, bool); sel = (r > 2.0) & (rest[E[:, 0], 0] < -0.08) & (rest[E[:, 0], 2] > 1.2); mem[E[sel].ravel()] = True
    trunk = W[:, [gi[b] for b in ('spine_02', 'spine_03', 'clavicle_l', 'scapula_l')]].sum(1)
    out[f'{spec[0]}_{spec[1]}_membrane_vertices'] = int(mem.sum())
    out[f'{spec[0]}_{spec[1]}_mean_weight_share'] = {'trunk_girdle': round(float(trunk[mem].mean()), 3), 'glenohumeral_half': round(float(W[mem, gi['glenohumeral_half_l']].mean()), 3), 'upperarm': round(float(W[mem, gi['upperarm_l']].mean()), 3)}
    out[f'{spec[0]}_{spec[1]}_frac_membrane_vertices_half_ge_0.3'] = round(float((W[mem, gi['glenohumeral_half_l']] >= 0.3).mean()), 3)
bpy.ops.wm.open_mainfile(filepath=argv[1])
P = Poser(); P.set_correctives(0)
for m in P.body.modifiers:
    if m.type == 'MASK': m.show_viewport = False
me = P.body.data; names = [g.name for g in P.body.vertex_groups]; gi = {k: i for i, k in enumerate(names)}; n = len(me.vertices)
Wa = np.zeros(n)
for v in me.vertices:
    for g in v.groups:
        if g.group == gi['axvol_ant_l']: Wa[v.index] = g.weight
band = Wa > 0.05
for spec in [('flexion', 170), ('abduction', 150)]:
    P.reset(); P.elevate('l', *spec); P.elevate('r', *spec); P.upd()
    dg = bpy.context.evaluated_depsgraph_get(); ev = P.body.evaluated_get(dg); mm = ev.to_mesh()
    nr = np.array([v.normal[:] for v in mm.vertices]); ev.to_mesh_clear()
    pbh = P.pb('axvol_ant_l'); hb = P.pb('glenohumeral_half_l')
    off = np.array(pbh.matrix.translation - hb.matrix.translation)
    nb = (nr[band] * Wa[band, None]).sum(0); nb /= np.linalg.norm(nb)
    out[f'{spec[0]}_{spec[1]}_ant_offset_mm'] = round(float(np.linalg.norm(off) * 1000), 1)
    out[f'{spec[0]}_{spec[1]}_ant_offset_vs_posed_band_normal_deg'] = round(float(np.degrees(np.arccos(np.clip(off @ nb / max(np.linalg.norm(off), 1e-9), -1, 1)))), 1)
print('BLOCKER', json.dumps(out))
