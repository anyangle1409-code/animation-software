#!/usr/bin/env python3
"""Trunk vertical closure audit (read-only; selects nothing).

Collects, for one candidate record, every committed independent vertical check on the trunk and reports the residuals
side by side, so that a spine/disc rebuild can be judged against all of them at once:

  lumbar_length      c004 L5-inferior to L1-superior arc vs male sourced bodies + discs (CT middle/average and MRI edge)
  cervical_length    C3-inferior to C2/C3 arc vs Yukawa male bodies + discs
  thoracic_length    T12-inferior to T1-superior arc vs THORACIC_CT_2016 bodies + THORACIC_BODY_DISC_2011 discs
  T12_L1_height      T12/L1 junction z vs P1 S1 centre + sourced lumbar vertical rise (P1 orientations)
  IJ_height          record IJ vs ANSUR suprasternale at 1.82 m (skin vs skin)
  rib10_height       anterior end of rib 10 (lowest of the two sides) vs ANSUR tenth-rib height at 1.82 m. Landmark
                     definitions differ (ANSUR: skin over the lower margin of the 10th rib; record: costochondral end of
                     the rib stick), so this is a directional check, not a target
  C7_height          C7 spinous tip (record C7 centre + grade-D specimen tip offset) vs ANSUR cervicale
Also re-tests a curve-preserving disc re-partition (P003) against the acceptance rule "thoracic rib attachments remain
level-correct after vertebral retargeting" (canonical_spine_geometry_audit_v1.json).

  trunk_vertical_closure_audit.py --discriminator JSON [--p003 PROPOSAL_RECORD] --out JSON
"""
import argparse, hashlib, json, math, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spine_column_length_discriminator as sd  # noqa: E402


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def arc(B, names, top_end):
    pts = [B[n]['head_m'] for n in names] + [top_end]
    return 1000 * sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def audit(rec, disc):
    B = rec['bones']
    stack, edges, geom, frames, s1 = sd.load('stack'), sd.load('edges'), sd.load('geom'), sd.load('frames'), sd.load('s1')
    out = {}
    # lengths along the record's own curve
    L = ['l5', 'l4', 'l3', 'l2', 'l1']
    lum_arc = arc(B, L, B['l1']['tail_m'])
    ct = sum(stack['vertebral_bodies_mm'][f'L{i}']['candidate'] for i in range(1, 6)) + \
        sum(stack['disc_gaps_mm'][k]['candidate'] for k in ('L1/L2', 'L2/L3', 'L3/L4', 'L4/L5'))
    mri = sum((edges['body_edge_heights'][f'L{i}']['anterior_mean_mm'] + edges['body_edge_heights'][f'L{i}']['posterior_mean_mm']) / 2 for i in range(1, 6)) + \
        sum((edges['disc_edge_gaps'][k]['anterior_mean_mm'] + edges['disc_edge_gaps'][k]['posterior_mean_mm']) / 2 for k in ('L1/L2', 'L2/L3', 'L3/L4', 'L4/L5'))
    out['lumbar_length'] = {'record_arc_mm': round(lum_arc, 1), 'sourced_CT_middle_avg_mm': round(ct, 1), 'sourced_MRI_edge_mm': round(mri, 1),
                            'excess_vs_MRI_edge_mm': round(lum_arc - mri, 1), 'excess_vs_CT_mm': round(lum_arc - ct, 1),
                            'span': 'L5 inferior endplate to L1 superior endplate (5 bodies + 4 discs)'}
    T = [f't{i}' for i in range(12, 0, -1)]
    th_arc = arc(B, T, B['t1']['tail_m'])
    tb, td = sd.thoracic_heights('B_CT_2016', stack, geom)
    ta, _ = sd.thoracic_heights('A_anatomical_2011', stack, geom)
    out['thoracic_length'] = {'record_arc_mm': round(th_arc, 1), 'sourced_B_plus_discs_mm': round(sum(tb.values()) + sum(td.values()), 1),
                              'sourced_A_plus_discs_mm': round(sum(ta.values()) + sum(td.values()), 1),
                              'excess_vs_B_mm': round(th_arc - sum(tb.values()) - sum(td.values()), 1),
                              'span': 'T12 inferior to T1 superior endplate (12 bodies + 11 discs)'}
    C = ['c7', 'c6', 'c5', 'c4', 'c3']
    cv_arc = arc(B, C, B['c3']['tail_m'])
    cv = sum(stack['vertebral_bodies_mm'][f'C{i}']['candidate'] for i in range(3, 8)) + \
        sum(stack['disc_gaps_mm'][k]['candidate'] for k in ('C3/C4', 'C4/C5', 'C5/C6', 'C6/C7'))
    out['cervical_length'] = {'record_arc_mm': round(cv_arc, 1), 'sourced_Yukawa_mm': round(cv, 1), 'excess_mm': round(cv_arc - cv, 1),
                              'span': 'C7 inferior to C3 superior endplate (5 bodies + 4 discs)'}
    # T12/L1 height from the provisional S1 anchor
    s1c = s1['derived_S1_superior_endplate']['centre_m']
    lel, _, _, _ = sd.lumbar_elements('MRI_edge_mean', frames, stack, edges)
    lpts = sd.walk((1000 * s1c[1], 1000 * s1c[2]), [(h, p) for h, p, _ in lel])
    t12l1_pred = lpts[-1][1] + stack['disc_gaps_mm']['T12/L1']['candidate'] / 2
    t12l1_rec = 1000 * (B['t12']['head_m'][2] + B['l1']['tail_m'][2]) / 2
    out['T12_L1_height'] = {'record_mm': round(t12l1_rec, 1), 'P1_S1_plus_sourced_lumbar_mm': round(t12l1_pred, 1),
                            'excess_mm': round(t12l1_rec - t12l1_pred, 1),
                            'note': 'record T12/L1 point is the shared stick endpoint (zero gap); prediction is the disc mid-height'}
    ij = rec['skeleton_input']['trunk']['ij_skin']['value_m']
    sup = sd.ansur_at('suprasternaleheight')
    out['IJ_height'] = {'record_ij_skin_mm': round(1000 * ij[2], 1), 'ANSUR_182': sup, 'excess_mm': round(1000 * ij[2] - sup['prediction_mm'], 1),
                        'z_residual_sd': round((1000 * ij[2] - sup['prediction_mm']) / sup['residual_sd_mm'], 2)}
    r10 = min(1000 * B[f'rib_10_{s}']['tail_m'][2] for s in ('left', 'right'))
    tr = sd.ansur_at('tenthribheight')
    out['rib10_height'] = {'record_rib10_anterior_end_mm': round(r10, 1), 'ANSUR_182': tr, 'excess_mm': round(r10 - tr['prediction_mm'], 1),
                           'z_residual_sd': round((r10 - tr['prediction_mm']) / tr['residual_sd_mm'], 2), 'definition_match': 'DIRECTIONAL_ONLY'}
    c7 = sd.candidate_c7_from(rec)
    tip = disc['c7_spinous_tip_offset_specimen']['tip_minus_body_centre_local_mm']
    zt = {d: sd.tip_world((c7['c7_stick_mid_mm'][1], c7['c7_stick_mid_mm'][2]), c7['c7_axis_lean_deg'] + d, tip)[1] for d in (-10, 0, 10)}
    cerv = disc['ansur_cervicale_at_182']
    out['C7_height'] = {'record_C7_tip_mm_lean_minus10_0_plus10': [round(zt[d], 1) for d in (-10, 0, 10)], 'ANSUR_cervicale_mm': cerv['prediction_mm'],
                        'excess_mm_central': round(zt[0] - cerv['prediction_mm'], 1), 'grade': 'tip offset from one specimen (grade D)'}
    return out


