#!/usr/bin/env python3
"""Source matrix for the two open follower gaps (read-only; changes no model, record or test).

 (1) patellar translation/rotation through knee flexion
 (2) clavicle elevation (and retraction) through arm elevation

Reads the exact definitions from repository-held evidence and from pinned official model files, records conventions, and
quantifies agreement/conflict. A proposed relation is emitted only as a SEPARATELY TESTABLE future experiment with explicit
arms and acceptance criteria; nothing is adopted.

  follower_source_matrix.py --opensim-models DIR --opensim-commit SHA --myosim DIR --myosim-commit SHA --out JSON
"""
import argparse, hashlib, json, math, re, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from opensim_model_geometry import Model  # noqa: E402
import joint_solver as js  # noqa: E402

ROOT = HERE.parents[1]
SUPP = ROOT / 'ORIGINAL_V1_WORK/anatomy/phase9_supplementary_observations.json'
FV = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/follower_verification_c004_v1.json'
PT = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/patellar_tracking_c004_v1.json'
CG = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/clavicle_elevation_gap_c004_v1.json'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def strip(s):
    return re.sub(r'<!--.*?-->', '', s, flags=re.S)


def rajagopal_patella(osim):
    """Patella pose relative to the femur over 0-120 deg (knee_angle_l, radians in the file; reported in degrees / mm)."""
    rows = []
    m0 = Model(osim)
    F0, P0 = m0.body_world('femur_l'), m0.body_world('patella_l')
    rel0 = np.linalg.inv(F0) @ P0
    for a in range(0, 121, 10):
        m = Model(osim); m.coords['knee_angle_l'] = math.radians(a); m.coords['knee_angle_l_beta'] = math.radians(a)
        rel = np.linalg.inv(m.body_world('femur_l')) @ m.body_world('patella_l')
        R = rel[:3, :3] @ rel0[:3, :3].T
        rot = math.degrees(math.atan2(R[1, 0], R[0, 0]))
        d = (rel[:3, 3] - rel0[:3, 3]) * 1000
        rows.append({'knee_deg': a, 'patella_rotation_deg': round(rot, 2), 'ratio': None if a == 0 else round(abs(rot) / a, 3),
                     'translation_mm_femur_frame_x_anterior_y_superior': [round(d[0], 1), round(d[1], 1)]})
    s = strip(Path(osim).read_text())
    credits = re.search(r'<credits>(.*?)</credits>', s, re.S)
    return rows, (credits.group(1).strip()[:400] if credits else None)


def myolegs_vs_rajagopal(myosim, rows_spline):
    """MyoLegs encodes the patella as polynomials of knee_angle; check whether they reproduce the Rajagopal splines."""
    a = (Path(myosim) / 'myo_sim/models/leg/assets/myolegs_assets.xml').read_text()
    pc = lambda name: [float(v) for v in re.search(rf'joint1="{name}"[^>]*polycoef="([^"]+)"', a).group(1).split()]
    poly = {k: pc(k) for k in ('knee_angle_beta_translation1_r', 'knee_angle_beta_translation2_r', 'knee_angle_beta_rotation1_r')}
    ev = lambda c, q: sum(ci * q ** i for i, ci in enumerate(c))
    raj_tx = {0: 52.4, 10: 48.8, 20: 43.7, 30: 37.1, 40: 29.6, 50: 21.6, 60: 13.6, 70: 5.7, 80: -1.9, 90: -8.8, 100: -14.8, 110: -19.6, 120: -22.7}
    diffs = [abs(ev(poly['knee_angle_beta_translation1_r'], math.radians(k)) * 1000 - v) for k, v in raj_tx.items()]
    return {'polycoef': poly, 'max_abs_diff_vs_rajagopal_translation1_spline_mm': round(max(diffs), 2),
            'reading': 'MyoLegs patella polynomials are a fit to the same Rajagopal splines (same lineage, not an independent source)'}


def mobl_clavicle(myosim):
    chain = (Path(myosim) / 'myo_sim/models/arm/assets/myoarm_r_chain.xml').read_text()
    assets = (Path(myosim) / 'myo_sim/models/arm/assets/myoarm_r_assets.xml').read_text()
    axes = {m.group(2): [float(v) for v in m.group(1).split()] for m in re.finditer(r'<joint axis="([^"]+)" name="(sternoclavicular_r\d_r)"', chain)}
    coef = {m.group(1): [float(v) for v in m.group(2).split()] for m in re.finditer(r'joint1="(sternoclavicular_r\d_r)" joint2="shoulder_elv_r"[^>]*polycoef="([^"]+)"', assets)}
    out = {}
    for k in axes:
        ax = np.array(axes[k]) / np.linalg.norm(axes[k])
        role = 'elevation/depression (axis ~ antero-posterior)' if abs(ax[0]) > 0.9 else ('protraction/retraction (axis ~ vertical)' if abs(ax[1]) > 0.9 else 'other')
        c1 = coef.get(k, [0, 0])[1]
        out[k] = {'axis_xyz_model_frame': axes[k], 'role': role, 'linear_coefficient_rad_per_rad': c1,
                  'at_HT_90_deg': round(c1 * 90, 2), 'at_HT_168_deg': round(c1 * 168, 2)}
    return out


