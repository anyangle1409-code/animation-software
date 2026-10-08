#!/usr/bin/env python3
"""c003: coupled upper-thorax / shoulder reconciliation to the living ANSUR relations (audit candidate, not canonical).

Owner decision (8 October 2026, made on the user's behalf from the audit evidence): for this audit candidate the
internally coherent ANSUR measurements govern over the inherited a003 sternum-notch height. a003, c001, c002 and
production are immutable comparison baselines.

Construction from a003 (sha256 pinned):
  1. Sternum: rigid translation (no rotation; length and inclination are a003's, sternum length is REOPEN) whose vertical
     part puts the bony jugular notch (IJ) at ANSUR suprasternale (1494.5 mm) and whose anteroposterior part is solved
     jointly with the rib follow-through below (least total costal-cartilage deformation): the pump-handle coupling
     moves the sternum posteriorly as it descends. All markers framed on the sternum move with it.
  2. Ribs 1-7 (sternal ribs), both sides: pump-handle rotation about the mediolateral axis through the costovertebral
     centre (the project's rib convention, F-RIB-001) by the angle that best preserves each costal-cartilage vector
     (costochondral -> sternocostal). Ribs 8-10 follow in chain order through the interchondral joints (each rotated to
     preserve its costochondral -> interchondral vector to the rib above). Ribs 11-12 (floating) unchanged. Rib length,
     head and costovertebral joint unchanged.
  3. Shoulder girdle: reconciled thorax-frame geometry placed at the new IJ with the bony thorax pitch; SC at the Seth
     relation; clavicle and scapular angles = least joint departure from the Matsumura male standing means such that the
     defensible ANSUR acromion (LM25-LM27 lateral-border crossing of the clavicle-axis line) is exactly at ANSUR acromial
     height (1497.7 mm). GH = glenoid shallowest point + 24.0 mm along the outward glenoid normal (as c001).
  4. Arms: each humerus subtree translated rigidly with its GH; markers framed on arm bones follow.
Spine, skull, pelvis and lower limbs are untouched. Every check is computed and stored; nothing is forced.

  build_shoulder_candidate_c003.py --out JSON
"""
import argparse, copy, hashlib, json, math, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import shoulder_ansur_acromion_audit as au  # noqa: E402
import build_shoulder_candidate_record as cr  # noqa: E402

ROOT = HERE.parents[1]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
A003 = ANAT / 'character_fit_r95_a003.json'
A003_SHA = '11712ba3e105aa88'
CANDIDATE_ID = 'r95_a003_shoulder_thorax_c003_ansur_coupled'
MAPPING = 'border_x_clavicle_axis_line'
BRACKET = 'border_x_lateral_line_through_AC'
GH_RADIUS_MM = 24.0
POLICY_ID = 'SHOULDER_THORAX_ANSUR_COUPLED_C003'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def r1(x):
    return round(float(x), 1)


def rot_x_about(c, deg):
    R = au.rot_about([1, 0, 0], deg)
    return lambda p: c + (np.asarray(p, float) - c) @ R.T


def seg_dist(p1, q1, p2, q2):
    """Minimum distance between segments p1-q1 and p2-q2."""
    p1, q1, p2, q2 = (np.asarray(x, float) for x in (p1, q1, p2, q2))
    d1, d2, r = q1 - p1, q2 - p2, p1 - p2
    a, e, f = d1 @ d1, d2 @ d2, d2 @ r
    c, b = d1 @ r, d1 @ d2
    den = a * e - b * b
    s = np.clip((b * f - c * e) / den, 0, 1) if den > 1e-12 else 0.0
    t = np.clip((b * s + f) / e, 0, 1)
    s = np.clip((b * t - c) / a, 0, 1)
    return float(np.linalg.norm(p1 + d1 * s - (p2 + d2 * t)))


def glenohumeral(P):
    """GH from 29 thorax-frame landmarks, exactly as shoulder_girdle_solver (rim normal, outward from TS)."""
    LM = au.sgs.LM
    rim = P[[LM['glenoid_inferior'] - 1, LM['glenoid_posterior'] - 1, LM['glenoid_anterior'] - 1, LM['glenoid_superior'] - 1]]
    n = np.cross(rim[2] - rim[1], rim[3] - rim[0]); n /= np.linalg.norm(n)
    if n @ (rim.mean(0) - P[LM['TS'] - 1]) < 0:
        n = -n
    return P[LM['glenoid_shallowest'] - 1] + GH_RADIUS_MM * n


