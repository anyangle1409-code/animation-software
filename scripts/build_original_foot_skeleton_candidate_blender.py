#!/usr/bin/env python3
"""ORIGINAL_v1 foot SKELETON-revision candidate C3 (Claude): re-partition the foot length around a fixed ankle.

Owner instruction 13 Oct 2026: "continue with skeleton" (answering: revise the frozen foot skeleton towards ~280 mm?).
This builds a REVIEW CANDIDATE for sign-off on a new file; the frozen skeleton in a003 is not touched.

Evidence (docs/ORIGINAL_V1_FOOT_SKELETON_C3_CLAUDE_20261013.md):
  * ANSUR II male at 1.82 m (OLS on stature, n = 4,082): foot length 279.9 +/- 9.1 mm, ball-of-foot length (heel to
    1st MTP) 207.4 +/- 7.8 mm.  a003: 309.2 and 229.2 mm.
  * Heel behind the ankle: a003 heel skin is only 38 mm behind the ankle-joint centre (AJC) while the AJC->MTP1 span is
    191 mm. Rajagopal2016 / Delp-lineage OpenSim foot (repo-recorded source, SHA 3f5c5f23...) puts the posterior heel
    marker 73.8 mm behind and the MTP axis 130 mm in front of the ankle (generic 1.70 m); a secondary foot-anthropometry
    ratio puts pternion->lateral malleolus at ~0.18 FL (~50 mm). HEEL_BEHIND_AJC = 60 mm is a provisional central value
    (band 50-72 mm, recorded; parameter --heel-behind-ajc-mm).
  * Metatarsal lengths are kept (stature-aware Spain/Portugal regressions support a003 M1/M2: committed
    canonical_foot_proportion_audit_v1.json); the metatarsals are translated, not scaled.
  * The tarsal sticks are schematic (canonical_tarsal_geometry_audit_v1.json); the AJC->TMT midfoot span is compressed so
    that MTP1 lands at heel - 207.4 mm; the subtalar joint station and the ankle are kept (talus decision
    KEEP_ANKLE_SUBTALAR_JOINTS_PROVISIONAL).
  * Phalanges are scaled about their MTP so that the hallux tip lands at heel - 279.9 mm (soft-tissue tip allowance kept).

Mapping (applied identically to the 206-bone master, the 67-joint runtime foot/toe controls, the bone-parented joint and
landmark empties, and the skin; mirrored exactly; z is never changed, so floor contact and arch heights are kept):
  anterior (y < y_AJC): per ray k (x interpolated between the five rays): y_AJC fixed; TMT_k and MTP_k translated by DELTA
     (posterior); between AJC and TMT linear; anterior of MTP scaled by S_TOE about the moved MTP.
  posterior (y > y_STJ): stretched linearly so the heel skin lands HEEL_BEHIND_AJC behind the AJC; the calcaneus
     posterior station keeps its soft-tissue distance to the heel skin.
  skin: the foot is REGENERATED from the O2 body generator (scripts/original_v1_foot_regen.py), whose foot output equals
     the a003 foot vertex-for-vertex: the forefoot sections and toe split are moved with the same per-ray knots (anchored
     at the shin's anterior skin line, so the dorsum never passes behind the shin), the toe tips with the skeleton toe
     map and a uniform toe-length factor solved so the toe tip lands at heel - ANSUR foot length; the heel is then
     lengthened by a smooth backward translation (smoothstep from the subtalar station to the heel; full below 40 mm,
     fading to none at 140 mm, so the lower Achilles slopes into the heel) solved so the heel skin lands
     HEEL_BEHIND_AJC behind the AJC. (Growing the generator's heel fan radially was rejected: it drives the heel below
     the floor and the generator then re-grounds the whole lower leg.) A first attempt that remapped the
     existing skin coordinates directly was rejected (pointed heel spur, fold at the front of the ankle).
  The toe pulp (C2) must be re-applied afterwards with build_original_foot_shape_candidate_blender.py against the new
  toe skeleton.
Not changed: topology, vertex groups/weights, shape-key relative deltas, every bone outside the feet, stature, ankle
height, foot breadth; skin above the ankle changes only through the generator's subdivision smoothing (reported).

  python3.13 build_original_foot_skeleton_candidate_blender.py --blend a003.blend --expect-sha SHA --out C3.blend --report JSON
       [--heel-behind-ajc-mm 60]
"""
import argparse, hashlib, json, math, sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree

