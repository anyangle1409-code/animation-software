"""Phase 9 isolated bone-only test specifications and measurement analysis (pure numpy).

Each test drives one articulation of HGPT_ANATOMICAL_MASTER through neutral -> intermediate ->
context reference -> return -> reversal -> return with C1 (cosine) easing, on each side. Commands are
rigid world-space rotations about fitted joint centres/axes defined in the rest pose. Measurements are
taken back from the evaluated Blender pose: signed clinical JCS angles, joint-centre drift, off-axis
residuals, continuity (finite-difference velocity/acceleration) and left/right mirror consistency.

Amplitudes come from the atlas observations with their context attached. Where no joint-specific
source exists, the amplitude is a labelled TEST AMPLITUDE and is never a range-of-motion claim.
"""
import math

import numpy as np

import joint_solver as js

UP = np.array([0, 0, 1.0])
ANT = np.array([0, -1.0, 0])
SIDES = ('left', 'right')
S = {'left': 1.0, 'right': -1.0}  # world-X sign of the anatomical side


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def rodrigues(axis, deg):
    return js.rot(unit(axis), deg)


def rigid(R, c):
    """4x4 world transform rotating by R about point c."""
    M = np.eye(4)
    M[:3, :3] = R
    M[:3, 3] = np.asarray(c) - R @ np.asarray(c)
    return M


# ----------------------------------------------------------------------------- anatomical frames
def limb_frame(proximal_pt, distal_pt, radial_dir, side):
    """ISB-pattern frame for forearm/hand/digits: Y proximal, X palmar, Z = X x Y (right)."""
    Yd = unit(np.asarray(proximal_pt) - np.asarray(distal_pt))
    r = np.asarray(radial_dir, float)
    r = unit(r - (r @ Yd) * Yd)
    s = 1.0 if side == 'right' else -1.0
    Xd = unit(s * np.cross(Yd, r))
    return np.stack([Xd, Yd, np.cross(Xd, Yd)], axis=1)


def thumb_frame(proximal_pt, distal_pt, radial_dir):
    """Thumb flexes across the palm toward the ulnar side: X = ulnar direction normal to the thumb axis."""
    Yd = unit(np.asarray(proximal_pt) - np.asarray(distal_pt))
    r = np.asarray(radial_dir, float)
    Xd = unit(-(r - (r @ Yd) * Yd))
    return np.stack([Xd, Yd, np.cross(Xd, Yd)], axis=1)


def frames(rec):
    """Rest anatomical frames per segment (columns X, Y, Z)."""
    B = rec['bones']
    sk = rec['skeleton_input']
    F = {'world': js.WORLD_FRAME}
    for bid, b in B.items():
        F[bid] = js.frame_from_bone(b['head_m'], b['tail_m'])
    for side in SIDES:
        P = sk['sides'][side]
        us, rs, ejc = np.array(P['ulnar_styloid_bone']), np.array(P['radial_styloid_bone']), np.array(P['EJC'])
        fa = limb_frame(ejc, (us + rs) / 2, rs - us, side)
        for b in ('radius', 'ulna'):
            F[f'{b}_{side}'] = fa
        mc = {d: np.array(B[f'metacarpal_{d}_{side}']['tail_m']) for d in (2, 3, 5)}
        hand = limb_frame(P['WJC'], mc[3], mc[2] - mc[5], side)
        for c in ('scaphoid', 'lunate', 'triquetrum', 'pisiform', 'trapezium', 'trapezoid', 'capitate', 'hamate'):
            F[f'{c}_{side}'] = hand
        for d in range(1, 6):
            F[f'metacarpal_{d}_{side}'] = hand
        for d in range(2, 6):
            for ph in ('proximal', 'middle', 'distal'):
                b = B[f'digit{d}_{ph}_phalanx_{side}']
                F[f'digit{d}_{ph}_phalanx_{side}'] = limb_frame(b['head_m'], b['tail_m'], mc[2] - mc[5], side)
        r_hand = mc[2] - mc[5]
        for bid in ('metacarpal_1', 'thumb_proximal_phalanx', 'thumb_distal_phalanx'):
            b = B[f'{bid}_{side}']
            F[f'{bid}_{side}'] = thumb_frame(b['head_m'], b['tail_m'], r_hand)
    return F


# ----------------------------------------------------------------------------- test definitions
DISC_ABOVE = {'l2_l3': 'disc_l1_l2', 'l3_l4': 'disc_l2_l3', 'l4_l5': 'disc_l3_l4', 'l5_sacrum': 'disc_l4_l5'}   # carried by the moving vertebra


def half_rotation(R):
    """Exact square root of a rotation (same axis, half angle)."""
    q = rot_to_quat(R)
    if q[0] < 0:
        q = -q
    h = np.array([1.0 + q[0], *q[1:]])
    h /= np.linalg.norm(h)
    w, x, y, z = h
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def intermetacarpal_angle(d1, d2, normal):
    """Angle between metacarpal directions projected onto the plane with the given normal (deg)."""
    n = unit(normal)
    a, b = d1 - (d1 @ n) * n, d2 - (d2 @ n) * n
    return math.degrees(math.atan2(np.linalg.norm(np.cross(a, b)), a @ b))


def ease(keys, frames_per_leg=10):
    """Keypose list -> per-frame values with cosine easing (C1 at every keypose)."""
    out = []
    for a, b in zip(keys, keys[1:]):
        for i in range(frames_per_leg):
            t = 0.5 - 0.5 * math.cos(math.pi * i / frames_per_leg)
            out.append({k: a.get(k, 0.0) + (b.get(k, 0.0) - a.get(k, 0.0)) * t for k in set(a) | set(b)})
    out.append(dict(keys[-1]))
    return out


def sweep(channel, positive, negative, base=None):
    """neutral -> half -> positive -> half -> neutral -> negative half -> negative -> neutral (+ base pose)."""
    base = base or {}
    k = lambda v: {**base, channel: base.get(channel, 0.0) + v}
    seq = [k(0), k(positive / 2), k(positive), k(positive / 2), k(0)]
    if negative:
        seq += [k(-negative / 2), k(-negative), k(-negative / 2), k(0)]
    return seq


def obs(rec_obs, key):
    o = rec_obs[key]
    return {'id': key, 'value': o['value'], 'mode': o['mode'], 'scope': o['measured_scope'], 'sources': o['sources'],
            'population': o.get('population')}