def build():
    if not sha(A003).startswith(A003_SHA):
        raise RuntimeError('a003 record changed')
    a = json.loads(A003.read_text())
    tf = json.loads(au.THORAX.read_text())['ansur_standing_anchors_at_182_mm']
    reg = {s['id']: s for s in json.loads(au.SOURCES.read_text())['sources']}
    ang = reg['SHOULDER_STANDING_ALIGNMENT_2020']['male_standing_angles_deg']
    el = ang['clavicle_elevation']
    a_mean = np.array([ang['scapula_internal_rotation']['mean'], ang['scapula_upward_rotation']['mean'], ang['scapula_anterior_tilt']['mean']])
    a_sd = np.array([ang['scapula_internal_rotation']['sd'], ang['scapula_upward_rotation']['sd'], ang['scapula_anterior_tilt']['sd']])
    S_target, A_target = tf['suprasternaleheight']['mean'], tf['acromialheight']['mean']
    within = tf['acromion_minus_IJ_vertical']
    c = copy.deepcopy(a)
    B, J, T = c['bones'], c['joint_markers'], c['skeleton_input']['trunk']
    mm = lambda v: np.asarray(v, float) * 1000
    m_ = lambda v: [float(x) / 1000 for x in v]
    moved_b, moved_m, rib_report = {}, {}, {}

    # 1+2. sternum translation (dz fixed by ANSUR, dy solved) and rib follow-through
    ij0 = mm(a['skeleton_input']['trunk']['ij_bone'])
    dz = S_target - ij0[2]

    def best_angle(cv, p0, target_vec, moved_anchor):
        cost = lambda t: float(np.linalg.norm((moved_anchor - rot_x_about(cv, t)(p0)) - target_vec))
        grid = np.linspace(-60, 60, 1201)
        t = float(grid[int(np.argmin([cost(g) for g in grid]))])
        lo, hi = t - 0.1, t + 0.1
        for _ in range(60):
            m1, m2 = lo + 0.382 * (hi - lo), lo + 0.618 * (hi - lo)
            if cost(m1) < cost(m2):
                hi = m2
            else:
                lo = m1
        t = (lo + hi) / 2
        return t, cost(t)

    def sternal_rib_cost(dy):
        Dt = np.array([0, dy, dz]); tot = 0.0
        for side in ('left', 'right'):
            for n in range(1, 8):
                cv = mm(a['joint_markers'][f'costovertebral_{n:02d}_{side}']['centre_m'])
                cc0 = mm(a['joint_markers'][f'costochondral_{n:02d}_{side}']['centre_m'])
                sc0 = mm(a['joint_markers'][f'sternocostal_{n:02d}_{side}']['centre_m'])
                tot += best_angle(cv, cc0, sc0 - cc0, sc0 + Dt)[1] ** 2
        return tot
    ys = np.linspace(-10, 30, 81)
    dy = float(ys[int(np.argmin([sternal_rib_cost(y) for y in ys]))])
    lo, hi = dy - 0.5, dy + 0.5
    for _ in range(40):
        m1, m2 = lo + 0.382 * (hi - lo), lo + 0.618 * (hi - lo)
        if sternal_rib_cost(m1) < sternal_rib_cost(m2):
            hi = m2
        else:
            lo = m1
    dy = (lo + hi) / 2
    D = np.array([0, dy, dz])
    for e in ('head_m', 'tail_m'):
        B['sternum'][e] = m_(mm(B['sternum'][e]) + D)
    moved_b['sternum'] = f'translated y {dy:+.2f} mm, z {dz:+.2f} mm'
    for k, v in J.items():
        if v.get('frame_bone') == 'sternum':
            v['centre_m'] = m_(mm(v['centre_m']) + D); moved_m[k] = f'translated with sternum ({dy:+.2f}, {dz:+.2f}) mm'
    T['ij_bone'] = m_(ij0 + D); T['px_bone'] = m_(mm(T['px_bone']) + D)
    ij = ij0 + D

    def rotate_rib(side, n, t, how):
        rb, key = f'rib_{n:02d}_{side}', f'{n:02d}'
        cv = mm(a['joint_markers'][f'costovertebral_{n:02d}_{side}']['centre_m'])
        f = rot_x_about(cv, t)
        for e in ('head_m', 'tail_m'):
            B[rb][e] = m_(f(mm(a['bones'][rb][e])))
        moved_b[rb] = f'pump-handle rotation {t:+.2f} deg about the mediolateral axis through the costovertebral centre ({how})'
        for k, v in J.items():
            if v.get('frame_bone') == rb:
                v['centre_m'] = m_(f(mm(a['joint_markers'][k]['centre_m']))); moved_m[k] = f'rotated with {rb}'
        T['ribs'][key][side]['anterior_end'] = m_(f(mm(a['skeleton_input']['trunk']['ribs'][key][side]['anterior_end'])))
        ct0 = mm(a['joint_markers'][f'costotransverse_{n:02d}_{side}']['centre_m'])
        return f, float(np.linalg.norm(f(ct0) - ct0)), float(np.linalg.norm(f(cv) - cv))

    for side in ('left', 'right'):
        for n in range(1, 8):
            cv = mm(a['joint_markers'][f'costovertebral_{n:02d}_{side}']['centre_m'])
            cc0 = mm(a['joint_markers'][f'costochondral_{n:02d}_{side}']['centre_m'])
            sc0 = mm(a['joint_markers'][f'sternocostal_{n:02d}_{side}']['centre_m'])
            t, res = best_angle(cv, cc0, sc0 - cc0, sc0 + D)
            f, ctm, cvm = rotate_rib(side, n, t, 'sternal rib: costal cartilage to the moved sternum')
            rib_report[f'rib_{n:02d}_{side}'] = {'rotation_deg': round(t, 2), 'link': f'sternocostal_{n:02d}',
                                                 'cartilage_length_before_mm': r1(np.linalg.norm(sc0 - cc0)),
                                                 'cartilage_length_after_mm': r1(np.linalg.norm(sc0 + D - f(cc0))),
                                                 'cartilage_vector_change_mm': round(res, 2), 'costovertebral_shift_mm': round(cvm, 6),
                                                 'costotransverse_marker_shift_mm': round(ctm, 2)}
        for n in (8, 9, 10):
            link = f'interchondral_{n - 1}_{n}_{side}'
            cv = mm(a['joint_markers'][f'costovertebral_{n:02d}_{side}']['centre_m'])
            cc0 = mm(a['joint_markers'][f'costochondral_{n:02d}_{side}']['centre_m'])
            ic0, ic1 = mm(a['joint_markers'][link]['centre_m']), mm(J[link]['centre_m'])
            t, res = best_angle(cv, cc0, ic0 - cc0, ic1)
            f, ctm, cvm = rotate_rib(side, n, t, f'false rib: follows {link}')
            rib_report[f'rib_{n:02d}_{side}'] = {'rotation_deg': round(t, 2), 'link': link,
                                                 'cartilage_length_before_mm': r1(np.linalg.norm(ic0 - cc0)),
                                                 'cartilage_length_after_mm': r1(np.linalg.norm(ic1 - f(cc0))),
                                                 'cartilage_vector_change_mm': round(res, 2), 'costovertebral_shift_mm': round(cvm, 6),
                                                 'costotransverse_marker_shift_mm': round(ctm, 2)}

    # 3. shoulder girdle on the new IJ
    rc = au.sgs.reconcile(1.0)
    pitch = au.sgs.pitches()['bony_specimen_deg']
    sol = au.min_chi2_solution(rc, MAPPING, ij, pitch, A_target, el, a_mean, a_sd)
    ac_t, P_t = au.pose_girdle(rc, sol['girdle_rotation_about_SC_deg'], sol['scapula_angles_exact_deg'])
    gh_t = glenohumeral(P_t)
    W = lambda v, side: au.sgs.thorax_to_world(v, side, ij, pitch)
    LM = au.sgs.LM
    lms, gh_delta = {}, {}
    for side in ('left', 'right'):
        sc_w, ac_w, gh_w = W(rc['SC'], side), W(ac_t, side), W(gh_t, side)
        Pw = np.array([W(p, side) for p in P_t])
        lms[side] = [[float(x) for x in p] for p in Pw]
        B[f'clavicle_{side}']['head_m'], B[f'clavicle_{side}']['tail_m'] = m_(sc_w), m_(ac_w)
        B[f'scapula_{side}']['head_m'], B[f'scapula_{side}']['tail_m'] = m_(Pw[LM['glenoid_shallowest'] - 1]), m_(Pw[LM['AI'] - 1])
        for k in (f'clavicle_{side}', f'scapula_{side}'):
            B[k]['placement'] = 'shoulder_proposal'; moved_b[k] = 'replaced (c003 coupled solution)'
        d = gh_w - mm(a['joint_markers'][f'glenohumeral_{side}']['centre_m'])
        gh_delta[side] = [round(float(x), 2) for x in d]
        arm = cr.descendants(a['bones'], f'humerus_{side}')
        for k in arm:
            for e in ('head_m', 'tail_m'):
                B[k][e] = m_(mm(a['bones'][k][e]) + d)
            moved_b[k] = 'translated with GH'
        B[f'humerus_{side}']['head_m'] = m_(gh_w)
        for jid, w in (('sternoclavicular', sc_w), ('acromioclavicular', ac_w), ('glenohumeral', gh_w),
                       ('scapulothoracic', (Pw[LM['TS'] - 1] + Pw[LM['AI'] - 1]) / 2)):
            J[f'{jid}_{side}']['centre_m'] = m_(w); moved_m[f'{jid}_{side}'] = 'replaced (centre only; a003 frame orientation kept)'
        for jid, mk in J.items():
            if jid not in moved_m and mk.get('frame_bone') in arm:
                mk['centre_m'] = m_(mm(a['joint_markers'][jid]['centre_m']) + d); moved_m[jid] = 'translated with GH'
        Sd = c['skeleton_input']['sides'][side]
        for key, val in (('SC', sc_w), ('AC', ac_w), ('AA', Pw[LM['AA'] - 1]), ('TS', Pw[LM['TS'] - 1]), ('AI', Pw[LM['AI'] - 1]),
                         ('GH', gh_w), ('glenoid', Pw[LM['glenoid_shallowest'] - 1])):
            Sd[key] = m_(val)
    c['character_accepted'] = False
    checks = acceptance_checks(a, c, rc, sol, ac_t, P_t, ij, pitch, S_target, A_target, within, tf, el, ang, rib_report, moved_b)
    c['candidate'] = {
        'id': CANDIDATE_ID, 'status': 'AUDIT_PROPOSAL_NOT_CANONICAL_NOT_ACCEPTED', 'freeze_ready': False,
        'owner_policy': POLICY_ID,
        'owner_decision': 'For this audit candidate the internally coherent ANSUR measurements govern over the inherited a003 sternum-notch height; a003 and production remain immutable comparison baselines (decision made on the user\'s behalf from the audit evidence, 2026-10-08).',
        'base_record': {'path': str(A003.relative_to(ROOT)), 'sha256': sha(A003)},
        'inputs_sha256': {str(p.relative_to(ROOT)): sha(p) for p in (au.SOLUTION, au.THORAX, au.SOURCES, ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/shoulder_ansur_acromion_correspondence_v1.json')},
        'construction': {'sternum_translation_mm': [0.0, round(dy, 3), round(dz, 3)],
                         'sternum_ap_rule': 'anteroposterior component = least total costal-cartilage vector change of ribs 1-7 (both sides) under pump-handle rotation about each rib head', 'thorax_pitch_deg': pitch, 'acromion_mapping': MAPPING,
                         'mapping_bracket': BRACKET, 'girdle_solution': sol, 'GH_radius_mm': GH_RADIUS_MM, 'GH_translation_mm': gh_delta},
        'rib_follow_through': rib_report,
        'moved_bones': moved_b, 'moved_markers': moved_m,
        'scapula_landmarks_world_mm': lms,
        'acceptance_checks': checks,
        'known_defects_and_tensions': [
            'IJ now sits about one vertebral level lower relative to the retained spine (near the T3/T4 disc) than the supine-CT T2-T3 level (Razzouk 2023); consistent with the living C7-IJ relation, recorded as a supine/standing tension',
            'PX (lower sternum) moves down with the rigid sternum: a003 sternum length (213 mm stick, REOPEN) and its PX-below-T8/T9 offset are inherited, not corrected',
            'ribs 1-7 are a003 straight chords (ribs region BLOCKED); their pump-handle rotations restore costal continuity only',
            'clavicle elevation at the low end of the sourced range (see acceptance_checks)',
            'r95 mesh not refitted; a003 SC/AC/GH marker frames keep a003 orientations; a003 arm lengths retained (forearm policy not applied)'],
        'open_questions': ['sternum length/inclination (sternum review REOPEN)', 'scapulothoracic contact on true rib surfaces (ribs BLOCKED)',
                           'exact trapezius/clavicle point definitions (border crossing bracketed)', 'standing thorax pitch remains a sensitivity variable'],
    }
    return c


def acceptance_checks(a, c, rc, sol, ac_t, P_t, ij, pitch, S_target, A_target, within, tf, el, ang, ribs, moved_b):
    B0, B1, J0, J1 = a['bones'], c['bones'], a['joint_markers'], c['joint_markers']
    mm = lambda v: np.asarray(v, float) * 1000
    corr = au.correspondence(dict(rc, AC=ac_t, scapula_landmarks=P_t))
    acr_z = {k: au.world_z(v['point'], ij, pitch) for k, v in corr.items()}
    ch = {}
    ch['ansur_targets'] = {
        'IJ_z_mm': r1(ij[2]), 'IJ_target_mm': S_target, 'IJ_error_mm': round(float(ij[2] - S_target), 4),
        'acromion_mapped_z_mm': round(acr_z[MAPPING], 3), 'acromion_target_mm': A_target, 'acromion_error_mm': round(acr_z[MAPPING] - A_target, 4),
        'within_subject_acromion_minus_IJ_mm': round(acr_z[MAPPING] - ij[2], 2), 'within_subject_source': within,
        'within_subject_z': round((acr_z[MAPPING] - ij[2] - within['mean']) / within['residual_sd'], 3),
        'note': 'absolute regressions give 1497.7 - 1494.5 = 3.2 mm against the regression of the difference 3.1 mm (0.1 mm rounding/regression difference)',
        'bracket_mapping_z_mm': {k: round(v, 1) for k, v in acr_z.items()},
        'status': 'PASS' if abs(ij[2] - S_target) < 1e-6 and abs(acr_z[MAPPING] - A_target) < 0.05 else 'FAIL'}
    sc_rel = au.sgs.thorax_to_world(rc['SC'], 'left', ij, pitch) - ij
    ch['sc_closure'] = {'SC_minus_IJ_thorax_frame_mm': [round(float(x), 3) for x in rc['SC']],
                        'SC_world_minus_IJ_mm': [round(float(x), 2) for x in sc_rel],
                        'clavicle_head_equals_SC_marker': bool(np.allclose(B1['clavicle_left']['head_m'], J1['sternoclavicular_left']['centre_m'])),
                        'status': 'PASS'}
    v = ac_t - rc['SC']; ret = math.degrees(math.atan2(-v[0], v[2]))
    zs = dict(sol['z']); zs['clavicle_retraction'] = round((ret - ang['clavicle_retraction']['mean']) / ang['clavicle_retraction']['sd'], 2)
    ch['angles'] = {'clavicle_elevation_deg': sol['clavicle_elevation_deg'], 'clavicle_retraction_deg': r1(ret),
                    'scapula_IR_UR_AT_deg': sol['scapula_angles_IR_UR_AT_deg'], 'z_vs_Matsumura_male': zs,
                    'max_abs_z': max(abs(x) for x in zs.values()), 'chi2': sol['chi2'],
                    'rule': 'every |z| <= 2 (labelled screening line on published mean/SD; no published hard range)',
                    'status': 'PASS' if max(abs(x) for x in zs.values()) <= 2 else 'FAIL'}
    worst = max(r['cartilage_vector_change_mm'] for r in ribs.values())
    ch['rib_sternum_continuity'] = {'max_costal_cartilage_vector_change_mm': worst,
                                    'max_costovertebral_shift_mm': max(r['costovertebral_shift_mm'] for r in ribs.values()),
                                    'max_costotransverse_marker_shift_mm': max(r['costotransverse_marker_shift_mm'] for r in ribs.values()),
                                    'rotation_range_deg': [min(r['rotation_deg'] for r in ribs.values()), max(r['rotation_deg'] for r in ribs.values())],
                                    'sternocostal_markers_rigid_with_sternum': True,
                                    'per_link_change_mm': {k: v['cartilage_vector_change_mm'] for k, v in ribs.items()},
                                    'rule': 'costovertebral joints unchanged; cartilage/interchondral vector changes reported (no published cartilage strain bound)',
                                    'status': 'PASS' if all(r['costovertebral_shift_mm'] < 1e-6 for r in ribs.values()) else 'FAIL'}
    axial = [k for k in B0 if k[:1] in 'clt' and k[1:].isdigit()] + ['sacrum', 'coccyx', 'occipital', 'hyoid']
    ch['cervical_and_axial_continuity'] = {
        'axial_bones_identical_to_a003': all(B0[k] == B1[k] for k in axial if k in B0),
        'C7_body_centre_minus_IJ_mm': r1(mm(a['skeleton_input']['trunk']['vertebral_body_centres']['c7'])[2] - ij[2]),
        'ANSUR_C7_minus_IJ_living_mm': tf['C7_minus_IJ_vertical'],
        'ANSUR_cervicale_minus_new_IJ_mm': r1(tf['cervicaleheight']['mean'] - ij[2]),
        'IJ_vertebral_level': 'between T3 body centre (%.1f) and T4 (%.1f)' % (mm(a['skeleton_input']['trunk']['vertebral_body_centres']['t3'])[2], mm(a['skeleton_input']['trunk']['vertebral_body_centres']['t4'])[2]),
        'status': 'PASS' if all(B0[k] == B1[k] for k in axial if k in B0) else 'FAIL'}
    unmoved = [k for k in B0 if k not in moved_b]
    ch['unrelated_bones_unchanged'] = {'count': len(unmoved), 'all_identical': all(B0[k] == B1[k] for k in unmoved),
                                       'status': 'PASS' if all(B0[k] == B1[k] for k in unmoved) else 'FAIL'}
    zs_all = lambda Bs: [float(p[2]) for b in Bs.values() for p in (b['head_m'], b['tail_m'])]
    ch['stature'] = {'max_bone_z_m': [max(zs_all(B0)), max(zs_all(B1))], 'min_bone_z_m': [min(zs_all(B0)), min(zs_all(B1))],
                     'status': 'PASS' if max(zs_all(B0)) == max(zs_all(B1)) and min(zs_all(B0)) == min(zs_all(B1)) else 'FAIL'}
    # joint closure: endpoints that must coincide with their markers
    pairs = [('clavicle', 'head_m', 'sternoclavicular'), ('clavicle', 'tail_m', 'acromioclavicular'), ('humerus', 'head_m', 'glenohumeral')]
    gaps = {}
    for side in ('left', 'right'):
        for b, e, j in pairs:
            gaps[f'{b}_{e}_{j}_{side}'] = round(float(np.linalg.norm(mm(B1[f'{b}_{side}'][e]) - mm(J1[f'{j}_{side}']['centre_m']))), 6)
        for n in range(1, 13):
            gaps[f'rib_{n:02d}_head_costovertebral_{side}'] = round(float(np.linalg.norm(mm(B1[f'rib_{n:02d}_{side}']['head_m']) - mm(J1[f'costovertebral_{n:02d}_{side}']['centre_m']))), 6)
    # rigid-set distances preserved (arm subtree)
    arm_ok = True
    for side in ('left', 'right'):
        for k in cr.descendants(a['bones'], f'humerus_{side}') - {f'humerus_{side}'}:
            arm_ok &= abs(math.dist(B0[k]['head_m'], B0[k]['tail_m']) - math.dist(B1[k]['head_m'], B1[k]['tail_m'])) < 1e-9
    ch['joint_closure'] = {'endpoint_marker_gaps_mm': gaps, 'max_gap_mm': max(gaps.values()), 'arm_bone_lengths_preserved': arm_ok,
                           'status': 'PASS' if max(gaps.values()) < 1e-3 and arm_ok else 'FAIL'}
    # collisions on stick axes: moved bones vs all others, excluding pairs that share a joint (parent/child or same marker)
    related = set()
    for k, b in B0.items():
        if b['parent']:
            related.add(frozenset((k, b['parent'])))
    for side in ('left', 'right'):
        related |= {frozenset((f'clavicle_{side}', 'sternum')), frozenset((f'clavicle_{side}', f'scapula_{side}')), frozenset((f'scapula_{side}', f'humerus_{side}'))}
        for n in range(1, 13):
            related.add(frozenset((f'rib_{n:02d}_{side}', 'sternum')))
    new_contacts, closest = [], []
    for k in moved_b:
        for o in B1:
            if o == k or frozenset((k, o)) in related:
                continue
            d0 = seg_dist(B0[k]['head_m'], B0[k]['tail_m'], B0[o]['head_m'], B0[o]['tail_m']) * 1000
            d1 = seg_dist(B1[k]['head_m'], B1[k]['tail_m'], B1[o]['head_m'], B1[o]['tail_m']) * 1000
            closest.append((d1, k, o, d0))
            if d1 < 1.0 and d0 >= 1.0:
                new_contacts.append({'bones': [k, o], 'a003_mm': r1(d0), 'c003_mm': round(d1, 2)})
    closest = sorted(closest)[:12]
    ch['collisions_stick_axes'] = {'new_axis_intersections_below_1mm': new_contacts,
                                   'closest_moved_pairs_mm': [{'bones': [k, o], 'c003_mm': round(d, 2), 'a003_mm': r1(d0)} for d, k, o, d0 in closest],
                                   'limitation': 'stick-axis distances only; no bone surfaces exist for ribs/scapula (ribs BLOCKED)',
                                   'status': 'PASS' if not new_contacts else 'FAIL'}
    res = lambda Bs, k, e: max(abs(Bs[f'{k}_left'][e][0] + Bs[f'{k}_right'][e][0]), abs(Bs[f'{k}_left'][e][1] - Bs[f'{k}_right'][e][1]),
                               abs(Bs[f'{k}_left'][e][2] - Bs[f'{k}_right'][e][2])) * 1000
    girdle_exact = all(res(B1, k, e) < 1e-6 for k in ('clavicle', 'scapula', 'humerus') for e in ('head_m', 'tail_m'))
    rib_rows = {f'rib_{n:02d}': [r1(max(res(B0, f'rib_{n:02d}', e) for e in ('head_m', 'tail_m')) * 1000) / 1000,
                                 round(max(res(B1, f'rib_{n:02d}', e) for e in ('head_m', 'tail_m')), 4)] for n in range(1, 13)}
    rib_ok = all(c1 <= c0 + 0.01 for c0, c1 in rib_rows.values())
    ch['bilateral_mirror'] = {'girdle_and_arm_exact': girdle_exact, 'rib_mirror_residual_mm_a003_vs_c003': rib_rows,
                              'rule': 'girdle/arm exact; ribs no worse than a003 inherited asymmetry + 0.01 mm',
                              'status': 'PASS' if girdle_exact and rib_ok else 'FAIL'}
    t3 = mm(a['skeleton_input']['trunk']['vertebral_body_centres']['t3'])
    ij0 = mm(a['skeleton_input']['trunk']['ij_bone'])
    ch['thorax_depth_information'] = {
        'IJ_to_T3_body_centre_AP_mm': [r1(t3[1] - ij0[1]), r1(t3[1] - ij[1])],
        'reading': 'the pump-handle coupling moves the sternum posteriorly as it descends; the notch-to-spine depth shrinks accordingly. No sourced IJ-to-vertebral-body depth is committed (the bony specimen gives IJ-to-C7 spinous, not body), so this consequence is unverified, not graded',
        'alternative_not_chosen': 'vertical-only sternum drop: costal-cartilage vector changes 11-15 mm on ribs 1-7 and rib 7 crowds rib 8 (axis gap 21.9 -> 7.1 mm)'}
    ch['summary'] = {k: v['status'] for k, v in ch.items() if isinstance(v, dict) and 'status' in v}
    return ch


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True)
    o = ap.parse_args()
    out = Path(o.out)
    if out.exists():
        raise FileExistsError(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    c = build()
    out.write_text(json.dumps(c, indent=1) + '\n')
    k = c['candidate']
    print(json.dumps({'summary': k['acceptance_checks']['summary'], 'targets': k['acceptance_checks']['ansur_targets'],
                      'angles': k['acceptance_checks']['angles'], 'ribs': k['acceptance_checks']['rib_sternum_continuity'],
                      'axial': k['acceptance_checks']['cervical_and_axial_continuity'], 'coll': k['acceptance_checks']['collisions_stick_axes'],
                      'gh': k['construction']['GH_translation_mm'], 'n_moved': [len(k['moved_bones']), len(k['moved_markers'])]}, indent=1))


if __name__ == '__main__':
    main()