BODY = 'HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE'
RIG = 'HGPT_CANONICAL_V4_ORIGINAL'
MASTER = 'HGPT_ANATOMICAL_MASTER'
ANSUR_FOOT = 0.2799
ANSUR_BALL = 0.2074
RAYS = [('metatarsal_1', ['hallux_proximal_phalanx', 'hallux_distal_phalanx']),
        ('metatarsal_2', ['toe2_proximal_phalanx', 'toe2_middle_phalanx', 'toe2_distal_phalanx']),
        ('metatarsal_3', ['toe3_proximal_phalanx', 'toe3_middle_phalanx', 'toe3_distal_phalanx']),
        ('metatarsal_4', ['toe4_proximal_phalanx', 'toe4_middle_phalanx', 'toe4_distal_phalanx']),
        ('metatarsal_5', ['toe5_proximal_phalanx', 'toe5_middle_phalanx', 'toe5_distal_phalanx'])]
HZ = (0.040, 0.140)     # heel translation: full below HZ[0], none above HZ[1] (smoothstep)
FOOT_BONES = {'talus', 'calcaneus', 'navicular', 'cuboid', 'medial_cuneiform', 'intermediate_cuneiform', 'lateral_cuneiform'} | \
    {m for m, _ in RAYS} | {p for _, ps in RAYS for p in ps}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def smooth(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def strip(n):
    return n[5:] if n.startswith('anat_') else n


class FootMap:
    """Exact per-ray piecewise-linear y map for the +X foot (use |x|; mirror the result)."""

    def __init__(self, rays, y_ajc, y_stj, heel_y, heel_new, delta, s_toe):
        self.r = sorted(rays)                    # (x_mtp, y_tmt, y_mtp)
        self.y_ajc, self.y_stj, self.heel_y, self.heel_new, self.delta, self.s_toe = y_ajc, y_stj, heel_y, heel_new, delta, s_toe

    def knots(self, ax):
        r = self.r
        if ax <= r[0][0]:
            return r[0][1], r[0][2]
        if ax >= r[-1][0]:
            return r[-1][1], r[-1][2]
        for a, b in zip(r, r[1:]):
            if a[0] <= ax <= b[0]:
                t = (ax - a[0]) / (b[0] - a[0])
                return a[1] + t * (b[1] - a[1]), a[2] + t * (b[2] - a[2])

    def y(self, ax, y):
        if y > self.y_stj:
            return self.y_stj + (y - self.y_stj) * (self.heel_new - self.y_stj) / (self.heel_y - self.y_stj)
        if y >= self.y_ajc:
            return y
        tmt, mtp = self.knots(ax)
        if y >= tmt:
            return self.y_ajc + (y - self.y_ajc) * (tmt + self.delta - self.y_ajc) / (tmt - self.y_ajc)
        if y >= mtp:
            return y + self.delta
        return mtp + self.delta + (y - mtp) * self.s_toe


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    for a in ('--blend', '--expect-sha', '--out', '--report'):
        ap.add_argument(a, required=True)
    ap.add_argument('--heel-behind-ajc-mm', type=float, default=60.0)
    o = ap.parse_args(argv)
    if Path(o.out).exists():
        raise FileExistsError(o.out)
    parent_sha = sha(o.blend)
    if parent_sha != o.expect_sha:
        raise SystemExit(f'parent SHA mismatch {parent_sha}')
    bpy.ops.wm.open_mainfile(filepath=str(Path(o.blend).resolve()))
    body, rig, master = (bpy.data.objects[n] for n in (BODY, RIG, MASTER))
    for ob in (body, rig, master):
        assert ob.matrix_world == Matrix.Identity(4), f'{ob.name} has a non-identity transform'
    me = body.data
    P = [v.co.copy() for v in me.vertices]
    zmin = min(p.z for p in P)
    bones = {strip(b.name): b for b in master.data.bones}

    def station(n, end):
        b = bones[n + '_left']        # anatomical left = +X in HGPT
        p = b.head_local if end == 'head' else b.tail_local
        assert p.x > 0, n
        return p.copy()
    y_ajc = bpy.data.objects['LM_tibia_left__AJC'].matrix_world.translation.y
    y_stj = station('calcaneus', 'head').y                               # subtalar posterior joint station
    foot = [p for p in P if p.x > 0.02 and p.z < zmin + 0.16]
    heel_y = max(p.y for p in foot); tip_y = min(p.y for p in foot)
    heel_new = y_ajc + o.heel_behind_ajc_mm / 1000.0
    mtp1 = station('metatarsal_1', 'tail')
    delta = (heel_new - ANSUR_BALL) - mtp1.y                             # metatarsal translation (posterior, > 0)
    s_toe = ((heel_new - ANSUR_FOOT) - (mtp1.y + delta)) / (tip_y - mtp1.y)
    rays = [(station(m, 'tail').x, station(m, 'head').y, station(m, 'tail').y) for m, _ in RAYS]
    F = FootMap(rays, y_ajc, y_stj, heel_y, heel_new, delta, s_toe)
    calc_post = station('calcaneus', 'tail')
    calc_soft = heel_y - calc_post.y                                     # soft tissue behind the calcaneus station (kept)

    def bone_point(name, end, p):
        ax, sg = abs(p.x), (1 if p.x > 0 else -1)
        base = strip(name)
        for sfx in ('_left', '_right'):
            if base.endswith(sfx):
                base = base[:-len(sfx)]
        if base == 'calcaneus' and end == 'tail':
            ny = heel_new - calc_soft
        elif base.startswith('metatarsal'):
            ny = p.y + delta
        else:
            ray = [k for k, (m, ps) in enumerate(RAYS) if base in ps]
            if ray:
                k = ray[0]; mtp = station(RAYS[k][0], 'tail')
                ny = mtp.y + delta + (p.y - mtp.y) * s_toe
            else:
                ny = F.y(ax, p.y)
        return Vector((p.x, ny, p.z)), sg

    # --- targets for master bones (both feet), computed before editing
    targets = {}
    for b in master.data.bones:
        base = strip(b.name)
        for sfx in ('_left', '_right'):
            if base.endswith(sfx) and base[:-len(sfx)] in FOOT_BONES:
                h, _ = bone_point(b.name, 'head', b.head_local)
                t, _ = bone_point(b.name, 'tail', b.tail_local)
                targets[b.name] = (h, t)
    # runtime foot/toe controls
    rtargets = {}
    for b in rig.data.bones:
        if b.name in ('foot_l', 'foot_r', 'toe_l', 'toe_r'):
            mapped = [Vector((p.x, F.y(abs(p.x), p.y) if p.y < y_ajc else p.y, p.z)) for p in (b.head_local, b.tail_local)]
            if b.name.startswith('foot_'):
                mapped[0] = b.head_local.copy()                          # the ankle pivot never moves
            rtargets[b.name] = tuple(mapped)
    # bone-parented empties in the foot
    etargets = {}
    for ob in bpy.data.objects:
        if ob.type == 'EMPTY' and ob.parent is master and ob.parent_bone and strip(ob.parent_bone).rsplit('_', 1)[0] in FOOT_BONES | {'tibia', 'fibula'}:
            p = ob.matrix_world.translation
            if p.z < 0.13 and abs(p.x) > 0.02:
                m = ob.matrix_world.copy(); m.translation = Vector((p.x, F.y(abs(p.x), p.y), p.z))
                etargets[ob.name] = m
    # --- skin: regenerate the foot from the O2 generator with re-proportioned constants (see original_v1_foot_regen.py)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import numpy as np
    import original_v1_foot_regen as R
    g = R.g
    shin = [p for p in P if 0.06 < p.x < 0.13 and 0.115 < p.z < 0.135]
    y_sf = min(p.y for p in shin)                                        # shin anterior skin line just above the ankle

    def ant(ax, y):                                                      # skin knots anchored at the shin front line
        if y >= y_sf:
            return y
        tmt, mtp = F.knots(ax)
        if y >= tmt:
            return y_sf + (y - y_sf) * (tmt + delta - y_sf) / (tmt - y_sf)
        return F.y(ax, y)
    V0 = R.build_vertices()
    Pa = np.array([tuple(p) for p in P])
    sec = [-ant(s_[1][0], -s_[0]) for s_ in R.ORIGINAL['FOOT_SECTIONS']]
    fan_end_f = g.FOOT_PIVOT[1]
    sec[0] = max(sec[0], 0.5 * (fan_end_f + sec[1]))                     # keep ring spacing behind the first section
    lx_mid = sum(g.TOE_D_LX) / len(g.TOE_D_LX)
    split = -F.y(lx_mid, -R.ORIGINAL['TOE_SPLIT_F'])
    tips = [-F.y(0.5 * (g.TOE_D_LX[a_] + g.TOE_D_LX[b_]), -t) for (a_, b_), t in zip(g.TOE_SPANS, R.ORIGINAL['TOE_TIPS_F'])]
    params, V1, metrics, toe_k = R.solve_tip(heel_new - ANSUR_FOOT, sec, split, tips, y_ajc)
    assert abs(float(V1[:, 2].min()) - float(V0[:, 2].min())) < 1e-9, 'regenerated body changed its floor'
    # heel: smooth backward translation of the posterior foot (translation profile in y, long fade in z), solved so the
    # heel skin lands exactly HEEL_BEHIND_AJC behind the AJC
    sel = (np.abs(V1[:, 0]) > 0.02) & (V1[:, 1] > y_stj) & (V1[:, 2] < HZ[1])
    heel_y0 = float(V1[(V1[:, 0] > 0.02) & (V1[:, 2] < zmin + 0.16), 1].max())
    prof = np.zeros(len(V1))
    t = np.clip((V1[sel, 1] - y_stj) / (heel_y0 - y_stj), 0, 1)
    tz = np.clip((V1[sel, 2] - HZ[0]) / (HZ[1] - HZ[0]), 0, 1)
    prof[sel] = (t * t * (3 - 2 * t)) * (1 - tz * tz * (3 - 2 * tz))
    lo, hi = 0.0, 0.08
    footm = (V1[:, 0] > 0.02) & (V1[:, 2] < zmin + 0.16)
    for _ in range(50):
        D = 0.5 * (lo + hi)
        lo, hi = (D, hi) if float((V1[footm, 1] + D * prof[footm]).max()) < heel_new else (lo, D)
    D = hi
    V1 = V1.copy(); V1[:, 1] += D * prof
    metrics = R.foot_metrics(V1, y_ajc)
    dV = V1 - V0
    ch = np.where(np.linalg.norm(dV, axis=1) > 1e-9)[0]
    pre = float(np.abs(Pa[ch] - V0[ch]).max())
    assert pre < 1e-5, f'parent differs from the generator where the foot is regenerated ({pre} m): refuse to overwrite'
    assert (np.abs(V0[ch, 0]) > 0.02).all()
    disp = {int(i): Vector(dV[i]) for i in ch}
    regen = {'generator_params': params, 'heel_translation_mm': round(D * 1000, 3), 'heel_fade_z_m': HZ, 'toe_length_factor_solved': toe_k, 'generator_foot_metrics': metrics,
             'skin_anterior_anchor_y_mm': round(y_sf * 1000, 3), 'parent_vs_generator_max_diff_m': pre,
             'changed_vertex_max_z_m': float(V0[ch, 2].max()),
             'max_displacement_above_150mm_m': float(np.linalg.norm(dV[ch][V0[ch, 2] > 0.15], axis=1).max()) if (V0[ch, 2] > 0.15).any() else 0.0}
    keys = me.shape_keys.key_blocks if me.shape_keys else []
    for i, d in disp.items():
        me.vertices[i].co += d
        for kb in keys:
            kb.data[i].co += d
    me.update()
    # --- armatures (edit mode); rolls preserved
    for arm, tg in ((master, targets), (rig, rtargets)):
        bpy.context.view_layer.objects.active = arm
        for ob in bpy.context.view_layer.objects:
            ob.select_set(ob is arm)
        bpy.ops.object.mode_set(mode='EDIT')
        for name, (h, t) in tg.items():
            eb = arm.data.edit_bones[name]; roll = eb.roll
            eb.head = h; eb.tail = t; eb.roll = roll
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()
    for name, m in etargets.items():
        bpy.data.objects[name].matrix_world = m
    bpy.context.view_layer.update()
    err = max((bpy.data.objects[n].matrix_world.translation - m.translation).length for n, m in etargets.items())
    assert err < 1e-6, err
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(o.out).resolve()), copy=False)
    Pn = [v.co for v in me.vertices]
    footn = [p for p in Pn if p.x > 0.02 and p.z < zmin + 0.16]
    rep = {'schema_version': 1, 'candidate': 'ORIGINAL_V1_FOOT_SKELETON_C3_CLAUDE', 'status': 'REVIEW_CANDIDATE_NOT_ACCEPTED_SKELETON_CHANGE_NEEDS_OWNER_SIGNOFF',
           'parent': {'path': Path(o.blend).name, 'sha256': parent_sha}, 'output': {'path': Path(o.out).name, 'sha256': sha(o.out)},
           'parameters': {'heel_behind_ajc_mm': o.heel_behind_ajc_mm, 'ansur_foot_length_mm': ANSUR_FOOT * 1000, 'ansur_ball_of_foot_mm': ANSUR_BALL * 1000},
           'derived': {'y_ajc_mm': round(y_ajc * 1000, 3), 'y_subtalar_station_mm': round(y_stj * 1000, 3),
                       'heel_y_mm_before_after': [round(heel_y * 1000, 2), round(heel_new * 1000, 2)],
                       'metatarsal_translation_mm': round(delta * 1000, 3), 'toe_scale': round(s_toe, 5),
                       'midfoot_scale_per_ray': [round((t + delta - y_ajc) / (t - y_ajc), 4) for _, t, _ in sorted(rays)],
                       'calcaneus_posterior_soft_tissue_mm': round(calc_soft * 1000, 2)},
           'result_plusX_foot_mm': {'length': round((max(p.y for p in footn) - min(p.y for p in footn)) * 1000, 2),
                                    'breadth': round((max(p.x for p in footn) - min(p.x for p in footn)) * 1000, 2),
                                    'heel_behind_ajc': round((max(p.y for p in footn) - y_ajc) * 1000, 2)},
           'skin_regeneration': regen,
           'changed': {'vertices': len(disp), 'master_bones': sorted(targets), 'runtime_bones': sorted(rtargets), 'empties': sorted(etargets)},
           'shape_keys_updated': [kb.name for kb in keys]}
    Path(o.report).write_text(json.dumps(rep, indent=1) + '\n')
    print(json.dumps({k: v for k, v in rep.items() if k != 'changed'}, indent=1), 'changed counts',
          {k: len(v) if isinstance(v, list) else v for k, v in rep['changed'].items()})


if __name__ == '__main__':
    main()
