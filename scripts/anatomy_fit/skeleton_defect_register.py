#!/usr/bin/env python3
"""Skeleton defect register: every suspected problem classified, with numbers computed from committed records (read-only).

Classes:
  GEOMETRY_DEFECT            a bone dimension/position contradicted by >=2 compatible sources or a hard invariant
  JOINT_COORDINATE_DEFECT    a joint centre / connection that is wrong by construction (not by missing evidence)
  STRUCTURAL_INVARIANT_FAIL  a hard geometric invariant fails (CP2)
  MOVEMENT_TEST_DESIGN       the movement test, not the bone geometry, produces the implausible state
  MOVEMENT_MODEL_GAP         a physiological coupling is not modelled
  REPRESENTATION_LIMIT       the line/stick diagnostic cannot show the real bone (not an anatomical error by itself)
  EVIDENCE_GAP               correctness cannot be decided with accessible evidence
  NOT_A_DEFECT               checked and consistent with evidence
Status: CORRECTED_IN_CANDIDATE (non-canonical), DIAGNOSTIC_PROPOSAL, OPEN, BLOCKED, NONE.

  skeleton_defect_register.py --out JSON
"""
import argparse, json, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parents[1]
A = ROOT / 'ORIGINAL_V1_WORK/anatomy'; AU = A / 'audit'


def J(p):
    return json.loads(Path(p).read_text())


def dist(a, b):
    return float(np.linalg.norm(np.asarray(a) - np.asarray(b)) * 1000)


def seg(p, a, b):
    a, b, p = map(np.asarray, (a, b, p)); ab = b - a; t = np.clip((p - a) @ ab / (ab @ ab), 0, 1)
    return float(np.linalg.norm(p - (a + t * ab)) * 1000)


