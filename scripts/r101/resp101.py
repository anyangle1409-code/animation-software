import sys, json; sys.path.insert(0, '/home/user/r97/tools')
import bpy, numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
def load(f):
    bpy.ops.wm.open_mainfile(filepath=f)
    from hgpt_pose import Poser
    P = Poser(); P.set_correctives(0)
    for m in P.body.modifiers:
        if m.type == 'MASK': m.show_viewport = False
    return P
res = {}; store = {}
for tag, f in (('r98', argv[0]), ('v', argv[1])):
    P = load(f); store[tag] = {}
    keys = [b.name for b in P.rig.pose.bones if b.name.startswith('axvol_') and 'probe' not in b.name and b.name.endswith('_l')]
    for plane in ('abduction', 'flexion'):
        for th in (0, 30, 60, 90, 120, 150, 170):
            for ax in (-40, 0, 40):
                P.reset(); P.elevate('l', plane, th, axial=ax if th <= 120 else ax * 0.6); P.elevate('r', plane, th, axial=ax if th <= 120 else ax * 0.6)
                k = f'{plane}_{th:03d}_{ax:+d}'; store[tag][k] = P.evaluated()
                if tag == 'v':
                    res[k] = {b: round(float(np.linalg.norm(np.array(P.pb(b).location))) * 1000, 2) for b in keys}
    if tag == 'v':
        P.reset(); restv = P.evaluated()
sym = None
out = {}
for k in res:
    d = np.linalg.norm(store['v'][k] - store['r98'][k], axis=1)
    out[k] = {'helper_offset_mm': res[k], 'max_vertex_shift_mm': round(float(d.max() * 1000), 2)}
json.dump(out, open(argv[2], 'w'), indent=0)
for k, v in out.items():
    if k.endswith('+0') or k.startswith('flexion_150'): print(k, v)