def specs(rec, atlas):
    B = rec['bones']
    sk = rec['skeleton_input']
    O = atlas['observations']
    M = rec['joint_markers']
    F = frames(rec)
    T = []

    def add(**kw):
        T.append(kw)

    for side in SIDES:
        s = S[side]
        P = sk['sides'][side]
        lat = np.array([s, 0, 0])
        # ---- hip
        add(id=f'hip_flexion_extension_{side}', profile='hip', side=side, kind='zxy', joint='hip', proximal='world', moving=[f'femur_{side}'],
            centre=P['HJC'], plane='sagittal', keys=sweep('flexion', O['cdc_hip_flexion']['value']['mean'], O['cdc_hip_extension']['value']['mean']),
            context=[obs(O, 'cdc_hip_flexion'), obs(O, 'cdc_hip_extension')], amplitude_basis='CDC passive mean (male 20-44); amplitude only, not a character limit',
            marker=f'hip_{side}', distal_marker=f'tibiofemoral_{side}')
        add(id=f'hip_abduction_adduction_{side}', profile='hip', side=side, kind='zxy', joint='hip', proximal='world', moving=[f'femur_{side}'],
            centre=P['HJC'], plane='frontal', keys=sweep('adduction', 20.0, 30.0), context=[],
            amplitude_basis='TEST AMPLITUDE (no hip ab/adduction observation in the atlas): +20 adduction / -30 abduction', marker=f'hip_{side}', distal_marker=f'tibiofemoral_{side}')
        prone = {'left': ('hip_prone_ir_left', 'hip_prone_er_left'), 'right': ('hip_prone_ir_right', 'hip_prone_er_right')}[side]
        sit = {'left': ('hip_sitting_ir_left', 'hip_sitting_er_left'), 'right': ('hip_sitting_ir_right', 'hip_sitting_er_right')}[side]
        add(id=f'hip_rotation_at_0_flexion_{side}', profile='hip', side=side, kind='zxy', joint='hip', proximal='world', moving=[f'femur_{side}'],
            centre=P['HJC'], plane='transverse', keys=sweep('internal', O[prone[0]]['value']['mean'], O[prone[1]]['value']['mean']),
            context=[obs(O, prone[0]), obs(O, prone[1])], amplitude_basis='Prone (hip 0 deg) passive means, side-specific', marker=f'hip_{side}', distal_marker=f'tibiofemoral_{side}')
        add(id=f'hip_rotation_at_90_flexion_{side}', profile='hip', side=side, kind='zxy', joint='hip', proximal='world', moving=[f'femur_{side}'],
            centre=P['HJC'], plane='transverse_at_90_flexion',
            keys=[{'flexion': 0.0}, {'flexion': 90.0}] + sweep('internal', O[sit[0]]['value']['mean'], O[sit[1]]['value']['mean'], base={'flexion': 90.0})[1:] + [{'flexion': 0.0}],
            context=[obs(O, sit[0]), obs(O, sit[1])], amplitude_basis='Sitting (hip 90 deg) passive means, side-specific', marker=f'hip_{side}', distal_marker=f'tibiofemoral_{side}')
        # ---- knee
        add(id=f'knee_flexion_extension_{side}', profile='knee', side=side, kind='zxy', joint='knee', proximal=f'femur_{side}', moving=[f'tibia_{side}'],
            centre=P['KJC'], plane='sagittal', keys=sweep('flexion', O['cdc_knee_flexion']['value']['mean'], O['cdc_knee_extension']['value']['mean']),
            context=[obs(O, 'cdc_knee_flexion'), obs(O, 'cdc_knee_extension')], amplitude_basis='CDC passive knee complex means; screw-home coupling not applied (no sourced magnitude)',
            marker=f'tibiofemoral_{side}', distal_marker=f'talocrural_{side}')
        # ---- talocrural (axis through the fitted malleolus skin points; obliquity not measurable on this mesh)
        med = np.array(rec['landmarks_and_joint_centres']['sides'][side]['ankle']['malleolus_medial_skin']['value_m'])
        latm = np.array(rec['landmarks_and_joint_centres']['sides'][side]['ankle']['malleolus_lateral_skin']['value_m'])
        tc_axis = unit(latm - med) * s * -1.0  # points to the character's right for both sides
        add(id=f'talocrural_dorsi_plantarflexion_{side}', profile='ankle', side=side, kind='axis', joint='ankle', proximal=f'tibia_{side}', moving=[f'talus_{side}'],
            centre=P['AJC'], axis=tc_axis.tolist(), positive='dorsiflexion', plane='sagittal', keys=sweep('angle', 20.0, 40.0),
            context=[obs(O, 'cdc_ankle_dorsiflexion'), obs(O, 'cdc_ankle_plantarflexion')],
            amplitude_basis='TEST AMPLITUDE +20 DF / -40 PF for the talocrural stage; CDC values are the ankle-foot complex and are not assigned to this joint',
            marker=f'talocrural_{side}', distal_marker=f'talocalcaneonavicular_{side}')
        # ---- subtalar about the Inman axis
        heel = np.array(P['foot']['heel_bone'])
        mt2 = np.array(P['foot']['mt2'][1])
        f_axis = unit(np.array([mt2[0] - heel[0], mt2[1] - heel[1], 0.0]))
        medial = -lat
        cpl = js.FOLLOWER_COUPLINGS['subtalar_axis']
        st_axis = unit(math.cos(math.radians(cpl['inclination_deg'])) * (math.cos(math.radians(cpl['medial_deviation_deg'])) * f_axis
                       + math.sin(math.radians(cpl['medial_deviation_deg'])) * medial) + math.sin(math.radians(cpl['inclination_deg'])) * UP)
        add(id=f'subtalar_inversion_eversion_{side}', profile='subtalar', side=side, kind='axis', joint='subtalar', proximal=f'talus_{side}', moving=[f'calcaneus_{side}'],
            centre=P['foot']['subtalar'], axis=(st_axis * -s).tolist(), positive='inversion (supination about the Inman axis)', plane='oblique_inman_axis',
            keys=sweep('angle', 20.0, 10.0), context=[], amplitude_basis='TEST AMPLITUDE +20 inversion / -10 eversion about the Inman axis (42 deg / 23 deg); midfoot followers not driven',
            marker=f'subtalar_posterior_{side}', distal_marker=f'calcaneocuboid_{side}')
        # ---- glenohumeral (scapula fixed; thorax-aligned reference)
        for plane in (0.0, 40.0, 90.0):
            add(id=f'gh_elevation_plane_{int(plane)}_{side}', profile='gh', side=side, kind='gh', joint='gh', proximal='world', moving=[f'humerus_{side}'],
                centre=P['GH'], plane=f'elevation_plane_{int(plane)}', keys=[{'plane': plane, 'elevation': v} for v in (0, 30, 60, 90, 120, 90, 60, 30, 0)],
                context=[], amplitude_basis='TEST AMPLITUDE to 120 deg GH elevation with the scapula fixed; CDC 168.8 deg is humerothoracic and is not assigned to GH',
                marker=f'glenohumeral_{side}', distal_marker=f'humeroulnar_{side}')
        for elev in (0.0, 90.0):
            keys = [{'plane': 0.0, 'elevation': elev, 'internal': v} for v in (0, 25, 50, 25, 0, -25, -50, -25, 0)]
            if elev:
                keys = [{'plane': 0.0, 'elevation': 0.0, 'internal': 0.0}] + keys + [{'plane': 0.0, 'elevation': 0.0, 'internal': 0.0}]
            add(id=f'gh_axial_rotation_at_{int(elev)}_elevation_{side}', profile='gh', side=side, kind='gh', joint='gh', proximal='world', moving=[f'humerus_{side}'],
                centre=P['GH'], plane=f'axial_at_{int(elev)}', keys=keys, context=[], amplitude_basis='TEST AMPLITUDE +/-50 deg axial rotation at stated elevation',
                marker=f'glenohumeral_{side}', distal_marker=f'humeroulnar_{side}')
        # ---- elbow flexion about the humeroulnar-humeroradial axis, at two forearm rotations
        hu, hr = np.array(M[f'humeroulnar_{side}']['centre_m']), np.array(M[f'humeroradial_{side}']['centre_m'])
        el_axis = unit(hr - hu) * s * -1.0  # to the character's right
        radial_head = np.array(B[f'radius_{side}']['head_m'])
        pr_axis = unit(np.array(M[f'distal_radioulnar_{side}']['centre_m']) - radial_head)   # radial-head centre -> ulnar head
        for pron in (0.0, 60.0):
            keys = sweep('angle', O['cdc_elbow_flexion']['value']['mean'], O['cdc_elbow_extension']['value']['mean'], base={'pronation': pron})
            if pron:
                keys = [{'angle': 0.0, 'pronation': 0.0}] + keys + [{'angle': 0.0, 'pronation': 0.0}]
            add(id=f'elbow_flexion_at_pronation_{int(pron)}_{side}', profile='elbow', side=side, kind='elbow', joint='elbow', proximal=f'humerus_{side}',
                moving=[f'ulna_{side}', f'radius_{side}'], centre=((hu + hr) / 2).tolist(), axis=el_axis.tolist(), pron_axis=pr_axis.tolist(),
                pron_centre=radial_head.tolist(), positive='flexion', plane='sagittal', keys=keys,
                context=[obs(O, 'cdc_elbow_flexion'), obs(O, 'cdc_elbow_extension')], amplitude_basis='CDC passive elbow means at the stated forearm rotation',
                marker=f'humeroulnar_{side}', distal_marker=f'radiocarpal_{side}')
        for elb in (0.0, 90.0):
            keys = sweep('pronation', O['cdc_forearm_pronation']['value']['mean'], O['cdc_forearm_supination']['value']['mean'], base={'angle': elb})
            if elb:
                keys = [{'angle': 0.0, 'pronation': 0.0}] + keys + [{'angle': 0.0, 'pronation': 0.0}]
            add(id=f'forearm_rotation_at_elbow_{int(elb)}_{side}', profile='radioulnar', side=side, kind='elbow', joint='forearm', proximal=f'humerus_{side}',
                moving=[f'ulna_{side}', f'radius_{side}'], centre=((hu + hr) / 2).tolist(), axis=el_axis.tolist(), pron_axis=pr_axis.tolist(),
                pron_centre=radial_head.tolist(), positive='pronation', plane='axial', keys=keys,
                context=[obs(O, 'cdc_forearm_pronation'), obs(O, 'cdc_forearm_supination'), obs(O, 'forearm_pronation'), obs(O, 'forearm_supination')],
                amplitude_basis='CDC passive forearm means; dynamic biplane active means retained as a second context', marker=f'proximal_radioulnar_{side}', distal_marker=f'radiocarpal_{side}')
        # ---- wrist complex (radiocarpal + midcarpal equal split, unverified)
        for ch, pos, neg, a, b in (('flexion', 'wrist_flexion', 'wrist_extension', 'flexion', 'extension'),
                                   ('adduction', 'wrist_ulnar_deviation', 'wrist_radial_deviation', 'ulnar deviation', 'radial deviation')):
            add(id=f'wrist_{ch}_{side}', profile='radiocarpal', side=side, kind='wrist', joint='wrist', proximal=f'radius_{side}',
                moving=[f'scaphoid_{side}', f'lunate_{side}'], stage2=[f'trapezium_{side}', f'trapezoid_{side}', f'capitate_{side}', f'hamate_{side}'],
                centre=P['WJC'], centre2=M[f'midcarpal_lunate_capitate_{side}']['centre_m'], plane=ch,
                keys=sweep(ch, O[pos]['value']['mean'], O[neg]['value']['mean']), context=[obs(O, pos), obs(O, neg)],
                amplitude_basis=f'Active wrist-complex means ({a} / {b}); split equally between radiocarpal and midcarpal stages (split unverified)',
                marker=f'radiocarpal_{side}', distal_marker=f'cmc_3_{side}')
        # ---- fingers: digit-specific MCP/PIP/DIP flexion (active means)
        for d in range(2, 6):
            joints = [('mcp', f'digit{d}_proximal_phalanx_{side}', f'digit{d}_mcp_{side}', f'metacarpal_{d}_{side}'),
                      ('pip', f'digit{d}_middle_phalanx_{side}', f'digit{d}_pip_{side}', f'digit{d}_proximal_phalanx_{side}'),
                      ('dip', f'digit{d}_distal_phalanx_{side}', f'digit{d}_dip_{side}', f'digit{d}_middle_phalanx_{side}')]
            amp = {j: O[f'digit{d}_{j}_flexion']['value']['mean'] for j, *_ in joints}
            keys = [{j: f * amp[j] for j, *_ in joints} for f in (0, 0.5, 1.0, 0.5, 0, -0.1 / 1.0, 0)]
            add(id=f'digit{d}_flexion_{side}', profile='mcp', side=side, kind='digit', joint='digit', proximal=f'metacarpal_{d}_{side}',
                chain=[{'joint': j, 'moving': mv, 'marker': mk, 'proximal': px, 'centre': M[mk]['centre_m']} for j, mv, mk, px in joints],
                plane='flexion', keys=keys, context=[obs(O, f'digit{d}_{j}_flexion') for j, *_ in joints],
                amplitude_basis='Digit-specific active means (reduced numerical confidence, see finger_table_consistency); -10% of each mean as a small extension reversal (TEST AMPLITUDE)',
                marker=f'digit{d}_mcp_{side}', distal_marker=f'digit{d}_dip_{side}')
        # ---- thumb MCP/IP (clinical values; examination mode unspecified)
        tj = [('mcp', f'thumb_proximal_phalanx_{side}', f'thumb_mcp_{side}', f'metacarpal_1_{side}'),
              ('ip', f'thumb_distal_phalanx_{side}', f'thumb_ip_{side}', f'thumb_proximal_phalanx_{side}')]
        tk = [{'mcp': 0, 'ip': 0}, {'mcp': 30, 'ip': 44}, {'mcp': O['thumb_mcp_flexion']['value']['mean'], 'ip': O['thumb_ip_flexion']['value']['mean']},
              {'mcp': 30, 'ip': 44}, {'mcp': 0, 'ip': 0}, {'mcp': -O['thumb_mcp_extension']['value']['mean'], 'ip': -O['thumb_ip_extension']['value']['mean']}, {'mcp': 0, 'ip': 0}]
        add(id=f'thumb_flexion_{side}', profile='thumb_mcp', side=side, kind='digit', joint='digit', proximal=f'metacarpal_1_{side}',
            chain=[{'joint': j, 'moving': mv, 'marker': mk, 'proximal': px, 'centre': M[mk]['centre_m']} for j, mv, mk, px in tj],
            plane='thumb_flexion_across_palm', keys=tk, context=[obs(O, k) for k in ('thumb_mcp_flexion', 'thumb_mcp_extension', 'thumb_ip_flexion', 'thumb_ip_extension')],
            amplitude_basis='Clinical thumb means (examination mode unspecified in the accessible abstract); flexion axis normal to the thumb and the hand radial-ulnar line',
            marker=f'thumb_mcp_{side}', distal_marker=f'thumb_ip_{side}')
        # ---- thumb CMC: drive the first metacarpal until the clinical intermetacarpal angle is reached
        hand = F[f'capitate_{side}']
        palmar, radial = hand[:, 0], hand[:, 2] * (1.0 if side == 'right' else -1.0)
        mc1, mc2 = B[f'metacarpal_1_{side}'], B[f'metacarpal_2_{side}']
        for motion, obs_key, axis, plane_normal in (('radial_abduction', 'thumb_cmc_radial_abduction', palmar, palmar),
                                                     ('anteposition', 'thumb_cmc_anteposition', radial, radial)):
            d1 = unit(np.array(mc1['tail_m']) - np.array(mc1['head_m']))
            d2 = unit(np.array(mc2['tail_m']) - np.array(mc2['head_m']))
            rest_angle = intermetacarpal_angle(d1, d2, plane_normal)
            target = O[obs_key]['value']['mean']
            if not rest_angle + 1.0 < target:
                raise ValueError(f'{motion}: unsigned intermetacarpal target {target} must exceed the rest angle {rest_angle:.1f}')
            probe = rodrigues(axis, 5.0) @ d1
            sgn = 1.0 if intermetacarpal_angle(probe, d2, plane_normal) > rest_angle else -1.0
            add(id=f'thumb_cmc_{motion}_{side}', profile='thumb_cmc', side=side, kind='axis', joint='thumb_cmc', proximal=f'trapezium_{side}',
                moving=[f'metacarpal_1_{side}'], centre=M[f'cmc_1_{side}']['centre_m'], axis=(axis * sgn).tolist(), positive=motion,
                plane=motion, keys=sweep('angle', target - rest_angle, 0.0), context=[obs(O, obs_key)],
                amplitude_basis=f'Command = clinical intermetacarpal mean {target} deg minus the fitted rest angle {rest_angle:.1f} deg (examination mode unspecified); measured angle reported',
                marker=f'cmc_1_{side}', distal_marker=f'thumb_mcp_{side}', intermetacarpal={'plane_normal': list(plane_normal), 'mc2_dir': list(d2), 'rest_angle_deg': rest_angle, 'target_deg': target})
        # ---- sacroiliac nutation (functional total rotation)
        add(id=f'sacroiliac_rotation_{side}', profile='si', side=side, kind='axis', joint='si', proximal='sacrum', moving=[f'hip_bone_{side}'],
            centre=M[f'sacroiliac_anterior_{side}']['centre_m'], axis=[-1.0, 0, 0], positive='posterior rotation of the innominate',
            plane='sagittal', keys=sweep('angle', O['si_rotation']['value']['mean'] / 2, O['si_rotation']['value']['mean'] / 2),
            context=[obs(O, 'si_rotation')], amplitude_basis='Functional total SI rotation 1.7 deg (healthy volunteers), split +/-0.85 about a mediolateral axis through the SI locator',
            marker=f'sacroiliac_anterior_{side}', distal_marker=f'hip_{side}')
        # ---- hallux MTP dorsiflexion
        add(id=f'hallux_mtp_dorsiflexion_{side}', profile='hallux', side=side, kind='axis', joint='hallux_mtp', proximal=f'metatarsal_1_{side}',
            moving=[f'hallux_proximal_phalanx_{side}'], centre=M[f'mtp_1_{side}']['centre_m'], axis=(np.array([-1.0, 0, 0])).tolist(), positive='dorsiflexion',
            plane='sagittal', keys=sweep('angle', O['hallux_active']['value']['mean'], 20.0), context=[obs(O, 'hallux_active')],
            amplitude_basis='Standing active DF mean (task-specific); -20 plantarflexion TEST AMPLITUDE', marker=f'mtp_1_{side}', distal_marker=f'hallux_ip_{side}')
    # ---- coupled tests (sourced magnitudes; shapes partly unverified, see FOLLOWER_COUPLINGS)
    for side in SIDES:
        P = sk['sides'][side]
        add(id=f'knee_flexion_with_screw_home_{side}', profile='knee', side=side, kind='zxy', joint='knee', proximal=f'femur_{side}', moving=[f'tibia_{side}'],
            centre=P['KJC'], plane='sagittal_with_axial_coupling', keys=sweep('flexion', 60.0, 0.0) + [{'flexion': 30.0}, {'flexion': 0.0}],
            derive='screw_home', context=[], amplitude_basis='TEST AMPLITUDE 0-60 deg knee flexion; coupled tibial internal rotation 3.6 deg over the first 20 deg of flexion (screw-home reversed)',
            marker=f'tibiofemoral_{side}', distal_marker=f'talocrural_{side}', coupled=True)
        add(id=f'shoulder_complex_scapular_plane_{side}', profile='st', side=side, kind='shoulder_complex', joint='shoulder_complex', proximal='world',
            moving=[f'clavicle_{side}', f'scapula_{side}', f'humerus_{side}'], centre=P['GH'], plane='scapular_plane_40',
            keys=[{'elevation': v} for v in (0.0, 60.0, 117.5, 60.0, 0.0, 60.0, 0.0)], derive='shoulder_rhythm', context=[],
            amplitude_basis='GH elevation 0-117.5 deg in the 40 deg plane with sourced scapulothoracic rhythm (0.43 upward rotation per GH degree; McClure end values) and clavicular posterior rotation 31 deg',
            marker=f'acromioclavicular_{side}', distal_marker=f'glenohumeral_{side}', coupled=True,
            landmarks={k: P[k] for k in ('TS', 'AA', 'AI', 'AC', 'SC', 'GH')})
    # ---- midline: C1/C2 axial rotation, lumbar segmental extension, thoracic segment FE/LB/AR
    add(id='c1_c2_axial_rotation', profile='c1_c2', side='midline', kind='axis', joint='c1_c2', proximal='c2', moving=['c1'],
        centre=M['atlantoaxial_median']['centre_m'], axis=[0, 0, 1.0], positive='rotation to the character left (counter-clockwise viewed from above)',
        plane='transverse', keys=sweep('angle', O['c1c2_left']['value']['mean'], O['c1c2_right']['value']['mean']),
        context=[obs(O, 'c1c2_left'), obs(O, 'c1c2_right')], amplitude_basis='MRI maximal voluntary rotation means (left/right)', marker='atlantoaxial_median', distal_marker='atlantooccipital_left')
    for ch in ('flexion', 'adduction', 'internal'):
        add(id=f'cervical_c4_c5_{ch}', profile='cervical', side='midline', kind='zxy', joint='spine', proximal='c5', moving=['c4'], centre=M['disc_c4_c5']['centre_m'],
            plane=ch, keys=sweep(ch, 5.0, 5.0), context=[],
            amplitude_basis='TEST AMPLITUDE +/-5 deg (cervical review values excluded: cervical_review_AR_typo; no per-level transferable value)', marker='disc_c4_c5',
            distal_marker='facet_c3_c4_left' if ch == 'internal' else 'disc_c3_c4')
    tmj_l, tmj_r = np.array(M['tmj_left']['centre_m']), np.array(M['tmj_right']['centre_m'])
    mand = B['mandible']
    incisor = np.array(mand['tail_m']) + np.array([0, 0.0, 0.02])
    add(id='tmj_opening', profile='tmj', side='midline', kind='tmj', joint='tmj', proximal='temporal_left', moving=['mandible'],
        centre=((tmj_l + tmj_r) / 2).tolist(), axis=unit(tmj_l - tmj_r).tolist(), incisor=incisor.tolist(), plane='sagittal',
        keys=[{'angle': v, 'glide': g} for v, g in ((0, 0), (12, 0.008), (25, 0.016), (12, 0.008), (0, 0))], context=[obs(O, 'tmj_incisor'), obs(O, 'tmj_condyle')],
        amplitude_basis='TEST AMPLITUDE 25 deg rotation with 16 mm anteroinferior condylar glide (within the observed 7.5-25.3 mm condylar range); incisor displacement compared with the observed 34.9-54.3 mm',
        marker='tmj_left', distal_marker=None)
    for lv, key in (('l2_l3', 'lumbar_lift_l2_l3'), ('l3_l4', 'lumbar_lift_l3_l4'), ('l4_l5', 'lumbar_lift_l4_l5'), ('l5_sacrum', 'lumbar_lift_l5_sacrum')):
        sup, inf = lv.split('_')[0], lv.split('_')[1].replace('sacrum', 'sacrum')
        add(id=f'lumbar_{lv}_extension', profile='lumbar', side='midline', kind='zxy', joint='spine', proximal=inf if inf != 'sacrum' else 'sacrum', moving=[sup],
            centre=M[f'disc_{lv}']['centre_m'], plane='sagittal', keys=sweep('flexion', 0.0001, O[key]['value']['mean'])[4:],
            context=[obs(O, key)], amplitude_basis='Level-specific extension during a lift (task context, not maximum flexibility); rotation about the disc marker as a fixed COR (moving COR not modelled)',
            marker=f'disc_{lv}', distal_marker=DISC_ABOVE[lv])
    for ch, key in (('flexion', 'thoracic_fe'), ('adduction', 'thoracic_lb'), ('internal', 'thoracic_ar')):
        hi = O[key]['value']['range_of_segment_pooled_means'][1]
        add(id=f'thoracic_t6_t7_{ch}', profile='thoracic', side='midline', kind='zxy', joint='spine', proximal='t7', moving=['t6'], centre=M['disc_t6_t7']['centre_m'],
            plane=ch, keys=sweep(ch, hi / 2, hi / 2), context=[obs(O, key)],
            amplitude_basis=f'Half of the upper pooled cadaver total ({hi} deg) each way; cadaver passive context', marker='disc_t6_t7',
            distal_marker='facet_t5_t6_left' if ch == 'internal' else 'disc_t5_t6')   # axial rotation: off-axis marker carried by t6
    primary = {'thumb_cmc': 'angle', 'tmj': 'angle', 'thumb': 'mcp', 'cervical_c4_c5_adduction': 'adduction', 'cervical_c4_c5_internal': 'internal', 'shoulder_complex': 'elevation', 'knee_flexion_with': 'flexion', 'hip_rotation': 'internal', 'forearm_rotation': 'pronation', 'gh_elevation': 'elevation', 'gh_axial': 'internal',
               'elbow_flexion': 'angle', 'digit': 'mcp', 'wrist_adduction': 'adduction', 'hip_abduction': 'adduction', 'thoracic_t6_t7_adduction': 'adduction',
               'thoracic_t6_t7_internal': 'internal'}
    for t in T:
        t['primary'] = next((v for k, v in primary.items() if t['id'].startswith(k)), None) or commanded_channels(t)[0]
        c = t['centre'] if t['kind'] != 'digit' else t['chain'][0]['centre']
        t['marker_is_centre'] = bool(t.get('marker') in M and np.linalg.norm(np.asarray(M[t['marker']]['centre_m']) - np.asarray(c)) < 1e-9)
    return T


