#!/usr/bin/env python3
"""Blender (Workbench) diagnostic renders of the left knee at 0/60/120 deg flexion: c004 static patella vs the scaled
Rajagopal 2016 patellar follower (patellar_tracking_analysis.py). Built from computed coordinates in an empty scene:
femur, tibia, fibula and patella sticks plus the patellar ligament (red). Orthographic lateral view from +X. Nothing is
saved except the PNGs; no project blend is opened or modified.

  python3.13 render_patella_follower.py --osim Rajagopal2016.osim --out DIR
"""
import argparse, json, math, sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import patellar_tracking_analysis as pta  # noqa: E402
from opensim_model_geometry import Model  # noqa: E402
import joint_solver as js  # noqa: E402

ANGLES = (0, 60, 120)


def stick(name, a, b, r, rgba, coll):
    a, b = Vector(a), Vector(b); d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=d.length, location=(a + b) / 2)
    ob = bpy.context.active_object; ob.name = name
    ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = d.to_track_quat('Z', 'Y')
    m = bpy.data.materials.new(name); m.diffuse_color = rgba; ob.data.materials.append(m)
    for c in ob.users_collection:
        c.objects.unlink(ob)
    coll.objects.link(ob)
    return ob


def poses(osim):
    rec = json.loads(pta.C004.read_text()); B = rec['bones']; J = rec['joint_markers']
    raj, flen = pta.rajagopal(osim)
    pta.rajagopal.osim = osim
    c = pta.c004(raj, flen)
    hjc, kjc = np.array(B['femur_left']['head_m']), np.array(B['femur_left']['tail_m'])
    s = c['femur_scale_c004_over_rajagopal']
    zax = np.array(J['tibiofemoral_left']['frame_axes_columns_XYZ'])[:, 2]; sgn = c['flexion_sign_about_marker_Z']
    sup = (hjc - kjc) / np.linalg.norm(hjc - kjc)
    ant = np.array([0, -1.0, 0]) - sup * (np.array([0, -1.0, 0]) @ sup); ant /= np.linalg.norm(ant)
    to_h = lambda v: s * (v[0] * ant + v[1] * sup)
    ph, pt = np.array(B['patella_left']['head_m']), np.array(B['patella_left']['tail_m'])
    r0 = raj[0]
    lig0 = to_h(np.array(r0['tibia_point_in_femur_m']) - np.array(r0['patella_point_in_femur_m']))
    ins0 = pt + lig0
    out = {}
    for a in ANGLES:
        R = js.rot(zax, sgn * a)
        tib = [kjc + R @ (np.array(B['tibia_left'][e]) - kjc) for e in ('head_m', 'tail_m')]
        fib = [kjc + R @ (np.array(B['fibula_left'][e]) - kjc) for e in ('head_m', 'tail_m')]
        ins = kjc + R @ (ins0 - kjc)
        r = next(x for x in raj if x['knee_deg'] == a)
        dpole = to_h(np.array(r['patella_point_in_femur_m']) - np.array(r0['patella_point_in_femur_m']))
        # patella flexion relative to the femur from the model (rotation about the femur's ML axis)
        m = Model(osim); m.coords['knee_angle_l'] = math.radians(a); m.coords['knee_angle_l_beta'] = math.radians(a)
        Rp = (np.linalg.inv(m.body_world('femur_l')) @ m.body_world('patella_l'))[:3, :3]
        m0 = Model(osim); Rp0 = (np.linalg.inv(m0.body_world('femur_l')) @ m0.body_world('patella_l'))[:3, :3]
        rel = Rp @ Rp0.T; ang = math.degrees(math.atan2(rel[1, 0], rel[0, 0]))       # rotation about the model z (ML) axis
        Rpat = js.rot(zax, math.copysign(abs(ang), sgn))          # patella flexes in the same sense as the tibia
        pole_f = pt + dpole
        fh = pole_f + Rpat @ (ph - pt)
        out[a] = {'tibia': tib, 'fibula': fib, 'insertion': ins, 'static': (ph, pt), 'follower': (fh, pole_f),
                  'lig_static_mm': float(np.linalg.norm(ins - pt) * 1000), 'lig_follower_mm': float(np.linalg.norm(ins - pole_f) * 1000),
                  'patella_rotation_deg': ang}
    return B, hjc, kjc, out


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser(); ap.add_argument('--osim', required=True); ap.add_argument('--out', required=True)
    o = ap.parse_args(argv)
    outdir = Path(o.out); outdir.mkdir(parents=True, exist_ok=True)
    B, hjc, kjc, P = poses(o.osim)
    meta = {}
    for variant in ('static', 'follower'):
        for a in ANGLES:
            bpy.ops.wm.read_factory_settings(use_empty=True)
            sc = bpy.context.scene; coll = sc.collection
            sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
            sc.render.resolution_x = sc.render.resolution_y = 700; sc.render.film_transparent = False
            sc.world = bpy.data.worlds.new('w'); sc.world.color = (0.95, 0.95, 0.93)
            bone = (0.25, 0.65, 0.65, 1); pat = (0.95, 0.6, 0.15, 1); lig = (0.85, 0.1, 0.1, 1)
            stick('femur', hjc, kjc, 0.007, bone, coll)
            stick('tibia', *P[a]['tibia'], 0.007, bone, coll)
            stick('fibula', *P[a]['fibula'], 0.004, (0.35, 0.55, 0.55, 1), coll)
            ph, pt = P[a][variant]
            stick('patella', ph, pt, 0.006, pat, coll)
            stick('ligament', pt, P[a]['insertion'], 0.0025, lig, coll)
            cam_d = bpy.data.cameras.new('cam'); cam_d.type = 'ORTHO'; cam_d.ortho_scale = 0.36
            cam = bpy.data.objects.new('cam', cam_d); coll.objects.link(cam); sc.camera = cam
            target = Vector(kjc) + Vector((0, 0.03, -0.02))
            cam.location = target + Vector((1.0, 0, 0))
            cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = (target - cam.location).to_track_quat('-Z', 'Y')
            p = outdir / f'knee_{variant}_{a:03d}.png'
            sc.render.filepath = str(p); bpy.ops.render.render(write_still=True)
            meta[p.name] = {'variant': variant, 'knee_deg': a, 'ligament_mm': round(P[a][f'lig_{variant}_mm'], 2),
                            'patella_rotation_deg_model': round(P[a]['patella_rotation_deg'], 2) if variant == 'follower' else 0.0}
    (outdir / 'renders_meta.json').write_text(json.dumps({'blender_version': bpy.app.version_string, 'view': 'orthographic lateral from +X, scale 0.36 m',
                                                          'renders': meta}, indent=1) + '\n')
    print(json.dumps(meta))


if __name__ == '__main__':
    main()