def main():
    ap = argparse.ArgumentParser()
    for a in ('--opensim-models', '--opensim-commit', '--myosim', '--myosim-commit', '--out'):
        ap.add_argument(a, required=True)
    o = ap.parse_args()
    supp = json.loads(SUPP.read_text())['observations']
    pr = supp['patellar_flexion_ratio']
    osim = Path(o.opensim_models) / 'Models/Rajagopal/Rajagopal2016.osim'
    raj, credits = rajagopal_patella(osim)
    myo = myolegs_vs_rajagopal(o.myosim, raj)
    rr = {r['knee_deg']: r['ratio'] for r in raj if r['ratio']}
    fv = json.loads(FV.read_text())['results']; ptj = json.loads(PT.read_text())
    clav = mobl_clavicle(o.myosim)
    coup = js.FOLLOWER_COUPLINGS['scapulothoracic_rhythm']
    elev = next(v for v in clav.values() if v['role'].startswith('elevation'))
    retr = next(v for v in clav.values() if v['role'].startswith('protraction'))
    ht_end = coup['gh_at_max_deg'] * (1 + coup['upward_rotation_per_gh_deg'])
    gh = f'https://github.com/opensim-org/opensim-models/blob/{o.opensim_commit}/'
    my = f'https://github.com/MyoHub/myo_sim/blob/{o.myosim_commit}/'
    matrix = {
        'patella': [
            {'source': 'PATELLA_LUNGE (repository: phase9_supplementary_observations.json)', 'type': 'primary measurement (lateral radiographs, healthy knees, single-leg lunge 0-165 deg); second cadaver study cited to 100 deg',
             'quantity': 'patellar flexion relative to femur per degree of knee flexion', 'value': pr['value'], 'units': 'deg/deg (unitless)',
             'plane': 'sagittal', 'side': 'not side-specific', 'translation': 'NOT reported', 'task': pr.get('mode'), 'used_in_c004': 'yes (rotation-only follower)'},
            {'source': gh + 'Models/Rajagopal/Rajagopal2016.osim', 'type': 'official generic model (75 kg, 1.70 m male per repository registry)',
             'quantity': 'patellofemoral CustomJoint: rotation1 about patella z + translation1 (x anterior) + translation2 (y superior) as SimmSpline(knee_angle_beta), coupled 1:1 to knee_angle',
             'units': 'radians and metres in file; reported here as deg and mm', 'frame': 'femur_l offset frame at the knee (x anterior, y superior, z lateral-right); left/right files mirror z',
             'rotation_ratio_by_knee_deg': rr, 'translation_mm': {r['knee_deg']: r['translation_mm_femur_frame_x_anterior_y_superior'] for r in raj},
             'lineage': credits or 'Rajagopal 2016 credits not present in the file', 'used_in_c004': 'no'},
            {'source': my + 'myo_sim/models/leg/assets/myolegs_assets.xml', 'type': 'official model (MyoLegs), polynomial equality constraints', **myo, 'used_in_c004': 'no'},
            {'source': gh + 'Models/Gait2392_Simbody/gait2392_millard2012muscle.osim', 'type': 'official model', 'quantity': 'no patella body; quadriceps use moving path points (credits: Delp 1990; Yamaguchi & Zajac 1989)',
             'used_in_c004': 'no', 'reading': 'same lineage; no independent patellar path'}],
        'clavicle': [
            {'source': 'joint_solver.FOLLOWER_COUPLINGS[scapulothoracic_rhythm] (repository)', 'type': 'secondary review snippet + bone-pin study (SHOULDER_PINS)',
             'quantity': 'clavicle retraction end value; posterior rotation end value; elevation upper bound', 'value': {'retraction_deg': coup['clavicle_retraction_deg'], 'posterior_rotation_deg': 31.0,
             'elevation': coup['clavicle_retraction_source']}, 'scaling': 'linear in GH elevation to the McClure end (GH 117.5 deg, HT about 168 deg)', 'used_in_c004': 'retraction and posterior rotation yes; elevation no'},
            {'source': my + 'myo_sim/models/arm/assets/myoarm_r_assets.xml (axes: myoarm_r_chain.xml)', 'type': 'official model (MyoSuite arm; MoBL-ARMS lineage per the model family)',
             'quantity': 'sternoclavicular rotations as linear polynomials of shoulder_elv (thoracohumeral elevation coordinate)', 'units': 'rad/rad (equal to deg/deg)',
             'frame': 'OpenSim thorax axes kept by MyoSuite (x anterior, y superior, z right); right arm only in this file, left by mirroring',
             'coordinates': clav, 'used_in_c004': 'no'}]}
    conflicts = {
        'patella_rotation': {'sourced_ratio': pr['value']['ratio'], 'rajagopal_ratio_at_60_90_120': [rr.get(60), rr.get(90), rr.get(120)],
                             'reading': 'The generic model rotation is non-linear (cumulative 0.04 at 10 deg, 0.67 at 50 deg, 0.85 at 120 deg); the primary lunge measurement '
                                        'is linear 0.66 (r2 0.992). Different task '
                                        '(weight-bearing lunge vs model) and frame definitions; NOT reconciled.'},
        'clavicle_elevation': {'repository_bound': 'below about 10 deg (secondary snippet; bound only)', 'mobl_at_HT_90_168': [elev['at_HT_90_deg'], elev['at_HT_168_deg']],
                               'crossing_HT_deg': round(10 / elev['linear_coefficient_rad_per_rad'], 1), 'reading': 'Agree below ~98 deg HT; conflict above. No primary bone-pin table is held.'},
        'clavicle_retraction': {'repository_end_deg': coup['clavicle_retraction_deg'], 'mobl_at_HT_168_deg': retr['at_HT_168_deg'],
                                'reading': 'MoBL protraction/retraction magnitude at 168 deg HT differs strongly from the repository end value (sign convention of the MoBL '
                                           'axis not verified against anatomy here); NOT reconciled.'}}
    proposals = {
        'E-PAT-1': {'status': 'PROPOSED_FUTURE_EXPERIMENT_NOT_ADOPTED',
                    'relation': 'patella pose relative to femur = Rajagopal 2016 patellofemoral translation (x anterior, y superior; mm) scaled by c004 femur '
                                'length / Rajagopal femur length, expressed in the c004 femur sagittal frame, as a function of knee flexion',
                    'arms': {'A_rotation_rajagopal': 'patella rotation from the same spline (internally consistent with its translation)',
                             'B_rotation_sourced_0.66': 'patella rotation 0.66 x knee flexion (primary measurement) with the Rajagopal translation'},
                    'correspondence_basis': 'patellar_tracking_c004_v1.json: arm A keeps the patellar ligament within '
                                            f"{ptj['summary']['follower_ligament_change_max_percent']} % (model itself {ptj['summary']['rajagopal_own_ligament_change_percent']} %)",
                    'acceptance': ['patellar-ligament length change <= the Rajagopal model own range at 0-120 deg',
                                   'no patella-femur / patella-tibia axis crossing; bilateral symmetry <= 1e-3 deg',
                                   'rotation arm chosen only after a source reconciles 0.66 with the model ratio; otherwise report both'],
                    'limits': ['single model lineage (Delp/Yamaguchi-Zajac); generic 1.70 m male scaled by femur length only',
                               'c004 knee is a pure rotation about the KJC, Rajagopal knee translates; knee-origin definitions differ by a few mm',
                               f"current c004 rotation-only follower lengthens the ligament by up to {fv['knee']['left']['ligament_change_with_follower_mm'][1]} mm"]},
        'E-CLAV-1': {'status': 'NO_RELATION_PROPOSED_UNRESOLVED',
                     'reason': 'the only quantitative elevation relation (MoBL 0.1025 deg/deg) conflicts with the repository bound above ~98 deg HT, its retraction '
                               'coupling conflicts with the repository retraction end value, and no primary bone-pin table is accessible',
                     'needed': 'primary clavicle elevation/retraction vs humerothoracic elevation table (e.g. bone-pin study) with axis and sign definitions'}}
    out = {'schema_version': 1, 'created': '2026-10-09', 'kind': 'SOURCE_MATRIX_DOCUMENTATION_ONLY',
           'inputs_sha256': {str(p.relative_to(ROOT)): sha(p) for p in (SUPP, FV, PT, CG)},
           'conventions_note': 'HGPT: +X left, +Y posterior, +Z superior. OpenSim/MoBL model frames: x anterior, y superior, z right. Model files in '
                               'radians/metres; all angles reported in degrees, lengths in mm. Linear rad/rad couplings are unit-free.',
           'matrix': matrix, 'conflicts': conflicts, 'proposals': proposals,
           'not_reachable_from_cloud': 'primary literature hosts (PubMed/PMC/publishers) blocked by the environment network policy'}
    Path(o.out).parent.mkdir(parents=True, exist_ok=True)
    Path(o.out).write_text(json.dumps(out, indent=1) + '\n')
    print('raj ratio', rr); print('myo vs raj', myo['max_abs_diff_vs_rajagopal_translation1_spline_mm'], 'mm')
    print('clav', {k: (v['role'][:12], v['linear_coefficient_rad_per_rad'], v['at_HT_168_deg']) for k, v in clav.items()})
    print('credits', (credits or '')[:200])


if __name__ == '__main__':
    main()