def derive(spec, cmd):
    cmd = dict(cmd)
    if spec.get('derive') == 'screw_home':
        f = cmd.get('flexion', 0.0)
        cmd['internal'] = js.FOLLOWER_COUPLINGS['knee_screw_home']['magnitude_deg'] * min(max(f, 0.0), 20.0) / 20.0
    elif spec.get('derive') == 'shoulder_rhythm':
        c = js.FOLLOWER_COUPLINGS['scapulothoracic_rhythm']
        e = cmd.get('elevation', 0.0)
        k = e / c['gh_at_max_deg']
        cmd.update(upward=c['upward_rotation_per_gh_deg'] * e, tilt=c['max_scapular_plane']['posterior_tilt_deg'] * k,
                   scap_er=c['max_scapular_plane']['external_rotation_deg'] * k, clav_post=31.0 * k, clav_ret=c['clavicle_retraction_deg'] * k)
    return cmd


def series(spec):
    return [derive(spec, c) for c in ease(spec['keys'])]


def scapular_axes(spec):
    L = {k: np.asarray(v, float) for k, v in spec['landmarks'].items()}
    lat = np.array([S[spec['side']], 0, 0])
    Zs = unit(L['AA'] - L['TS'])
    Xs = unit(np.cross(L['AI'] - L['TS'], Zs))
    if Xs @ ANT < 0:
        Xs = -Xs
    Ys = np.cross(Zs, Xs)
    def signed(axis, probe_from, probe, want):
        R = rodrigues(axis, 5.0)
        moved = R @ (probe - probe_from)
        return 1.0 if (moved - (probe - probe_from)) @ want > 0 else -1.0
    ac = L['AC']
    up_s = signed(Xs, ac, L['AI'], lat)           # upward rotation swings the inferior angle laterally
    tilt_s = signed(Zs, ac, L['AI'], ANT)         # posterior tilt brings the inferior angle forward
    er_s = signed(Ys, ac, L['AA'] + 0.05 * lat, -ANT)   # external rotation moves the lateral end posteriorly
    clav_axis = unit(L['AC'] - L['SC'])
    clav_s = 1.0 if (rodrigues(clav_axis, 5.0) @ ANT)[2] > 0 else -1.0   # posterior rotation lifts the anterior surface
    ret_s = 1.0 if (rodrigues(UP, 5.0) @ clav_axis - clav_axis) @ (-ANT) > 0 else -1.0   # retraction moves the lateral clavicle posteriorly (test the change)
    return {'Xs': Xs, 'Ys': Ys, 'Zs': Zs, 'up': up_s, 'tilt': tilt_s, 'er': er_s, 'clav_axis': clav_axis, 'clav': clav_s, 'ret': ret_s}


