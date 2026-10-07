"""Fitted joint-marker centres/frames for all 427 articulations, plus Phase 6 verification checks.

Centres: explicitly fitted centres for the major synovial joints; otherwise the midpoint of the
closest approach between participant bone segments (sutures, intercarpal/intertarsal contacts,
facets, costal joints). Non-206 participants (costal cartilage, sternal parts, hyoid horns) use
explicit locators. Frames follow the ISB axis pattern for the marker's frame bone: X anterior,
Y proximal/superior, Z to the character's right (Wu et al. 2002/2005). Character-specific JCS
refinements remain Phase 8/9 work.
"""
import json
import math
from pathlib import Path

import numpy as np

DATA = Path(__file__).resolve().parents[2] / 'ORIGINAL_V1_WORK/anatomy'
UP = np.array([0.0, 0.0, 1.0])
ANT = np.array([0.0, -1.0, 0.0])


def unit(a):
    n = np.linalg.norm(a)
    return a / n if n > 0 else a


def segment_closest(p0, p1, q0, q1):
    """Closest points between segments p0p1 and q0q1."""
    d1, d2, r = p1 - p0, q1 - q0, p0 - q0
    a, e, f = d1 @ d1, d2 @ d2, d2 @ r
    c, b = d1 @ r, d1 @ d2
    denom = a * e - b * b
    s = np.clip((b * f - c * e) / denom, 0, 1) if denom > 1e-12 else 0.0
    t = (b * s + f) / e
    if t < 0:
        t, s = 0.0, np.clip(-c / a, 0, 1)
    elif t > 1:
        t, s = 1.0, np.clip((b - c) / a, 0, 1)
    return p0 + d1 * s, q0 + d2 * t


def host_bone(part):
    """206-bone host of a non-bone participant (sternal parts, costal cartilage, hyoid parts)."""
    if part in ('manubrium', 'sternal_body', 'xiphoid'):
        return 'sternum'
    if part.startswith('costal_cartilage_'):
        return 'rib_' + part[len('costal_cartilage_'):]
    if part.startswith('hyoid'):
        return 'hyoid'
    if part.startswith('coccygeal_component_'):
        return 'coccyx'
    if part.startswith('hallux_sesamoid_'):
        return 'metatarsal_1_' + part.rsplit('_', 1)[1]
    if part.startswith('tfcc_'):
        return 'ulna_' + part.rsplit('_', 1)[1]
    raise KeyError(part)


def bone_frame(head, tail):
    head, tail = np.asarray(head), np.asarray(tail)
    d = unit(tail - head)
    if abs(d[2]) >= 0.5:                          # vertical-ish: Y toward the superior end
        Y = d if d[2] > 0 else -d
        X = unit(ANT - (ANT @ Y) * Y)
    else:                                         # horizontal (foot/toes, ribs): X along the bone, anteriorly
        X = d if d @ ANT >= 0 else -d
        Y = unit(UP - (UP @ X) * X)
    Z = np.cross(X, Y)
    return np.stack([X, Y, Z], axis=1)            # columns X, Y, Z


