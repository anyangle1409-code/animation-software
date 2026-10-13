#!/usr/bin/env python3
"""ORIGINAL_v1 foot-shape candidates (Claude): mesh-only neutral toe grounding.

Defect (docs/ORIGINAL_V1_NEUTRAL_FOOT_VISUAL_REJECTION_20261012.md): the procedurally lofted toes (build_toes in
scripts/original_v1_o2_body.py) have ring centres 10-13.5 mm above the floor, so every distal digit floats 8.5-9.3 mm in
neutral and the toes read as straight, raised tubes.

Variant c2 (default; supersedes c1): skeleton-anchored plantar pulp. The 206-bone toe chains of the frozen skeleton run
almost level (MTP 22 mm -> distal phalanx tip 14-20 mm above the floor) through the middle of each skin digit, so the
digits themselves must stay where they are. Only the skin BELOW each digit's skeleton axis is expanded downwards,
smoothly (d' = d + (f - 1) D smoothstep(d / D): slope 1 at the axis, so no crease, and a near-uniform shift of the
lower half, so the pad is rounded rather than keeled), with a weight that rises (smoothstep) from the
web line to the distal phalanx head, so that the plantar pulp of every digit reaches the floor at the middle of the distal phalanx (rising
to 3 mm under the phalanx tip, so the toe tip still curves up off the floor) while the dorsal skin,
nail line and every skeleton station stay unchanged. Skeleton stations on the axis therefore remain inside the skin.

Variant c1 (REJECTED, kept for reproducibility): each digit rotated about a transverse floor axis at y0 until its lowest
vertex reached the floor. verify_original_foot_shape_candidate_blender.py found the distal phalanx tips of toes 2-5
outside the bent skin: the bend lowers the whole digit below its frozen skeleton.

Common to both: root/web vertices take a Gaussian (in X) mix of the neighbouring digits; vertices never go below the floor;
the +X foot is computed and mirrored exactly to the -X foot (topology mirror map verified); every shape-key block receives
the same displacement (inherited relative corrective deltas preserved).
Not changed: topology, vertex groups/weights, both armatures (206 source, 67 runtime), object transforms, modifiers, any
vertex outside the forefoot box, foot length, ankle, heel, height.
NOT addressed (recorded, not hidden): foot length 309 mm (shortening blocked by the skeleton forefoot chain, see
docs/ORIGINAL_V1_FOOT_SOURCE_AUDIT_CLAUDE_20261013.md), toe girth/tubular cross-sections, nails (no nail geometry exists),
individual toe articulation (one runtime toe control per foot).

  python3.13 build_original_foot_shape_candidate_blender.py --blend PARENT.blend --expect-sha SHA --out NEW.blend --report JSON [--variant c2|c1]
"""
import argparse, hashlib, json, math, sys
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree

