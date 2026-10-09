#!/usr/bin/env python3
"""Adversarial probe of the draft PR #12 bone-surface contract (read-only review aid; imports the PR's own modules).

  pr12_contract_probe.py --pr12-scripts DIR --out JSON
Runs the PR's validate() on constructed assets and records what passes. Used by docs/CLAUDE_ANATOMICAL_DEVELOPMENT_20261009.md.
"""
import argparse, copy, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'


def tetra(origin, s=0.02):
    x, y, z = origin
    V = [[x, y, z], [x + s, y, z], [x, y + s, z], [x, y, z + s]]
    return V, [[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--pr12-scripts', required=True); ap.add_argument('--out', required=True)
    o = ap.parse_args()
    sys.path.insert(0, str(Path(o.pr12_scripts) / 'anatomy_fit'))
    import bone_surface_contract as c
    skel = json.loads((ANAT / 'character_fit_r95_a003.json').read_text())
    arts = json.loads((ANAT / 'adult_articulation_inventory.json').read_text())
    B = skel['bones'] if 'bones' in skel else skel['record']['bones']
    I = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    base = {'schema_version': 1, 'status': 'AUDIT_ONLY', 'units': 'm', 'bone_id': 'femur_left', 'world_from_local': I,
            'rig_anchors_local_m': {'head': B['femur_left']['head_m'], 'tail': B['femur_left']['tail_m']}, 'surface_type': 'closed_bone'}
    cases = {}

    def run(name, asset, expect_pass_is_problem):
        try:
            r = c.validate(asset, skel, arts); res = {'passed': True, 'status': r['status']}
        except Exception as e:
            res = {'passed': False, 'error': str(e)}
        res['passing_is_a_problem'] = expect_pass_is_problem
        cases[name] = res
    a = copy.deepcopy(base); a['vertices_m'], a['triangles'] = tetra([5, 5, 5]); run('mesh_5m_away_from_its_bone', a, True)
    a = copy.deepcopy(base); a['vertices_m'], a['triangles'] = tetra([-B['femur_left']['head_m'][0], B['femur_left']['head_m'][1], 0.7])
    run('left_femur_mesh_on_the_right_side', a, True)
    a = copy.deepcopy(base); a['vertices_m'], a['triangles'] = tetra([B['femur_left']['head_m'][0], 0, 0.7], s=0.0005)
    run('half_millimetre_femur', a, True)
    a = copy.deepcopy(base); a['vertices_m'], a['triangles'] = tetra([B['femur_left']['head_m'][0], 0, 0.7]); a['triangles'][0] = a['triangles'][0][::-1]
    run('one_reversed_face', a, False)
    out = {'schema_version': 1, 'created': '2026-10-09', 'kind': 'REVIEW_PROBE', 'target': 'draft PR #12 (codex/anatomical-bone-surfaces-foundation-20261009 @ d0f6bfd3)',
           'cases': cases,
           'problems': [k for k, v in cases.items() if v['passed'] and v['passing_is_a_problem']]}
    Path(o.out).write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps(cases, indent=1))


if __name__ == '__main__':
    main()
