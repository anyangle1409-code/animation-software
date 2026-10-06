"""How much of the rest ridge offset survives in a pose: |X_variant - X_r98| / |rest displacement|, ridge vertices (left)."""
import sys, json; sys.path.insert(0, '/home/user/r97/tools')
import bpy, numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
def run(f):
    bpy.ops.wm.open_mainfile(filepath=f)
    from hgpt_pose import Poser
    P = Poser(); P.set_correctives(0)
    for m in P.body.modifiers:
        if m.type == 'MASK': m.show_viewport = False
    out = {'rest': P.evaluated()}
    for spec in ['abduction:0:0', 'abduction:90:0', 'flexion:60:40', 'abduction:150:0', 'flexion:170:0']:
        pl, th, ax = spec.split(':'); P.reset(); P.elevate('l', pl, float(th), axial=float(ax)); out[spec] = P.evaluated()
    return out
a = run(argv[0]); b = run(argv[1])
d0 = np.linalg.norm(b['rest'] - a['rest'], axis=1); m = (d0 > 0.6 * d0.max()) & (a['rest'][:, 0] < 0)
res = {'ridge_vertices': int(m.sum()), 'rest_offset_mm_mean': float(d0[m].mean() * 1000)}
for k in a:
    if k == 'rest': continue
    res[k] = round(float(np.median(np.linalg.norm(b[k] - a[k], axis=1)[m] / d0[m])), 3)
print('RETAIN', json.dumps(res))
