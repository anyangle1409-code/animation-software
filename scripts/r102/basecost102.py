"""Base-motion cost of re-sourcing fold weight: zero-offset variant vs r98, in-band and out-of-band displacement (mm)."""
import sys, json; sys.path.insert(0, '/home/user/r97/tools')
import bpy, numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
POSES = {'rest': ('abduction', 0, 0, 0, 0), 'curl_top': ('flexion', 15, 0, 125, 0), 'abduction_030': ('abduction', 30, 0, 0, 0),
         'horizontal_adduction_90': ('flexion', 90, 0, 20, 35), 'side_internal_40': ('abduction', 0, -40, 0, 0), 'side_external_40': ('abduction', 0, 40, 0, 0),
         'press_bottom_like': (20, 85, 60, 95, 0), 'pullup_top_like': (10, 60, 10, 130, 0), 'flexion_170': ('flexion', 170, 0, 0, 0), 'abduction_150': ('abduction', 150, 0, 0, 0)}
def run(f):
    bpy.ops.wm.open_mainfile(filepath=f)
    from hgpt_pose import Poser
    P = Poser(); P.set_correctives(0)
    for m in P.body.modifiers:
        if m.type == 'MASK': m.show_viewport = False
    out = {}
    for k, (pl, th, ax, el, hz) in POSES.items():
        P.reset()
        for s in 'lr': P.elevate(s, pl, th, axial=ax, elbow=el, horizontal=hz)
        out[k] = P.evaluated()
    band = None
    if any(g.name.startswith('axvol_') for g in P.body.vertex_groups):
        ids = {g.index for g in P.body.vertex_groups if g.name.startswith('axvol_')}
        band = np.array([any(g.group in ids and g.weight > 1e-6 for g in v.groups) for v in P.body.data.vertices])
    return out, band
a, _ = run(argv[0]); b, band = run(argv[1])
res = {}
for k in POSES:
    d = np.linalg.norm(b[k] - a[k], axis=1) * 1000
    res[k] = {'band_max_mm': round(float(d[band].max()), 2), 'band_p90_mm': round(float(np.percentile(d[band], 90)), 2), 'outside_band_max_mm': round(float(d[~band].max()), 3)}
json.dump(res, open(argv[2], 'w'), indent=1); print('COST', json.dumps(res))