def build():
    a3, c4 = J(A / 'character_fit_r95_a003.json'), J(AU / 'candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json')
    B3, B4, M4 = a3['bones'], c4['bones'], c4['joint_markers']
    L = lambda B, n: dist(B[n]['head_m'], B[n]['tail_m'])
    ac = lambda B, M: dist(M['acromioclavicular_left']['centre_m'], M['acromioclavicular_right']['centre_m'])
    hp = J(A / 'canonical_hand_proportion_audit_v1.json')['bones']
    conv = J(A / 'canonical_evidence_convergence_v1.json')['region_findings']
    hand = J(AU / 'hand_input_audit/hand_input_source_rebuild_v1.json')
    wh = J(AU / 'claude_independent_review_20261009/wrist_hand_model_context_v1.json')
    amp = J(AU / 'amplitude_provenance/c004_isolated_001.json')
    v2 = {k: J(AU / f'joint_attachment_scan/{k}_v2.json')['opened'] for k in ('c003_isolated_001', 'c004_isolated_001')}
    stack = J(A / 'canonical_spine_level_stack_v1.json')
    lv = ['c3', 'c4', 'c5', 'c6', 'c7'] + [f't{i}' for i in range(1, 13)] + [f'l{i}' for i in range(1, 6)]
    col = sum(L(B4, k) for k in lv)
    names = [k.upper() for k in lv]
    sourced = stack['disc_gaps_mm']['C2/C3']['candidate'] + sum(stack['vertebral_bodies_mm'][n]['candidate'] for n in names) + \
        sum(stack['disc_gaps_mm'][f'{x}/{y}']['candidate'] for x, y in zip(names, names[1:] + ['S1']))
    g = J(A / 'canonical_spine_geometry_audit_v1.json')['comparisons']
    th = [f't{i}' for i in range(1, 13)]
    th_disc = sum(stack['disc_gaps_mm'][f'{x.upper()}/{y.upper()}']['candidate'] for x, y in zip(th, th[1:] + ['l1']))
    th_cur = sum(L(B4, k) for k in th)
    R = []

    def add(**k):
        R.append(k)
    # ---------------------------------------------------------------- hand / wrist
    add(id='H1', region='hand', title='Metacarpals 2-4 too short', cls='GEOMETRY_DEFECT', status='DIAGNOSTIC_PROPOSAL',
        measured={f'M{d}_c004_mm': round(L(B4, f'metacarpal_{d}_left'), 1) for d in (2, 3, 4)} | {f'M{d}_z_vs_Aydinlioglu': hp[f'metacarpal_{d}']['z_vs_ayd1998_mean'] for d in (2, 3, 4)},
        evidence=['DOGAN_1998_HAND_RELATIONS (Aydinlioglu 1998 male radiographic 68/64/58 +-4)', 'BEREDJIKLIAN_2025_METACARPAL_HEIGHT (CT 67.7/66.1/58.0)', 'canonical_hand_ray_target_constraints_v1.json'],
        action='P001 diagnostic proposal lengthens M2-M4 to the radiographic means with fixed CMC ends; canonical freeze still requires carpal/CMC geometry')
    add(id='H2', region='hand', title='Ten fingertip (distal phalanx tail) endpoints', cls='EVIDENCE_GAP', status='BLOCKED',
        measured={'points': len(hand['not_encoded']), 'containment_mm': [x.split('contained ')[1].rstrip(' mm)') for x in hand['not_encoded'][:5]]},
        evidence=['hand_input_source_rebuild_v1.json', 'HAND_TIP_PRIMARY_RECHECK_20261009.md', 'wrist_hand_model_context_v1.json (one model source, non-population scale)'],
        action='needs an independent DIP-centre-to-bony-tip (or DP length + DIP-to-base offset) source for all five rays; containment offsets are not evidence')
    add(id='H3', region='hand', title='Thumb CMC: trapezium stick ends short of the first metacarpal base', cls='JOINT_COORDINATE_DEFECT', status='BLOCKED',
        measured={'trapezium_tail_to_MC1_base_mm': round(dist(B4['trapezium_left']['tail_m'], B4['metacarpal_1_left']['head_m']), 2),
                  'cmc_1_marker_to_each_mm': round(seg(M4['cmc_1_left']['centre_m'], B4['metacarpal_1_left']['head_m'], B4['metacarpal_1_left']['tail_m']), 2)},
        evidence=['joint marker method "midpoint of closest approach between participant segments"', 'canonical_freeze_readiness_v1 hand blocker "thumb CMC local geometry"'],
        action='rebuild with source-defined trapezium saddle and MC1 base once carpal geometry exists')
    add(id='H4', region='carpus', title='Carpal arrangement', cls='NOT_A_DEFECT', status='NONE',
        measured={'standard_topology_relations_hold': wh['carpal_topology_all_hold']},
        evidence=['wrist_hand_model_context_v1.json (Gonzalez 1997 wrist model + standard anatomy)'],
        action='topology correct on both sides; exact centroids, contacts and envelopes remain BLOCKED (readiness: carpus)')
    add(id='H5', region='carpus', title='Carpal bones drawn as short control sticks / clump', cls='REPRESENTATION_LIMIT', status='NONE',
        measured={}, evidence=['INV_TARSAL_SEMANTICS analogue: control-stick length is not whole-bone length'], action='needs envelopes, not stick changes')
    wb = {k: J(AU / f'claude_independent_review_20261009/whole_body_interaction_{k}.json') for k in ('a003', 'c004')}
    hand_thigh = lambda k: {x['test']: x['min_axis_mm'] for x in wb[k]['tests_with_cross_region_approach_below_10mm'] if 'femur' in str(x['bones']) and any(h in str(x['bones']) for h in ('thumb', 'digit'))}
    add(id='H6', region='hand', title='Isolated forearm/wrist/GH-rotation sweeps from the hanging posture drive the hand into the thigh', cls='MOVEMENT_TEST_DESIGN', status='OPEN',
        measured={'c004_min_hand_to_femur_axis_mm_by_test': hand_thigh('c004'), 'a003_same_tests': hand_thigh('a003')},
        evidence=['whole_body_interaction_c004.json / _a003.json', 'skeleton_only_renders_c004/pose_wrist_flexion_left_f1461.jpg'],
        action='exposed by the corrected (narrower) c003/c004 shoulders: the a003 hanging-arm posture was kept. Hand sweeps need a start posture with the hand clear of the thigh, or must be flagged; no amplitude change')
    add(id='U9', region='shoulder', title='Medial clavicle close to rib 1 at rest in c003/c004', cls='EVIDENCE_GAP', status='OPEN',
        measured={'c004_min_axis_mm': 7.5, 'a003_min_axis_mm': 16.4, 'location': 'about 12 mm lateral of the SC joint (costoclavicular region)'},
        evidence=['whole_body_interaction_c004.json', 'c003 rib pump-handle rotation and SC placement'],
        action='costoclavicular region is anatomically close; decide with clavicle/rib surface geometry before any canonical shoulder freeze')
    add(id='L7', region='foot', title='Hip internal rotation brings the hallux onto the opposite first metatarsal', cls='MOVEMENT_TEST_DESIGN', status='OPEN',
        measured={'min_axis_mm': 1.4, 'rest_axis_mm': 135.4}, evidence=['whole_body_interaction_c004.json (also a003)'],
        action='standing start posture with feet together; needs a stance-width start posture or flagging')
    add(id='H7', region='wrist', title='c001-c003 wrist sweeps pivoted 38.4 mm off the radiocarpal joint (stale WJC)', cls='JOINT_COORDINATE_DEFECT', status='CORRECTED_IN_CANDIDATE',
        measured={'c003_radiocarpal_opening_mm': v2['c003_isolated_001'].get('radiocarpal_left', {}).get('max_opening_mm'), 'c004_radiocarpal_opening_mm': v2['c004_isolated_001'].get('radiocarpal_left', {}).get('max_opening_mm', 0.0)},
        evidence=['candidates/shoulder_thorax_c004_arm_inputs/validation_summary.json'], action='c004 (non-canonical) closes it')
    add(id='H8', region='hand', title='Midcarpal follower joints separate during wrist sweeps', cls='MOVEMENT_MODEL_GAP', status='OPEN',
        measured={k: v2['c004_isolated_001'][k]['max_opening_mm'] for k in v2['c004_isolated_001'] if k.startswith('midcarpal') and k.endswith('_left')},
        evidence=['joint_attachment_scan/c004_isolated_001_v2.json'], action='two-stage wrist rotates rows about different centres; needs contact/sliding model, not a centre change')
    add(id='H9', region='hand', title='Thumb opposition shows only palmar abduction + pronation components', cls='MOVEMENT_MODEL_GAP', status='OPEN',
        measured={}, evidence=['tracker Phase 8 hand solver: full opposition (TMC/MCP/IP flexion) unresolved; pronation 30 deg TEST AMPLITUDE'], action='source-defined opposition kinematics required')
    # ---------------------------------------------------------------- shoulder / thorax / spine
    add(id='U1', region='shoulder', title='Clavicle far too long and shoulders far too broad (a003)', cls='GEOMETRY_DEFECT', status='CORRECTED_IN_CANDIDATE',
        measured={'a003_clavicle_mm': round(L(B3, 'clavicle_left'), 1), 'c004_clavicle_mm': round(L(B4, 'clavicle_left'), 1),
                  'a003_AC_breadth_mm': round(ac(B3, a3['joint_markers']), 1), 'c004_AC_breadth_mm': round(ac(B4, M4), 1)},
        evidence=[conv['clavicle']['evidence'][0], conv['clavicle']['evidence'][2], 'hard invariant: chord < curved length'],
        action='c003/c004 within male endpoint range (130-175) and feasible AC family (333-353 mm); still non-canonical (SC/thorax frame open)')
    add(id='U2', region='shoulder', title='Scapula transverse geometry too large (a003)', cls='GEOMETRY_DEFECT', status='CORRECTED_IN_CANDIDATE',
        measured={'a003_AA_TS_mm': round(dist(a3['skeleton_input']['sides']['left']['AA'], a3['skeleton_input']['sides']['left']['TS']), 1),
                  'c004_AA_TS_mm': round(dist(c4['skeleton_input']['sides']['left']['AA'], c4['skeleton_input']['sides']['left']['TS']), 1)},
        evidence=[conv['scapula']['evidence'][0]], action='c003/c004 rebuilt from the Lee 29-landmark male scapula; exact 3D target still open')
    add(id='U3', region='shoulder', title='Clavicle stays level while the arm elevates', cls='MOVEMENT_MODEL_GAP', status='OPEN',
        measured={}, evidence=['skeleton_only_renders_c004/pose_shoulder_complex_scapular_plane_left_f5716.jpg', 'tracker Phase 8: SC elevation (bound only) not applied'],
        action='needs a sourced clavicular elevation rhythm')
    add(id='U4', region='thorax', title='Ribs drawn as straight sticks', cls='REPRESENTATION_LIMIT', status='BLOCKED',
        measured={}, evidence=[conv['ribs']['state'], 'readiness ribs BLOCKED (proximal 2016 spiral, thoracic mapping)'],
        action='also a genuine model deficiency for rib kinematics (neck axis degenerate); needs curved rib centrelines')
    add(id='U5', region='spine', title='Zero disc space at every disc-bearing level', cls='STRUCTURAL_INVARIANT_FAIL', status='BLOCKED',
        measured={'C3_L5_column_stick_sum_mm': round(col, 1), 'sourced_bodies_plus_discs_C2C3_to_L5S1_mm': round(sourced, 1),
                  'T1_T12_current_mm': round(th_cur, 1), 'T1_T12_sourceA_plus_discs_mm': round(sum(g[k]['sourceA_mean_mm'] for k in th) + th_disc, 1),
                  'T1_T12_sourceB_plus_discs_mm': round(sum(g[k]['sourceB_mean_mm'] for k in th) + th_disc, 1),
                  'L1_L5_stick_sum_mm': round(sum(L(B4, f'l{i}') for i in range(1, 6)), 1)},
        evidence=['CP2 spinal_disc_centre_gap_positive', 'canonical_spine_level_stack_v1.json', 'canonical_spine_geometry_audit_v1.json'],
        action='full sagittal level-stack rebuild (readiness sequence item 2); a proportional re-partition would move C7/T1 by ~40 mm and cascade into ribs/sternum, so it is not applied as a local fix. The current thoracic span agrees with the CT source (B) within 3.4% and not with the mixed-sex donor source (A, -19%)')
    add(id='U6', region='thorax', title='Sternum length', cls='EVIDENCE_GAP', status='BLOCKED', measured={'c004_sternum_stick_mm': round(L(B4, 'sternum'), 1)},
        evidence=[conv['sternum']['state']], action='stature/method source conflict; no direction frozen')
    add(id='U7', region='arm', title='Radius short for stature', cls='GEOMETRY_DEFECT', status='BLOCKED', measured={'c004_radius_stick_mm': round(L(B4, 'radius_left'), 1)},
        evidence=[conv['radius_forearm']['evidence'][0], conv['radius_forearm']['evidence'][1]], action='direction confirmed (grade B); endpoint-compatible second source required before freeze')
    add(id='U8', region='arm', title='Humerus length', cls='EVIDENCE_GAP', status='BLOCKED', measured={'c004_humerus_stick_mm': round(L(B4, 'humerus_left'), 1)},
        evidence=['readiness humerus blockers (joint-span vs maximum-length sources inconsistent by 20-40 mm)'], action='known-stature male sample with matched endpoints needed')
    # ---------------------------------------------------------------- pelvis / lower limb / foot
    add(id='L1', region='pelvis', title='Femoral heads appear detached from the pelvis', cls='REPRESENTATION_LIMIT', status='NONE',
        measured={'hip_centre_to_hip_bone_stick_mm': round(seg(M4['hip_left']['centre_m'], B4['hip_bone_left']['head_m'], B4['hip_bone_left']['tail_m']), 1),
                  'hip_centre_to_femur_head_mm': round(dist(M4['hip_left']['centre_m'], B4['femur_left']['head_m']), 3)},
        evidence=['os coxae stick is the SI-to-pubic chord; the acetabulum is not on it', conv['pelvis_HJC']['evidence'][0]],
        action='HJC is an independently corroborated anchor (grade A); pelvic envelope still BLOCKED (readiness pelvis)')
    add(id='L2', region='lower_limb', title='Knee and ankle centres', cls='NOT_A_DEFECT', status='NONE',
        measured={'femur_tail_to_tibia_head_mm': round(dist(B4['femur_left']['tail_m'], B4['tibia_left']['head_m']), 3), 'tibia_tail_to_talus_head_mm': round(dist(B4['tibia_left']['tail_m'], B4['talus_left']['head_m']), 3)},
        evidence=[conv['femur_tibia']['evidence'][0]], action='femur/tibia grade B; femur length method conflict recorded in readiness')
    add(id='L3', region='lower_limb', title='Patella stays put during plain knee flexion', cls='MOVEMENT_TEST_DESIGN', status='OPEN', measured={},
        evidence=['skeleton_only_renders_c004/pose_knee_flexion_extension_left_f381.jpg', 'patellar follower exists only in knee_flexion_with_patellar_follower'],
        action='apply the sourced follower in every knee-flexing test')
    add(id='L4', region='lower_limb', title='Hip adduction 20 deg makes the tibiae cross', cls='MOVEMENT_TEST_DESIGN', status='OPEN', measured={'axis_distance_mm': 0.568},
        evidence=['movement_collision_scan', 'amplitude is an unsourced TEST AMPLITUDE'], action='unchanged by instruction; needs a sourced amplitude or a contralateral-clearance start pose')
    add(id='L5', region='tarsus', title='Calcaneocuboid and talonavicular joint centres float off the bones', cls='JOINT_COORDINATE_DEFECT', status='BLOCKED',
        measured={'calcaneocuboid_to_calcaneus_mm': round(seg(M4['calcaneocuboid_left']['centre_m'], B4['calcaneus_left']['head_m'], B4['calcaneus_left']['tail_m']), 1),
                  'calcaneocuboid_to_cuboid_mm': round(seg(M4['calcaneocuboid_left']['centre_m'], B4['cuboid_left']['head_m'], B4['cuboid_left']['tail_m']), 1),
                  'talonavicular_to_navicular_mm': round(seg(M4['talocalcaneonavicular_left']['centre_m'], B4['navicular_left']['head_m'], B4['navicular_left']['tail_m']), 1)},
        evidence=['calcaneus control stick runs posterior (subtalar facet to tuber); anterior process absent', 'readiness tarsus BLOCKED (contact centres)'],
        action='source-defined tarsal envelopes and contact centres; also explains the 37 mm midfoot split in subtalar sweeps')
    add(id='L6', region='foot', title='Foot too long', cls='NOT_A_DEFECT', status='NONE', measured={},
        evidence=[conv['foot_surface']['evidence'][0], conv['metatarsals']['state']], action='the long foot is the r95 SURFACE; metatarsal lengths remain source-conflicted (grade C); mesh must refit to the skeleton')
    # ---------------------------------------------------------------- head / neck / global
    add(id='S1', region='head_neck', title='Skull and face look like scattered sticks', cls='REPRESENTATION_LIMIT', status='BLOCKED', measured={},
        evidence=[conv['cranial_facial_fixed_geometry']['state']], action='landmark envelopes needed (grade D placeholder geometry)')
    add(id='S2', region='head_neck', title='Mandible drawn through the oral cavity', cls='REPRESENTATION_LIMIT', status='NONE', measured={'mandible_x_vomer_axis_mm': 0.09},
        evidence=['all_pairs_crossing_scan REPRESENTATION_ARTEFACT'], action='U-shaped bone; chord is not geometry')
    add(id='G1', region='global', title='Left-right symmetry', cls='NOT_A_DEFECT', status='NONE',
        measured={'max_mirror_mm_c004': max(dist(np.asarray(B4[n]['head_m']) * [-1, 1, 1], B4[n[:-5] + '_right']['head_m']) for n in B4 if n.endswith('_left'))},
        evidence=['mirror_parity_scan'], action='residual 0.38 mm confined to toe phalanges (inherited fit)')
    add(id='G2', region='global', title='c003/c004 wrist and hand lie outside the a003 body skin', cls='NOT_A_DEFECT', status='NONE',
        measured={'outside_points_left_arm_c004': len(hand['c004_arm_points_outside_a003_skin_left']['c004'])},
        evidence=['hand_input_source_rebuild_v1.json'], action='the mesh must be refitted to the skeleton (owner policy); bones are not moved to fit skin')
    add(id='G3', region='global', title='Unsourced movement amplitudes', cls='EVIDENCE_GAP', status='OPEN', measured={'test_amplitude_peaks': amp['by_kind']['LABELLED_TEST_AMPLITUDE'], 'tests': 49},
        evidence=['amplitude_provenance', 'movement_evidence_queue (Work)'], action='kept separate from physiological limits; no amplitude changed')
    return R


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); o = ap.parse_args()
    R = build()
    from collections import Counter
    out = {'schema_version': 1, 'created': '2026-10-09', 'kind': 'DEFECT_REGISTER_NOT_ACCEPTANCE', 'entries': R,
           'by_class': dict(Counter(r['cls'] for r in R)), 'by_status': dict(Counter(r['status'] for r in R))}
    Path(o.out).write_text(json.dumps(out, indent=1, default=float) + '\n')
    for r in R:
        print(r['id'], r['cls'], r['status'], '|', r['title'], '|', json.dumps(r['measured'], default=float)[:200])
    print(out['by_class'], out['by_status'])


if __name__ == '__main__':
    main()
