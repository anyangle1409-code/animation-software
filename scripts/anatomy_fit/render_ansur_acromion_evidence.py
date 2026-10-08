#!/usr/bin/env python3
"""Evidence renders for the ANSUR acromion correspondence audit (bpy). Read-only: opens the c001 audit blend, adds
review-only geometry in memory, renders, never saves.

Shown (both sides, mirrored): the reconciled c001 girdle (cyan sticks); Lee LM25 (red) and LM27 (orange); the two
trapezius-clavicle line constructions (white: clavicle-axis line; grey: lateral line through AC) and their crossings
of the LM25-LM27 lateral border (green / blue); a translucent plane at the ANSUR acromial height 1497.7 mm (magenta)
and a thin plane at the retained a003 jugular notch (yellow); ghost girdles (clavicle + scapula outline) for the
least-departure pose meeting the absolute ANSUR height (red, infeasible: clavicle -6.6 deg) and the pose meeting the
ANSUR within-subject relation (green). World mapping: bony thorax pitch, IJ at the a003 bony IJ (as c001).

  python3    render_ansur_acromion_evidence.py geometry --out GEOM.json     (numpy/scipy; no bpy)
  python3.13 render_ansur_acromion_evidence.py render --blend C001.blend --geometry GEOM.json --out DIR   (bpy only)
"""
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

BODY = 'HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE'
VARIANT = 'bony_specimen_deg__border_x_clavicle_axis_line'