def compute(bones, L, plan):
    B = {k: (np.asarray(b['head_m']), np.asarray(b['tail_m'])) for k, b in bones.items()}
    frames = plan['bone_frames']
    explicit = {}
    for s in ('left', 'right'):
        P = L['sides'][s]
        explicit.update({
            f'hip_{s}': (P['HJC'], 'Fitted HJC (Harrington PW-only / Hara mean)'),
            f'tibiofemoral_{s}': (P['KJC'], 'Fitted KJC (ISB epicondyle midpoint)'),
            f'talocrural_{s}': (P['AJC'], 'Fitted AJC (ISB malleolar midpoint at the leg-foot junction)'),
            f'glenohumeral_{s}': (P['GH'], 'Fitted GH (acromion depth chain + method mean)'),
            f'acromioclavicular_{s}': (P['AC'], 'AC joint medial/inferior to the lateral acromion skin'),
            f'sternoclavicular_{s}': (P['SC'], 'SC joint lateral/deep to the jugular notch'),
            f'humeroulnar_{s}': (P['humeroulnar'], 'Trochlear centre medial of the elbow centre'),
            f'humeroradial_{s}': (P['humeroradial'], 'Capitulum lateral of the elbow centre'),
            f'radiocarpal_{s}': (P['WJC'], 'Fitted wrist centre (ISB styloid midpoint)'),
            f'subtalar_posterior_{s}': (L['sides'][s]['foot']['subtalar'], 'Posterior facet below the talar dome'),
            f'scapulothoracic_{s}': ((np.asarray(P['TS']) + np.asarray(P['AI'])) / 2, 'Functional: medial-border midpoint on the thoracic wall (contact locator, not a hinge)'),
            f'patellofemoral_{s}': ((np.asarray(L['sides'][s]['patella'][0]) + np.asarray(L['sides'][s]['patella'][1])) / 2 + np.array([0, 0.012, 0]), 'Patellar articular surface on the trochlea'),
            f'tmj_{s}': (L['head']['tmj_est'][s], 'TMJ estimate anterior/inferior to the estimated porion'),
            f'sacroiliac_anterior_{s}': (np.asarray(P['SI']) + np.array([0, -0.01, 0]), 'Anterior SI locator'),
            f'sacroiliac_posterior_{s}': (np.asarray(P['SI']) + np.array([0, 0.012, 0.005]), 'Posterior SI (ligamentous) locator'),
        })
    def along(bone, t):
        h, tl = B[bone]
        return h + (tl - h) * t
    for s in ('left', 'right'):
        r, u, t_, f = f'radius_{s}', f'ulna_{s}', f'tibia_{s}', f'fibula_{s}'
        explicit[f'proximal_radioulnar_{s}'] = (along(r, 0.03), 'Radial head centre in the radial notch (proximal end of the forearm rotation axis)')
        explicit[f'distal_radioulnar_{s}'] = (along(u, 0.96), 'Ulnar head centre in the sigmoid notch (distal end of the forearm rotation axis)')
        explicit[f'radioulnar_interosseous_{s}'] = ((along(r, 0.5) + along(u, 0.5)) / 2, 'Interosseous membrane mid-shaft locator (fibrous follower, not a hinge)')
        explicit[f'proximal_tibiofibular_{s}'] = ((along(f, 0.02) + along(t_, 0.06)) / 2, 'Fibular head facet under the lateral tibial condyle')
        explicit[f'distal_tibiofibular_{s}'] = ((along(f, 0.93) + along(t_, 0.97)) / 2, 'Distal syndesmosis above the talocrural joint')
        explicit[f'tibiofibular_interosseous_{s}'] = ((along(f, 0.5) + along(t_, 0.5)) / 2, 'Interosseous membrane mid-shaft locator')
        for i in range(1, 13):
            rib = f'rib_{i:02d}_{s}'
            explicit[f'costovertebral_{i:02d}_{s}'] = (along(rib, 0.0), 'Rib head on the vertebral bodies')
            if i <= 10:
                explicit[f'costotransverse_{i:02d}_{s}'] = (along(rib, 0.12), 'Rib tubercle at the transverse process (12% along the rib)')
    sternum_h, sternum_t = B['sternum']
    locators = {'manubrium': sternum_h + (sternum_t - sternum_h) * 0.15, 'sternal_body': sternum_h + (sternum_t - sternum_h) * 0.6,
                'xiphoid': sternum_t}
    for i in range(1, 11):
        for s in ('left', 'right'):
            ant = B[f'rib_{i:02d}_{s}'][1]
            if i <= 7:
                tgt = sternum_h + (sternum_t - sternum_h) * (0.08 + 0.13 * (i - 1))
                tgt = tgt + np.array([0.012 if s == 'left' else -0.012, 0, 0])
            else:
                tgt = B[f'rib_{i - 1:02d}_{s}'][1]
            locators[f'costal_cartilage_{i:02d}_{s}'] = (ant + tgt) / 2
    hy = B['hyoid']
    for s, sg in (('left', 1), ('right', -1)):
        locators[f'hyoid_greater_horn_{s}'] = (hy[0] + hy[1]) / 2 + np.array([sg * 0.018, 0.012, 0.004])
        locators[f'hyoid_lesser_horn_{s}'] = (hy[0] + hy[1]) / 2 + np.array([sg * 0.008, 0.003, 0.006])
    locators['hyoid_body'] = (hy[0] + hy[1]) / 2
    ch, ct = B['coccyx']
    for k in range(1, 5):
        locators[f'coccygeal_component_{k}'] = ch + (ct - ch) * (k - 0.5) / 4
    for s, sg in (('left', 1), ('right', -1)):
        mt_head = B[f'metatarsal_1_{s}'][1]
        locators[f'hallux_sesamoid_medial_{s}'] = mt_head + np.array([-sg * 0.007, 0.004, -0.010])
        locators[f'hallux_sesamoid_lateral_{s}'] = mt_head + np.array([sg * 0.006, 0.004, -0.010])
        us = np.asarray(L['sides'][s]['ulnar_styloid_bone'])
        locators[f'tfcc_{s}'] = us + (np.asarray(L['sides'][s]['WJC']) - us) * 0.35
    out = {}
    for jid, m in plan['joint_markers'].items():
        parts = m['participants']
        if jid in explicit:
            c, how = explicit[jid]
            c = np.asarray(c, float)
        else:
            pts = []
            seg = [p for p in parts if p in B]
            loc = [p for p in parts if p not in B]
            if len(seg) >= 2:
                a, b = segment_closest(*B[seg[0]], *B[seg[1]])
                pts += [a, b]
                for extra in seg[2:]:
                    q, _ = segment_closest(*B[extra], (a + b) / 2, (a + b) / 2 + 1e-6)
                    pts.append(q)
            elif len(seg) == 1:
                ref = np.mean([locators[p] for p in loc], axis=0) if loc else None
                q, _ = segment_closest(*B[seg[0]], ref, ref + 1e-6)
                pts.append(q)
            pts += [locators[p] for p in loc if p in locators]
            if not pts:
                raise ValueError('No geometry for joint ' + jid)
            c = np.mean(pts, axis=0)
            how = 'Midpoint of closest approach between participant segments' + (' and explicit locators' if loc else '')
        side = m.get('side') or (jid.rsplit('_', 1)[1] if jid.endswith(('_left', '_right')) else 'midline')
        if side in ('left', 'right') and all(p in B and not p.endswith(('_left', '_right')) for p in parts):
            # paired contacts between midline bones (atlanto-occipital, lateral atlantoaxial, facets, uncovertebral)
            sg = 1.0 if side == 'left' else -1.0
            fam = jid.split('_')[0]
            lateral = {'atlantooccipital': 0.022, 'atlantoaxial': 0.022, 'facet': 0.020, 'uncovertebral': 0.012}.get(fam, 0.015)
            posterior = {'facet': 0.022}.get(fam, 0.0)
            c = c + np.array([sg * lateral, posterior, 0.0])
            how += f'; paired contact offset {lateral*1000:.0f} mm lateral' + (f', {posterior*1000:.0f} mm posterior' if posterior else '')
        hosts = [p if p in B else host_bone(p) for p in parts]
        fb = next((p for p in hosts if frames.get(p, {}).get('frame_id') == m['frame_id']), None) or hosts[0]
        R = bone_frame(*B[fb])
        out[jid] = {'centre_m': c.tolist(), 'frame_bone': fb, 'frame_axes_columns_XYZ': R.tolist(), 'method': how,
                    'fit_status': 'FITTED_UNVERIFIED_OPERATION'}
    return out