def shoulder_rotations(spec, cmd):
    a = scapular_axes(spec)
    R_scap = rodrigues(a['Ys'], a['er'] * cmd.get('scap_er', 0.0)) @ rodrigues(a['Xs'], a['up'] * cmd.get('upward', 0.0)) @ rodrigues(a['Zs'], a['tilt'] * cmd.get('tilt', 0.0))
    R_clav = rodrigues(UP, a['ret'] * cmd.get('clav_ret', 0.0)) @ rodrigues(a['clav_axis'], a['clav'] * cmd.get('clav_post', 0.0))
    return R_clav, R_scap, a


# ----------------------------------------------------------------------------- command -> world deltas
def deltas(spec, cmd, F):
    """World-space rigid deltas (4x4, defined in the rest pose) for the top-level moving bones."""
    side = spec['side']
    kind = spec['kind']
    out = {}
    if kind == 'zxy':
        P0 = F[spec['proximal']] if spec['proximal'] != 'world' else js.WORLD_FRAME
        z, x, y = js.clinical_to_zxy(spec['joint'], side if side != 'midline' else 'right', cmd.get('flexion', 0.0), cmd.get('adduction', 0.0), cmd.get('internal', 0.0))
        R = js.world_delta(P0, js.zxy_matrix(z, x, y))
        for b in spec['moving']:
            out[b] = rigid(R, spec['centre'])
    elif kind == 'gh':
        R = js.world_delta(js.WORLD_FRAME, js.gh_command(side, cmd.get('plane', 0.0), cmd.get('elevation', 0.0), cmd.get('internal', 0.0)))
        out[spec['moving'][0]] = rigid(R, spec['centre'])
    elif kind == 'axis':
        R = rodrigues(spec['axis'], cmd.get('angle', 0.0))
        for b in spec['moving']:
            out[b] = rigid(R, spec['centre'])
    elif kind == 'elbow':
        Rf = rigid(rodrigues(spec['axis'], cmd.get('angle', 0.0)), spec['centre'])
        Rp = rigid(rodrigues(spec['pron_axis'], cmd.get('pronation', 0.0) * (1 if side == 'right' else -1) * -1.0), spec['pron_centre'])
        out[spec['moving'][0]] = Rf                      # ulna
        out[spec['moving'][1]] = Rf @ Rp                 # radius: pronate in rest space, then flex with the ulna
    elif kind == 'wrist':
        P0 = F[spec['proximal']]
        z, x, y = js.clinical_to_zxy('wrist', side, cmd.get('flexion', 0.0), cmd.get('adduction', 0.0), 0.0)
        R = half_rotation(js.world_delta(P0, js.zxy_matrix(z, x, y)))   # exact equal split: R_half @ R_half = R
        for b in spec['moving']:
            out[b] = rigid(R, spec['centre'])
        for b in spec['stage2']:
            out[b] = rigid(R, spec['centre2'])            # second half about the midcarpal centre, carried by stage 1
    elif kind == 'digit':
        for link in spec['chain']:
            P0 = F[link['proximal']]
            z, x, y = js.clinical_to_zxy('digit', side, cmd.get(link['joint'], 0.0), 0.0, 0.0)
            out[link['moving']] = rigid(js.world_delta(P0, js.zxy_matrix(z, x, y)), link['centre'])
    elif kind == 'tmj':
        R = rodrigues(spec['axis'], cmd.get('angle', 0.0))     # axis points to the character's left (+X): + swings the chin down = opening
        glide = unit(ANT - 0.5 * UP) * cmd.get('glide', 0.0)    # anteroinferior along the articular eminence (direction approximate)
        G = rigid(R, spec['centre'])
        G[:3, 3] += glide
        out[spec['moving'][0]] = G
    elif kind == 'shoulder_complex':
        R_clav, R_scap, a = shoulder_rotations(spec, cmd)
        L = spec['landmarks']
        G_clav = rigid(R_clav, L['SC'])
        ac_new = (G_clav @ np.append(L['AC'], 1.0))[:3]
        G_target = rigid(R_scap, L['AC'])            # thorax-relative scapular orientation about the AC joint...
        G_target[:3, 3] += ac_new - np.asarray(L['AC'])   # ...carried with the AC point as the clavicle retracts
        out[spec['moving'][0]] = G_clav
        out[spec['moving'][1]] = np.linalg.inv(G_clav) @ G_target
        R_gh = js.world_delta(js.WORLD_FRAME, js.gh_command(side, 40.0, cmd.get('elevation', 0.0), 0.0))
        out[spec['moving'][2]] = rigid(R_gh, L['GH'])
    return out