def rib_test(p003):
    c = p003['candidate']
    worst = max(abs(v['p003_head_minus_level_z_mm']) for v in c['rib_head_levels'].values())
    base = max(abs(v['c004_head_minus_level_z_mm']) for v in c['rib_head_levels'].values())
    return {'proposal': c['id'], 'uniform_scale_to_c004_arc': c['uniform_scale_to_c004_arc'],
            'max_abs_rib_head_offset_from_articular_level_mm': {'c004': base, 'p003': worst},
            'per_rib_left': {k: v for k, v in c['rib_head_levels'].items() if k.endswith('left')},
            'body_centre_shift_mm': {r['bone']: r['centre_shift_mm'] for r in c['bodies']},
            'verdict': 'REJECTED_RIB_LEVEL_ACCEPTANCE' if worst > 2 * base else 'NOT_REJECTED',
            'rule': 'canonical_spine_geometry_audit_v1.json acceptance: thoracic rib attachments remain level-correct after vertebral '
                    'retargeting; rejected when the worst rib-head offset from its articular level more than doubles c004\'s'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--discriminator', required=True)
    ap.add_argument('--record', default=str(sd.IN['c004']))
    ap.add_argument('--p003')
    ap.add_argument('--out', required=True)
    o = ap.parse_args()
    rec = json.loads(Path(o.record).read_text()); disc = json.loads(Path(o.discriminator).read_text())
    res = audit(rec, disc)
    rows = {k: v.get('excess_mm', v.get('excess_vs_MRI_edge_mm', v.get('excess_vs_B_mm', v.get('excess_mm_central')))) for k, v in res.items()}
    out = {'schema_version': 1, 'created': '2026-10-09', 'kind': 'READ_ONLY_TRUNK_VERTICAL_CLOSURE_AUDIT', 'record': o.record,
           'inputs_sha256': {o.record: sha(o.record), o.discriminator: sha(o.discriminator)}, 'residuals_mm': rows, 'detail': res}
    if o.p003:
        out['inputs_sha256'][o.p003] = sha(o.p003)
        out['p003_curve_preserving_repartition'] = rib_test(json.loads(Path(o.p003).read_text()))
    out['reading'] = [
        'Positive = the record is longer/higher than the independent evidence.',
        'The lower-trunk height checks (T12/L1 from the pelvis, IJ and rib 10 from ANSUR) are independent of each other and are '
        'compared here side by side; the lumbar arc excess is the same signal seen along the curve.',
        'C7 relies on a grade-D tip offset and is reported for completeness; the thorax pitch / C7-IJ conflict is already OPEN '
        '(canonical_thorax_frame_182_review_v1.json, audit/shoulder_vertical_relation_audit_v1.json).']
    Path(o.out).parent.mkdir(parents=True, exist_ok=True)
    Path(o.out).write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps(rows))
    if o.p003:
        print(json.dumps({k: v for k, v in out['p003_curve_preserving_repartition'].items() if k in ('verdict', 'max_abs_rib_head_offset_from_articular_level_mm')}))


if __name__ == '__main__':
    main()