# ------------------------------------------------------------------ verification
def winding_inside(points, V, T):
    """Generalised winding number (solid-angle sum) for a closed mesh; > 0.5 means inside."""
    A, Bv, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    res = []
    for p in np.atleast_2d(points):
        a, b, c = A - p, Bv - p, C - p
        la, lb, lc = (np.linalg.norm(x, axis=1) for x in (a, b, c))
        det = np.einsum('ij,ij->i', a, np.cross(b, c))
        den = la * lb * lc + np.einsum('ij,ij->i', a, b) * lc + np.einsum('ij,ij->i', b, c) * la + np.einsum('ij,ij->i', c, a) * lb
        res.append(abs(np.arctan2(det, den).sum() * 2 / (4 * math.pi)))
    return np.array(res)


TROTTER_GLESER = {  # stature cm = a * bone cm + b (SE cm), white males
    'femur': (2.38, 61.41, 3.27), 'tibia': (2.52, 78.62, 3.37), 'fibula': (2.68, 71.78, 3.29),
    'humerus': (3.08, 70.45, 4.05), 'radius': (3.78, 79.01, 4.32), 'ulna': (3.70, 74.05, 4.32)}


def anatomical_lengths(L, s, bones):
    """Approximate osteometric maximum lengths from fitted joint centres (documented additions)."""
    P = L['sides'][s]
    g = lambda k: np.asarray(P[k])
    jl_off = np.linalg.norm(g('KJC') - g('tibial_plateau'))
    foot = P['foot']
    return {
        'femur': (np.linalg.norm(g('HJC') - g('KJC')) + 0.0247 + jl_off, 'HJC-KJC + head radius (24.7 mm) + epicondyle-to-joint-line offset'),
        'tibia': (np.linalg.norm(g('tibial_plateau') - g('AJC')) + 0.010, 'plateau to ankle centre + ~10 mm to the malleolar tip'),
        'fibula': (np.linalg.norm(g('fibular_head') - g('lateral_malleolus_bone')) + 0.015, 'fibular head to lateral malleolus + tip/apex allowance'),
        'humerus': (np.linalg.norm(g('GH') - g('EJC')) + 0.0247 + 0.012, 'GH-EJC + head radius + trochlea below the epicondyles'),
        'radius': (np.linalg.norm(g('humeroradial') - g('radial_styloid_bone')) + 0.008, 'radial head to styloid + articular allowance'),
        'ulna': (np.linalg.norm(g('humeroulnar') - g('ulnar_styloid_bone')) + 0.025, 'trochlear notch to styloid + olecranon height'),
    }


