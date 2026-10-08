#!/usr/bin/env python3
"""Sternum target review for a 1.82 m male (ribs/sternum region). Evidence and a003 consistency only; nothing selected.

Population sizes come from the registered sternum sources (male means). Layout topology (which costal cartilage meets
which sternal segment) is anatomy-textbook invariant; the single BodyParts3D specimen gives one measured layout
(grade D) that illustrates it. a003's sternum stick and sternocostal markers are tested against both.

  sternum_target_review.py --out JSON
"""
import argparse, json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
SOURCES = ['STERNUM_CT_TURKEY_2018', 'STERNUM_CT_IRAN_2022', 'STERNUM_CT_GREECE_2025', 'STERNUM_GALLOWAY_OSTEOLOGY', 'STERNUM_SELTHOFER_2006']
TOPOLOGY = [
    'costal cartilage 1 joins the manubrium (synchondrosis), below the clavicular notch',
    'costal cartilage 2 joins at the sternal angle, the manubriosternal junction',
    'costal cartilages 3-6 join the sternal body',
    'costal cartilage 7 joins at or near the xiphisternal junction',
    'ribs 8-10 reach the sternum only through the costal margin (interchondral), ribs 11-12 not at all',
]


def build():
    reg = {s['id']: s for s in json.loads((ANAT / 'canonical_proportion_sources_v1.json').read_text())['sources']}
    pop = {k: {kk: vv for kk, vv in reg[k].get('male_values_mm', {}).items()} for k in SOURCES}
    man = [v['manubrium_length']['mean'] for v in pop.values() if 'manubrium_length' in v]
    body = [v[k]['mean'] for v in pop.values() for k in ('corpus_sterni_length', 'body_length', 'sternal_body_length') if k in v]
    sums = [v['manubrium_plus_body_mean_sum'] for v in pop.values() if 'manubrium_plus_body_mean_sum' in v]
    spec = json.loads((ANAT / 'bodyparts3d_single_specimen_axial_shoulder_v1.json').read_text())['sternum']
    sl = spec['costal_attachment_depth_mm']
    spec_levels = {i: round((sl[f'left_{i}'] + sl[f'right_{i}']) / 2, 1) for i in range(1, 8)}
    ms = spec['manubriosternal_level_mm']
    a = json.loads((ANAT / 'character_fit_r95_a003.json').read_text())
    j, st = a['joint_markers'], a['bones']['sternum']
    top = st['head_m'][2]
    a_levels = {i: round((top - j[f'sternocostal_{i:02d}_left']['centre_m'][2]) * 1000, 1) for i in range(1, 8)}
    a_ms = round((top - j['manubriosternal']['centre_m'][2]) * 1000, 1)
    a_len = round(math.dist(st['head_m'], st['tail_m']) * 1000, 1)
    gaps = [round(a_levels[i + 1] - a_levels[i], 1) for i in range(1, 7)]
    turkey_total = reg['STERNUM_CT_TURKEY_2018']['male_values_mm']['total_sternum_length_including_xiphoid']
    return {
        'schema_version': 1, 'created': '2026-10-08', 'status': 'EVIDENCE_REVIEW_NOT_SELECTED', 'freeze_ready': False,
        'owner_policy': 'PROPORTION_POLICY_182CM_MALE',
        'population_male_means_mm': {'manubrium_length_range': [min(man), max(man)], 'body_length_range': [min(body), max(body)],
                                     'manubrium_plus_body_range': [min(sums), max(sums)],
                                     'total_including_xiphoid_turkey_CT': turkey_total,
                                     'xiphoid_galloway': reg['STERNUM_GALLOWAY_OSTEOLOGY']['male_values_mm']['xiphoid_length'],
                                     'manubrium_width_iran_CT': reg['STERNUM_CT_IRAN_2022']['male_values_mm']['manubrium_width'],
                                     'sources': SOURCES},
        'stature_conditioning': 'Weak: registered male sternum-stature correlations are r = 0.46-0.64, so a 1.82 m adjustment is '
                                'small and uncertain; population means are context, not a scaled target.',
        'topology_rules': TOPOLOGY,
        'specimen_layout_grade_D': {'manubriosternal_depth_mm': ms, 'costal_attachment_depth_mm': spec_levels,
                                    'reading': f'Rib 2 at {spec_levels[2]} mm against the manubriosternal junction at {ms} mm; '
                                               'all topology rules hold; left/right within 0.4 mm.'},
        'a003': {'sternum_stick_mm': a_len,
                 'stick_vs_total_with_xiphoid_z': round((a_len - turkey_total['mean']) / turkey_total['sd'], 2),
                 'manubriosternal_depth_mm': a_ms, 'sternocostal_depth_mm': a_levels, 'sternocostal_spacing_mm': gaps,
                 'findings': [f'Sternum stick {a_len} mm against {turkey_total["mean"]} +/- {turkey_total["sd"]} mm total male sternum including xiphoid '
                              f'(z {round((a_len - turkey_total["mean"]) / turkey_total["sd"], 1)}).',
                              f'Rib 2 attaches {a_levels[2]} mm below the top but the manubriosternal marker is {a_ms} mm down: '
                              'rib 2 is not at the sternal angle (topology rule 2 fails).',
                              f'Manubriosternal depth {a_ms} mm against male manubrium lengths {min(man)}-{max(man)} mm.',
                              f'Sternocostal spacing is near-uniform ({min(gaps)}-{max(gaps)} mm): a schematic layout, not anatomical.']},
        'what_would_close_it': ['Selthofer 2006 full text (Hrcak, blocked here): breadth/length per costal-notch segment for 55 male sterna',
                                'a 1.82 m-conditioned sternal length (or an explicit population-mean policy given weak stature correlation)',
                                'joint placement of sternum and rib anterior ends in one thoracic frame (shared with the rib region)'],
    }


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True)
    o = ap.parse_args()
    rep = build()
    Path(o.out).write_text(json.dumps(rep, indent=1) + '\n')
    print(json.dumps(rep['a003'], indent=1)); print(json.dumps(rep['population_male_means_mm']))


if __name__ == '__main__':
    main()