def geometry(o):
    """All review geometry in world metres (both sides), computed with the audit module; written to JSON for bpy."""
    import numpy as np
    import shoulder_ansur_acromion_audit as au
    A = json.loads((au.ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/shoulder_ansur_acromion_correspondence_v1.json').read_text())
    rc = au.sgs.reconcile(1.0); P = au.sgs.pitches()['bony_specimen_deg']
    ij = np.array(json.loads(au.A003.read_text())['skeleton_input']['trunk']['ij_bone']) * 1000
    W = lambda v, side: [float(c) / 1000 for c in au.sgs.thorax_to_world(v, side, ij, P)]
    corr = au.correspondence(rc)

    def girdle(ac, Pts):
        return {side: {'SC': W(rc['SC'], side), 'AC': W(ac, side), **{f'LM{i}': W(Pts[i - 1], side) for i in (5, 7, 14, 25, 27)}}
                for side in ('left', 'right')}
    g = {'variant': VARIANT, 'c001': girdle(rc['AC'], rc['scapula_landmarks']), 'points': {}, 'ghosts': {},
         'planes_mm': {'ANSUR_acromial_1497_7': A['targets']['ANSUR_acromial_height_mm']['mean'], 'a003_IJ_notch': A['targets']['a003_IJ_z_mm']}}
    for side in ('left', 'right'):
        g['points'][side] = {k: W(v['point'], side) for k, v in corr.items()}
        g['points'][side]['line2_start'] = W(rc['AC'] - np.array([0, 0, 60.0]), side)
    rec = A['feasibility'][VARIANT]
    for tag, key in (('absolute', 'absolute_ANSUR_acromial_height'), ('within_subject', 'ANSUR_within_subject_IJ_plus_3.1')):
        s_ = rec[key]['clavicle_and_scapula_min_chi2']
        ac, Pts = au.pose_girdle(rc, s_['girdle_rotation_about_SC_deg'], s_['scapula_angles_exact_deg'])
        g['ghosts'][tag] = dict(girdle(ac, Pts), solution=s_)
    Path(o.out).write_text(json.dumps(g, indent=1) + '\n')
    print('geometry written')


def render(o):
    import bpy
    from mathutils import Vector
    from render_master_review import ball, material, stick
    out = Path(o.out); out.mkdir(parents=True, exist_ok=False)
    g = json.loads(Path(o.geometry).read_text())
    bpy.ops.wm.open_mainfile(filepath=str(Path(o.blend).resolve()))
    sc_ = bpy.context.scene
    for ob in sc_.objects:
        if ob.name != BODY:
            ob.hide_render = True
    body = bpy.data.objects[BODY]
    body.data.materials.clear(); body.data.materials.append(material('skin', (0.82, 0.78, 0.74, 1)))
    coll = bpy.data.collections.new('REVIEW_ONLY'); sc_.collection.children.link(coll)
    M = {k: material(k, c) for k, c in {'cyan': (0.1, 0.85, 0.95, 1), 'red': (0.95, 0.15, 0.1, 1), 'orange': (1.0, 0.55, 0.05, 1),
                                         'green': (0.15, 0.9, 0.25, 1), 'blue': (0.2, 0.4, 1.0, 1), 'white': (0.95, 0.95, 0.95, 1),
                                         'grey': (0.55, 0.55, 0.6, 1), 'yellow': (1.0, 0.85, 0.1, 1), 'magenta': (0.9, 0.15, 0.85, 1),
                                         'ghost_red': (0.9, 0.1, 0.1, 1), 'ghost_green': (0.1, 0.8, 0.2, 1)}.items()}

    def girdle(tag, gg, mat, r):
        for side, d in gg.items():
            if side not in ('left', 'right'):
                continue
            stick(f'{tag}_clav_{side}', d['SC'], d['AC'], r, mat, coll)
            for i, (a, b) in enumerate([(25, 5), (5, 7), (7, 25), (5, 14), (14, 25), (25, 27)]):
                stick(f'{tag}_{side}_{i}', d[f'LM{a}'], d[f'LM{b}'], r * 0.6, mat, coll)
    girdle('C001', g['c001'], M['cyan'], 0.005)
    girdle('GHOST_ABS', g['ghosts']['absolute'], M['ghost_red'], 0.003)
    girdle('GHOST_REL', g['ghosts']['within_subject'], M['ghost_green'], 0.003)
    for side, p in g['points'].items():
        c = g['c001'][side]
        ball(f'SC_{side}', c['SC'], 0.009, M['yellow'], coll); ball(f'AC_{side}', c['AC'], 0.009, M['white'], coll)
        ball(f'LM25_{side}', p['LM25_exterior_acromial_angle'], 0.007, M['red'], coll)
        ball(f'LM27_{side}', p['LM27_lateral_distal_acromial_extent'], 0.007, M['orange'], coll)
        ball(f'X1_{side}', p['border_x_clavicle_axis_line'], 0.007, M['green'], coll)
        ball(f'X2_{side}', p['border_x_lateral_line_through_AC'], 0.007, M['blue'], coll)
        stick(f'border_{side}', p['LM25_exterior_acromial_angle'], p['LM27_lateral_distal_acromial_extent'], 0.0025, M['orange'], coll)
        stick(f'line1_{side}', c['SC'], p['border_x_clavicle_axis_line'], 0.0015, M['white'], coll)
        stick(f'line2_{side}', p['line2_start'], p['border_x_lateral_line_through_AC'], 0.0015, M['grey'], coll)
    for name, z in g['planes_mm'].items():
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.0, z / 1000))
        pl = bpy.context.active_object; pl.name = name
        pl.scale = (0.55, 0.30, 0.0015 if name.startswith('ANSUR') else 0.0008)
        pl.data.materials.append(M['magenta'] if name.startswith('ANSUR') else M['yellow'])
        for c in pl.users_collection:
            c.objects.unlink(pl)
        coll.objects.link(pl)
    eng = sc_.render; eng.engine = 'BLENDER_WORKBENCH'
    sh = sc_.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_xray = True; sh.xray_alpha = 0.25
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc_.collection.objects.link(cam); sc_.camera = cam
    cam.data.type = 'ORTHO'
    views = {}
    for side, s in (('left', 1.0), ('right', -1.0)):
        c = (s * 0.17, 0.0, 1.50)
        views.update({f'{side}_front': ((c[0], -3, c[2]), c, 0.36), f'{side}_side': ((s * 3, 0, c[2]), c, 0.36),
                      f'{side}_rear': ((c[0], 3, c[2]), c, 0.36), f'{side}_overhead': ((c[0], 0.001, 4), (c[0], 0, c[2]), 0.36)})
    views['both_front'] = ((0, -3, 1.50), (0, 0, 1.50), 0.75)
    views['both_rear'] = ((0, 3, 1.50), (0, 0, 1.50), 0.75)
    for name, (loc, tgt, size) in views.items():
        cam.location = loc
        cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size
        eng.resolution_x, eng.resolution_y = (900, 900) if not name.startswith('both') else (1200, 700)
        eng.image_settings.file_format = 'PNG'; eng.filepath = str(out / f'{name}.png')
        bpy.ops.render.render(write_still=True)
    print('views', len(views))


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    g = sub.add_parser('geometry'); g.add_argument('--out', required=True)
    r = sub.add_parser('render'); r.add_argument('--blend', required=True); r.add_argument('--geometry', required=True); r.add_argument('--out', required=True)
    o = ap.parse_args(argv)
    {'geometry': geometry, 'render': render}[o.cmd](o)


if __name__ == '__main__':
    main()