def measure(spec, pose, rest, F, markers_world):
    """Measured clinical angles from evaluated bone world matrices (pose/rest: bone -> 4x4)."""
    side = spec['side']
    kind = spec['kind']
    D = lambda b: pose[b] @ np.linalg.inv(rest[b])

    def seg(bid):
        if bid == 'world':
            return js.WORLD_FRAME, js.WORLD_FRAME
        return D(bid)[:3, :3] @ F[bid], F[bid]

    m = {}
    if kind in ('zxy', 'wrist'):
        P, P0 = seg(spec['proximal'])
        dist = spec['moving'][0] if kind == 'zxy' else spec['stage2'][2]
        Dd, D0 = seg(dist)
        R = js.relative_rotation(P, Dd, P0, D0)
        m.update(js.zxy_to_clinical(spec['joint'], side if side != 'midline' else 'right', *js.zxy_angles(R)))
        if kind == 'wrist':
            c2 = np.append(np.asarray(spec['centre2']), 1.0)
            m['midcarpal_centre_drift_m'] = float(np.linalg.norm((D(spec['stage2'][2]) @ c2)[:3] - (D(spec['moving'][1]) @ c2)[:3]))
    elif kind == 'gh':
        Rw = D(spec['moving'][0])[:3, :3]
        R = js.WORLD_FRAME.T @ Rw @ js.WORLD_FRAME
        m.update(js.gh_measure(side, R))
    elif kind in ('axis', 'elbow'):
        Rw = D(spec['moving'][0])[:3, :3]
        if 'intermetacarpal' in spec:
            im = spec['intermetacarpal']
            mc = spec['moving'][0]
            d1 = Rw @ unit(np.asarray(pose_dir(rest, mc)))
            m['intermetacarpal_angle_deg'] = intermetacarpal_angle(d1, np.asarray(im['mc2_dir']), np.asarray(im['plane_normal']))
        if kind == 'elbow':
            Rw_r = D(spec['moving'][1])[:3, :3]
            rel = Rw.T @ Rw_r                              # radius relative to ulna (pronation)
            ax = np.asarray(spec['pron_axis'])
            ang, res = axis_component(rel, ax)
            m['pronation'] = -ang * (1 if side == 'right' else -1)
            m['pronation_off_axis_deg'] = res
            rh = np.append(np.asarray(spec['pron_centre']), 1.0)       # radial head must stay on the capitulum
            m['humeroradial_drift_m'] = float(np.linalg.norm((D(spec['moving'][1]) @ rh)[:3] - rh[:3]))
        ang, res = axis_component(Rw, np.asarray(spec['axis']))
        m['angle'] = ang
        m['off_axis_deg'] = res
    elif kind == 'digit':
        for link in spec['chain']:
            P, P0 = seg(link['proximal'])
            Dd, D0 = seg(link['moving'])
            R = js.relative_rotation(P, Dd, P0, D0)
            c = js.zxy_to_clinical('digit', side, *js.zxy_angles(R))
            m[link['joint']] = c['flexion']
            m[link['joint'] + '_cross_talk_deg'] = max(abs(c['adduction']), abs(c['internal_rotation']))
    elif kind == 'tmj':
        Dm = D(spec['moving'][0])
        m['angle'], m['off_axis_deg'] = axis_component(Dm[:3, :3], np.asarray(spec['axis']))
        inc = np.append(np.asarray(spec['incisor']), 1.0)
        m['incisor_displacement_m'] = float(np.linalg.norm((Dm @ inc)[:3] - inc[:3]))
        cnd = np.append(np.asarray(spec['centre']), 1.0)
        m['condylar_displacement_m'] = float(np.linalg.norm((Dm @ cnd)[:3] - cnd[:3]))
        disp = (Dm @ cnd)[:3] - cnd[:3]
        m['condylar_glide_anterior_m'] = float(disp @ ANT)          # glide must be anterior...
        m['condylar_glide_inferior_m'] = float(-(disp @ UP))        # ...and inferior (down the articular eminence)
        m['glide'] = m['condylar_displacement_m']
    elif kind == 'shoulder_complex':
        L = {k: np.asarray(v, float) for k, v in spec['landmarks'].items()}
        Dc, Ds, Dh = D(spec['moving'][0]), D(spec['moving'][1]), D(spec['moving'][2])
        a = scapular_axes(spec)
        rel_scap = Ds[:3, :3]
        S0 = np.stack([a['Xs'], a['Ys'], a['Zs']], axis=1)
        er, up, tilt = yxz_angles(S0.T @ rel_scap @ S0)      # exact inverse of Ry(er) Rx(up) Rz(tilt) in the scapular frame
        m['scap_er_about_axis'], m['upward_about_axis'], m['tilt_about_axis'] = a['er'] * er, a['up'] * up, a['tilt'] * tilt
        Rc = Dc[:3, :3]
        theta = retraction_angle(Rc, a['clav_axis'])          # exact: the axial rotation leaves the clavicle axis fixed
        m['clav_ret'] = a['ret'] * theta
        m['clav_post'] = a['clav'] * axis_component(rodrigues(UP, theta).T @ Rc, a['clav_axis'])[0]
        Rgh = js.WORLD_FRAME.T @ (Ds[:3, :3].T @ Dh[:3, :3]) @ js.WORLD_FRAME
        g = js.gh_measure(side, Rgh)
        m['elevation'] = g['elevation']
        m['gh_plane'] = g['plane_of_elevation']
        down = Dh[:3, :3] @ np.array([0, 0, -1.0])
        m['humerothoracic_elevation'] = math.degrees(math.atan2(np.linalg.norm(np.cross(down, [0, 0, -1.0])), -down[2]))
        ac = np.append(L['AC'], 1.0)
        m['ac_closure_m'] = float(np.linalg.norm((Dc @ ac)[:3] - (Ds @ ac)[:3]))
        gh = np.append(L['GH'], 1.0)
        m['gh_centre_displacement_m'] = float(np.linalg.norm((Ds @ gh)[:3] - L['GH']))
        m['gh_centre_world_m'] = (Ds @ gh)[:3].tolist()
        m['gh_to_ac_distance_m'] = float(np.linalg.norm((Ds @ gh)[:3] - (Ds @ ac)[:3]))
    # joint-centre drift: the rest joint centre carried by the distal vs proximal segment
    c = np.append(np.asarray(spec['centre'] if kind != 'digit' else spec['chain'][0]['centre']), 1.0)
    prox = spec['proximal'] if kind != 'digit' else spec['chain'][0]['proximal']
    dist = spec['moving'][0] if kind != 'digit' else spec['chain'][0]['moving']
    if kind == 'shoulder_complex':
        prox, dist = spec['moving'][1], spec['moving'][2]      # GH centre: scapula-carried vs humerus-carried
    cp = (np.eye(4) if prox == 'world' else D(prox)) @ c
    cd = D(dist) @ c
    m['centre_drift_m'] = float(np.linalg.norm(cp[:3] - cd[:3]))
    if spec.get('marker_is_centre') and spec.get('marker') in markers_world:
        m['marker_vs_proximal_carried_centre_m'] = float(np.linalg.norm(np.asarray(markers_world[spec['marker']]) - cp[:3]))
    mov = spec['moving'][0] if kind != 'digit' else spec['chain'][0]['moving']
    m['moving_delta'] = D(mov).tolist()
    m['moving_deltas'] = {b: D(b).tolist() for b in moved_bones(spec)}   # every commanded bone, for the mirror check
    return m