BODY = 'HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE'
MASTER = 'HGPT_ANATOMICAL_MASTER'
Y0 = -0.190            # c1 bend line (m); also bounds the edited box
BLEND = 0.025          # c1 smoothstep length of the bend ramp (m)
DIGIT_CUT = -0.215     # anterior of this, the five digits are separate connected components
SIGMA_X = 0.006        # Gaussian width for root/web digit mixing (m)
PULP_W0 = -0.200       # c2: pulp weight starts at this y (web line)
BIN = 0.002            # c2: y bin for the plantar profile (m)
TIP_LIFT = 0.003       # c2: pulp target rises from the floor at the pad centre to this height at the distal phalanx tip (m)
TIP_FADE = 0.85       # c2: fraction of the pulp expansion removed between the phalanx tip and the skin tip
MIN_D = 0.003          # c2: only skin at least this far below the axis profile is a plantar surface to expand (m)
BOX = {'xmin': 0.02, 'zmax': 0.07, 'ymax': Y0 + 0.002}
CHAINS = [['hallux_proximal_phalanx', 'hallux_distal_phalanx']] + \
         [[f'toe{k}_proximal_phalanx', f'toe{k}_middle_phalanx', f'toe{k}_distal_phalanx'] for k in (2, 3, 4, 5)]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def smooth(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def bend(p, theta):
    """Rotate p about the X axis through (y0, z = 0) so that anterior points descend (theta > 0)."""
    dy, dz = p.y - Y0, p.z
    c, s = math.cos(theta), math.sin(theta)
    return Vector((p.x, Y0 + dy * c - dz * s, dy * s + dz * c))


def root_bend(P, region, comps, weights):
    """c1 (rejected)."""
    def ramp(p):
        return smooth((Y0 - p.y) / BLEND)
    theta = []
    for c in comps:
        lo, hi = 0.0, math.radians(30)
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            zmin = min(bend(P[i], mid * ramp(P[i])).z for i in c)
            lo, hi = (mid, hi) if zmin > 0 else (lo, mid)
        theta.append(hi)
    disp = {}
    for i in region:
        r = ramp(P[i])
        if r <= 0:
            continue
        new = Vector((0, 0, 0))
        for k, wk in weights(i).items():
            new += wk * bend(P[i], theta[k] * r)
        new.z = max(new.z, 0.0)
        d = new - P[i]
        if d.length > 1e-9:
            disp[i] = d
    return disp, {'bend_line_y_m': Y0, 'ramp_m': BLEND, 'digit_bend_deg': [round(math.degrees(t), 3) for t in theta]}


def pulp(P, region, comps, weights, centre_x):
    """c2: expand the skin below each digit's skeleton axis so that the plantar pulp reaches the floor."""
    master = bpy.data.objects[MASTER]
    bones = {b.name[5:] if b.name.startswith('anat_') else b.name: b for b in master.data.bones}
    Mw = master.matrix_world
    axes, pad_y, tip_y = [], [], []
    for k, chain in enumerate(CHAINS):
        side = [s for s in ('_left', '_right') if (Mw @ bones[chain[0] + s].head_local).x > 0][0]
        pts = [Mw @ bones[chain[0] + side].head_local] + [Mw @ bones[n + side].tail_local for n in chain]
        assert abs(pts[-1].x - centre_x[k]) < 0.012, (chain, pts[-1].x, centre_x[k])
        axes.append([(p.y, p.z) for p in pts])                       # y decreasing (anterior)
        dh, dt = Mw @ bones[chain[-1] + side].head_local, Mw @ bones[chain[-1] + side].tail_local
        pad_y.append(0.5 * (dh.y + dt.y))                             # pad centre: middle of the distal phalanx
        tip_y.append(dt.y)

    def axis_z(k, y):
        a = axes[k]
        if y >= a[0][0]:
            return a[0][1]
        for (y1, z1), (y2, z2) in zip(a, a[1:]):
            if y2 <= y <= y1:
                return z1 + (z2 - z1) * (y - y1) / (y2 - y1)
        return a[-1][1]
    member = {i: k for k, c in enumerate(comps) for i in c}
    bot = [dict() for _ in comps]
    for i in region:                                                  # plantar minimum per digit, 2 mm bins
        if P[i].y >= PULP_W0 + 0.004:
            continue
        k = member.get(i)
        if k is None:
            k = min(range(len(centre_x)), key=lambda q: abs(P[i].x - centre_x[q]))
            if abs(P[i].x - centre_x[k]) > 0.004:
                continue
        key = round(P[i].y / BIN)
        bot[k][key] = min(bot[k].get(key, 1.0), P[i].z)

    def bottom(k, y):
        key = round(y / BIN); b = bot[k]
        return b[key] if key in b else b[min(b, key=lambda q: abs(q - key))]

    mesh_tip_y = [min(P[i].y for i in c) for c in comps]

    def w_of(k, y):
        w = smooth((PULP_W0 - y) / (PULP_W0 - pad_y[k]))
        if y < tip_y[k]:                                              # beyond the phalanx tip the pulp wraps up into the
            w *= 1.0 - TIP_FADE * smooth((tip_y[k] - y) / max(tip_y[k] - mesh_tip_y[k], 1e-4))   # rounded tip
        return w

    def target(k, y):
        if y >= pad_y[k]:
            return 0.0
        return TIP_LIFT * min(1.0, (pad_y[k] - y) / (pad_y[k] - tip_y[k]))
    disp = {}
    for i in region:
        p = P[i]
        if p.y >= PULP_W0:
            continue
        new_z = 0.0
        for k, wk in weights(i).items():
            za = axis_z(k, p.y); d = za - p.z
            if d <= 0:
                new_z += wk * p.z; continue
            D = za - bottom(k, p.y)
            if D < MIN_D:
                new_z += wk * p.z; continue
            f = max(1.0, 1.0 + w_of(k, p.y) * ((za - target(k, p.y)) / D - 1.0))
            new_z += wk * (za - (d + (f - 1.0) * D * smooth(d / D)))
        new_z = max(new_z, 0.0)
        if abs(new_z - p.z) > 1e-9:
            disp[i] = Vector((0.0, 0.0, new_z - p.z))
    return disp, {'pulp_weight_start_y_m': PULP_W0, 'tip_lift_m': TIP_LIFT, 'tip_fade': TIP_FADE, 'min_plantar_depth_m': MIN_D,
                  'distal_tip_y_m_plusX': [round(y, 4) for y in tip_y], 'pad_full_weight_y_m_plusX': [round(y, 4) for y in pad_y],
                  'skeleton_axis_points_yz_m_plusX': [[[round(a, 4), round(b, 4)] for a, b in ax] for ax in axes]}


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    for a in ('--blend', '--expect-sha', '--out', '--report'):
        ap.add_argument(a, required=True)
    ap.add_argument('--variant', choices=('c1', 'c2'), default='c2')
    o = ap.parse_args(argv)
    if Path(o.out).exists():
        raise FileExistsError(o.out)
    parent_sha = sha(o.blend)
    if parent_sha != o.expect_sha:
        raise SystemExit(f'parent SHA mismatch {parent_sha}')
    bpy.ops.wm.open_mainfile(filepath=str(Path(o.blend).resolve()))
    body = bpy.data.objects[BODY]; me = body.data
    W = body.matrix_world; Wi = W.inverted()
    P = [W @ v.co for v in me.vertices]
    kd = KDTree(len(P))
    for i, p in enumerate(P):
        kd.insert(p, i)
    kd.balance()
    mirror, worst = {}, 0.0
    for i, p in enumerate(P):
        _, j, d = kd.find(Vector((-p.x, p.y, p.z)))
        mirror[i] = j; worst = max(worst, d)
    assert worst < 1e-6, f'body not mirror-symmetric within 1e-6 m ({worst})'
    adj = defaultdict(set)
    for e in me.edges:
        a, b = e.vertices; adj[a].add(b); adj[b].add(a)
    region = [i for i, p in enumerate(P) if p.x > BOX['xmin'] and p.z < BOX['zmax'] and p.y < BOX['ymax']]
    digits_set = {i for i in region if P[i].y < DIGIT_CUT}
    comps, seen = [], set()
    for s in digits_set:
        if s in seen:
            continue
        st, c = [s], []; seen.add(s)
        while st:
            u = st.pop(); c.append(u)
            for w in adj[u]:
                if w in digits_set and w not in seen:
                    seen.add(w); st.append(w)
        comps.append(c)
    comps.sort(key=lambda c: sum(P[i].x for i in c) / len(c))
    assert len(comps) == 5, f'expected five digits, found {len(comps)}'
    centre_x = [sum(P[i].x for i in c) / len(c) for c in comps]
    member = {i: k for k, c in enumerate(comps) for i in c}

    def weights(i):
        if i in member:
            return {member[i]: 1.0}
        g = [math.exp(-0.5 * ((P[i].x - cx) / SIGMA_X) ** 2) for cx in centre_x]
        s = sum(g) or 1.0
        return {k: v / s for k, v in enumerate(g)}
    if o.variant == 'c2':
        disp, info = pulp(P, region, comps, weights, centre_x)
    else:
        disp, info = root_bend(P, region, comps, weights)
    full = dict(disp)
    for i, d in disp.items():
        full[mirror[i]] = Vector((-d.x, d.y, d.z))
    keys = me.shape_keys.key_blocks if me.shape_keys else []
    for i, d in full.items():
        dl = Wi.to_3x3() @ d
        me.vertices[i].co += dl
        for kb in keys:
            kb.data[i].co += dl
    me.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(o.out).resolve()), copy=False)
    rep = {'schema_version': 1, 'candidate': f'ORIGINAL_V1_FOOT_SHAPE_{o.variant.upper()}_CLAUDE', 'variant': o.variant,
           'status': 'REVIEW_CANDIDATE_NOT_ACCEPTED' if o.variant == 'c2' else 'REJECTED_SKELETON_CONTAINMENT',
           'parent': {'path': Path(o.blend).name, 'sha256': parent_sha}, 'output': {'path': Path(o.out).name, 'sha256': sha(o.out)},
           'body_object': BODY, 'parameters': {'digit_cut_y_m': DIGIT_CUT, 'root_mix_sigma_x_m': SIGMA_X, 'box': BOX},
           'digit_centres_x_mm_plusX_foot': [round(x * 1000, 1) for x in centre_x], 'variant_info': info,
           'changed_vertices': len(full), 'changed_vertices_per_foot': len(disp),
           'max_displacement_mm': round(max(d.length for d in full.values()) * 1000, 3),
           'shape_keys_updated': [kb.name for kb in keys], 'mirror_map_max_error_m': worst}
    Path(o.report).write_text(json.dumps(rep, indent=1) + '\n')
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