def verify(bones, markers, L, V, T, rig, stature):
    checks = {}
    pts, names = [], []
    for k, b in bones.items():
        h, t = np.asarray(b['head_m']), np.asarray(b['tail_m'])
        for tag, p in (('head', h), ('mid', (h + t) / 2), ('tail', t)):
            pts.append(p)
            names.append(f'{k}.{tag}')
    w = winding_inside(np.array(pts), V, T)
    outside = [n for n, x in zip(names, w) if x < 0.5]
    checks['bones_inside_body'] = {'status': 'PASS' if not outside else 'FAIL', 'tested_points': len(pts), 'outside': outside}
    mk = np.array([m['centre_m'] for m in markers.values()])
    wm = winding_inside(mk, V, T)
    out_m = [j for j, x in zip(markers, wm) if x < 0.5]
    checks['joint_markers_inside_body'] = {'status': 'PASS' if not out_m else 'FAIL', 'tested': len(mk), 'outside': out_m}
    asym = []
    max_asym = [0.0]
    for k, b in bones.items():
        if k.endswith('_left'):
            r = bones[k[:-5] + '_right']
            for key in ('head_m', 'tail_m'):
                a, c = np.asarray(b[key]), np.asarray(r[key]) * np.array([-1, 1, 1])
                if np.linalg.norm(a - c) > 5e-4:
                    asym.append(k)
                max_asym[0] = max(max_asym[0], float(np.linalg.norm(a - c)))
        elif not k.endswith('_right'):
            if max(abs(b['head_m'][0]), abs(b['tail_m'][0])) > 1e-9:
                asym.append(k + ' (midline bone off x=0)')
    checks['bilateral_symmetry'] = {'status': 'PASS' if not asym else 'FAIL', 'failures': asym, 'max_left_right_mirror_difference_m': max_asym[0],
                                    'tolerance_m': 5e-4, 'note': 'Each side is fitted independently; the r95 mesh is mirror-symmetric to 1.3e-7 m, so differences above section-sampling noise indicate a recipe defect. Midline bones must lie on x=0.'}
    dist = []
    for s in ('left', 'right'):
        for a, b in [('sternoclavicular', 'acromioclavicular'), ('acromioclavicular', 'glenohumeral'), ('talocrural', 'subtalar_posterior'),
                     ('humeroulnar', 'humeroradial'), ('radiocarpal', 'midcarpal_lunate_capitate'), ('hip', 'sacroiliac_anterior'),
                     ('tibiofemoral', 'patellofemoral'), ('proximal_radioulnar', 'humeroradial'), ('tmj', 'atlantooccipital')]:
            ja, jb = f'{a}_{s}', f'{b}_{s}'
            if ja in markers and jb in markers:
                d = float(np.linalg.norm(np.asarray(markers[ja]['centre_m']) - np.asarray(markers[jb]['centre_m'])))
                dist.append({'pair': [ja, jb], 'separation_m': d})
    collisions = []
    keys = list(markers)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            if np.linalg.norm(mk[i] - mk[j]) < 1e-4:
                collisions.append([keys[i], keys[j]])
    checks['distinct_centres'] = {'status': 'PASS' if all(x['separation_m'] > 0.005 for x in dist) and not collisions else 'FAIL',
                                  'named_pairs': dist, 'coincident_marker_pairs_lt_0_1mm': collisions}
    order = []
    for s in ('left', 'right'):
        P = L['sides'][s]
        z = {k: P[k][2] for k in ('HJC', 'KJC', 'AJC', 'GH', 'EJC', 'WJC')}
        order.append({'side': s, 'lower_limb_descending': bool(z['HJC'] > z['KJC'] > z['AJC'] > 0),
                      'upper_limb_descending': bool(z['GH'] > z['EJC'] > z['WJC'])})
    spine = ['sacrum'] + [f'l{i}' for i in range(5, 0, -1)] + [f't{i}' for i in range(12, 0, -1)] + [f'c{i}' for i in range(7, 0, -1)]
    zs = [(bones[n]['head_m'][2] + bones[n]['tail_m'][2]) / 2 for n in spine]
    checks['ordering'] = {'status': 'PASS' if all(o['lower_limb_descending'] and o['upper_limb_descending'] for o in order) and all(np.diff(zs) > 0) else 'FAIL',
                          'limbs': order, 'spine_monotonic': bool(all(np.diff(zs) > 0))}
    tg = {}
    for s in ('left', 'right'):
        for bone, (length, how) in anatomical_lengths(L, s, bones).items():
            a, b0, se = TROTTER_GLESER[bone]
            pred = (a * length * 100 + b0) / 100
            tg[f'{bone}_{s}'] = {'length_m': float(length), 'derivation': how, 'predicted_stature_m': pred,
                                 'difference_m': pred - stature, 'se_m': se / 100,
                                 'within_2se': bool(abs(pred - stature) <= 2 * se / 100)}
    checks['trotter_gleser_cross_check'] = {'status': 'PASS' if all(v['within_2se'] for v in tg.values()) else 'FAIL',
                                            'character_stature_m': stature, 'bones': tg,
                                            'interpretation': 'Consistency of fitted long-bone lengths with stature (population regression, SE as published). Not an anatomical acceptance.'}
    sfx = {'left': '_r', 'right': '_l'}
    cmp = {}
    for s in ('left', 'right'):
        P = L['sides'][s]
        for anat, rig_bone in (('HJC', 'thigh'), ('KJC', 'shin'), ('AJC', 'foot'), ('GH', 'upperarm'), ('EJC', 'forearm'), ('WJC', 'hand'), ('SC', 'clavicle'), ('AC', 'scapula')):
            rh = np.asarray(rig[rig_bone + sfx[s]][0])
            d = np.asarray(P[anat]) - rh
            cmp[f'{anat}_{s}'] = {'runtime_bone_head': rig_bone + sfx[s], 'fitted_m': P[anat], 'runtime_head_m': rh.tolist(),
                                  'fitted_minus_runtime_m': d.tolist(), 'distance_m': float(np.linalg.norm(d))}
    checks['runtime_rig_comparison'] = {'status': 'MEASURED', 'note': 'Anatomical side binding: anatomical left = runtime *_r (F-SIDE-001).', 'joints': cmp}
    return checks