def moved_bones(spec):
    """Every bone a spec commands: top-level moving bones, the second wrist stage and digit chain links."""
    out = list(spec.get('moving', [])) + list(spec.get('stage2', []))
    out += [link['moving'] for link in spec.get('chain', [])]
    return list(dict.fromkeys(out))


def retraction_angle(Rc, clav_axis):
    """Signed rotation about vertical carrying the rest clavicle axis to its posed direction (Rc = R_up R_axis)."""
    a0, a1 = np.asarray(clav_axis), Rc @ np.asarray(clav_axis)
    h0, h1 = a0 - (a0 @ UP) * UP, a1 - (a1 @ UP) * UP
    return math.degrees(math.atan2(np.cross(h0, h1) @ UP, h0 @ h1))


def pose_dir(rest, bone):
    """Rest head->tail direction of a bone from its rest matrix (Blender bone Y axis)."""
    return rest[bone][:3, 1]


def yxz_angles(R):
    """Inverse of Ry(a) Rx(b) Rz(c) (ISB scapulothoracic-style sequence), degrees."""
    b = math.degrees(math.asin(max(-1.0, min(1.0, -R[1, 2]))))
    a = math.degrees(math.atan2(R[0, 2], R[2, 2]))
    c = math.degrees(math.atan2(R[1, 0], R[1, 1]))
    return a, b, c


