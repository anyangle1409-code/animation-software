#!/usr/bin/env python3
"""Foot proportion source audit for the ORIGINAL_v1 body (read-only; run with Blender's Python / bpy).

Measures, on the unchanged native model, where the foot length sits relative to:
  * stature-conditioned ANSUR II male standing values at 1.82 m (foot length, ball-of-foot length, foot breadth, heel
    breadth, lateral malleolus height) by OLS on stature, n = 4,082;
  * the 206-bone anatomical master foot stations (calcaneus, metatarsal 1, hallux phalanges) -- recorded as
    low-confidence control stations, not segmented bone surfaces;
  * the 67-joint runtime foot/toe controls.
Nothing is written into the model; the source file SHA is checked before and after.

  python3.13 audit_original_foot_source_proportions_blender.py --blend ORIGINAL.blend --ansur ANSUR_II_MALE_Public.csv --out JSON
"""
import argparse, csv, hashlib, json, math, sys
from pathlib import Path

import bpy
from mathutils import Vector

BODY = 'HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE'
RIG = 'HGPT_CANONICAL_V4_ORIGINAL'
MASTER = 'HGPT_ANATOMICAL_MASTER'
STATURE = 1820.0


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def ansur(path, cols):
    rows = list(csv.DictReader(open(path, newline='', encoding='latin-1')))
    x = [float(r['stature']) for r in rows]
    out = {}
    for c in cols:
        y = [float(r[c]) for r in rows]
        n = len(x); mx = sum(x) / n; my = sum(y) / n
        b = sum((a - mx) * (c2 - my) for a, c2 in zip(x, y)) / sum((a - mx) ** 2 for a in x)
        a0 = my - b * mx
        rsd = math.sqrt(sum((c2 - (a0 + b * a)) ** 2 for a, c2 in zip(x, y)) / (n - 2))
        out[c] = {'prediction_mm_at_1820': round(a0 + b * STATURE, 1), 'residual_sd_mm': round(rsd, 1), 'n': n,
                  'raw_mean_mm': round(my, 1)}
    return out


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    for a in ('--blend', '--ansur', '--out'):
        ap.add_argument(a, required=True)
    o = ap.parse_args(argv)
    h0 = sha(o.blend)
    bpy.ops.wm.open_mainfile(filepath=str(Path(o.blend).resolve()))
    body = bpy.data.objects[BODY]; rig = bpy.data.objects[RIG]; master = bpy.data.objects[MASTER]
    M = body.matrix_world
    V = [M @ v.co for v in body.data.vertices]                       # rest coordinates (armature modifier at rest pose)
    zmin = min(v.z for v in V)
    res = {'source': {'blend': Path(o.blend).name, 'sha256': h0}, 'ansur_182': ansur(o.ansur, [
        'footlength', 'balloffootlength', 'footbreadthhorizontal', 'heelbreadth', 'lateralmalleolusheight'])}
    feet = {}
    for side, sgn in (('left', 1), ('right', -1)):
        P = [v for v in V if v.z < zmin + 0.16 and v.x * sgn > 0.02]
        heel = max(P, key=lambda v: v.y); tip = min(P, key=lambda v: v.y)   # HGPT: -Y anterior
        xs = [v.x for v in P]
        f = {'heel_y_mm': round(heel.y * 1000, 2), 'toe_tip_y_mm': round(tip.y * 1000, 2), 'toe_tip_x_mm': round(tip.x * 1000, 2),
             'mesh_foot_length_mm': round((heel.y - tip.y) * 1000, 2),
             'mesh_foot_breadth_mm': round((max(xs) - min(xs)) * 1000, 2), 'vertex_count_below_160mm': len(P)}
        mb = {(b.name[5:] if b.name.startswith('anat_') else b.name): b for b in master.data.bones}
        def mw(name, end):
            b = mb[name]; return master.matrix_world @ (b.head_local if end == 'head' else b.tail_local)
        st = {}
        for n in [n for n in mb if n.endswith('_' + side) and any(n.startswith(k) for k in ('calcaneus', 'talus', 'metatarsal', 'hallux', 'toe', 'fibula', 'tibia'))]:
            st[n] = {'head_mm': [round(c * 1000, 2) for c in mw(n, 'head')], 'tail_mm': [round(c * 1000, 2) for c in mw(n, 'tail')]}
        f['master_stations'] = st
        rb = {b.name: b for b in rig.data.bones}
        suf = 'l' if side == 'left' else 'r'
        ctl = {}
        for n in rb:
            if n.lower() in (f'foot_{suf}', f'toe_{suf}', f'shin_{suf}', f'calf_{suf}', f'lowerleg_{suf}') or n.lower().startswith(('foot_', 'toe_', 'ball_', 'heel_')):
                b = rb[n]
                ctl[n] = {'head_mm': [round(c * 1000, 2) for c in rig.matrix_world @ b.head_local], 'tail_mm': [round(c * 1000, 2) for c in rig.matrix_world @ b.tail_local]}
        f['runtime_controls'] = ctl
        # derived: positions along the foot (HGPT -Y anterior) relative to the mesh heel
        hy = heel.y * 1000
        def along(y_mm):
            return round(hy - y_mm, 2)
        d = {}
        if f'metatarsal_1_{side}' in st:
            d['heel_to_MT1_distal_station_mm'] = along(st[f'metatarsal_1_{side}']['tail_mm'][1])
        tips = [v['tail_mm'] for k, v in st.items() if k.startswith(('hallux_distal', 'toe2_distal'))]
        if tips:
            d['heel_to_most_anterior_distal_phalanx_station_mm'] = along(min(t[1] for t in tips))
        if f'calcaneus_{side}' in st:
            d['heel_to_calcaneus_posterior_station_mm'] = round(hy - max(st[f'calcaneus_{side}']['head_mm'][1], st[f'calcaneus_{side}']['tail_mm'][1]), 2)
        if f'fibula_{side}' in st:
            d['lateral_malleolus_station_height_mm'] = round(min(st[f'fibula_{side}']['head_mm'][2], st[f'fibula_{side}']['tail_mm'][2]), 2)
        toe = [v for k, v in ctl.items() if k.lower() == ('toe_r' if side == 'left' else 'toe_l')]
        if toe:
            d['heel_to_runtime_toe_pivot_mm'] = along(toe[0]['head_mm'][1])
        d['runtime_toe_pivot_to_mesh_tip_mm'] = round((toe[0]['head_mm'][1] - tip.y * 1000), 2) if toe else None
        f['derived'] = d
        feet[side] = f
    res['feet'] = feet
    res['floor_z_mm'] = round(zmin * 1000, 4)
    res['source_sha256_after'] = sha(o.blend)
    assert res['source_sha256_after'] == h0
    Path(o.out).write_text(json.dumps(res, indent=1) + '\n')
    print(json.dumps({k: v for k, v in res.items() if k != 'feet'}, indent=1))
    for s, f in feet.items():
        print(s, {k: v for k, v in f.items() if k not in ('master_stations', 'runtime_controls')})
        print('  stations', sorted(f['master_stations']))


if __name__ == '__main__':
    main()