def axis_component(Rw, axis):
    """Signed rotation angle about `axis` and the residual off-axis rotation (deg)."""
    axis = unit(axis)
    q = rot_to_quat(Rw)
    w, v = q[0], q[1:]
    proj = v @ axis
    twist = np.array([w, *(proj * axis)])
    twist /= np.linalg.norm(twist)
    ang = math.degrees(2 * math.atan2(twist[1:] @ axis, twist[0]))
    swing = quat_mul(q, quat_conj(twist))
    res = math.degrees(2 * math.atan2(np.linalg.norm(swing[1:]), abs(swing[0])))   # well conditioned near zero
    return ((ang + 180) % 360) - 180, res


def rot_to_quat(R):
    t = np.trace(R)
    if t > 0:
        s = math.sqrt(t + 1) * 2
        return np.array([0.25 * s, (R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s])
    i = int(np.argmax([R[0, 0], R[1, 1], R[2, 2]]))
    j, k = (i + 1) % 3, (i + 2) % 3
    s = math.sqrt(1 + R[i, i] - R[j, j] - R[k, k]) * 2
    q = np.zeros(4)
    q[0] = (R[k, j] - R[j, k]) / s
    q[1 + i] = 0.25 * s
    q[1 + j] = (R[j, i] + R[i, j]) / s
    q[1 + k] = (R[k, i] + R[i, k]) / s
    return q


def quat_mul(a, b):
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    return np.array([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2, w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                     w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2])


def quat_conj(q):
    return np.array([q[0], -q[1], -q[2], -q[3]])


def commanded_channels(spec):
    k = spec['kind']
    if k == 'zxy' or k == 'wrist':
        if spec.get('derive') == 'screw_home':
            return ['flexion', 'internal']
        return [c for c in ('flexion', 'adduction', 'internal') if any(abs(kp.get(c, 0)) > 0 for kp in spec['keys'])]
    if k == 'gh':
        return ['plane', 'elevation', 'internal']
    if k == 'axis':
        return ['angle']
    if k == 'elbow':
        return ['angle', 'pronation']
    if k == 'shoulder_complex':
        return ['elevation', 'upward', 'tilt', 'scap_er', 'clav_post', 'clav_ret']
    if k == 'tmj':
        return ['angle']
    return [link['joint'] for link in spec['chain']]
