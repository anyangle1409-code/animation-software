"""Read-only adversarial review of Claude's CP2 checker at 6570e750.

These are deliberately invalid synthetic fixtures, never anatomy targets.
Run from any directory with the repository's Python dependencies installed.
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/anatomy_fit')]
import test_cp2_preflight as t


def observe():
    result = {}
    candidate = copy.deepcopy(t.A003)
    candidate['bones']['c3']['tail_m'] = candidate['bones']['c3']['head_m'][:]
    try:
        result['zero_length_c3'] = {'verdict': t.run(candidate)['verdict']}
    except Exception as exc:
        result['zero_length_c3'] = {'exception': type(exc).__name__, 'message': str(exc)}

    candidate = t.with_gaps(t.A003)
    candidate['disc_surfaces'] = {
        disc: {
            'upper_origin_mm': [100000, 100000, 100008],
            'lower_origin_mm': [100000, 100000, 100000],
            'upper_normal': [0, 0, 1], 'lower_normal': [0, 0, 1],
            'footprint_centre_xy_mm': [100000, 100000],
            'footprint_radii_xy_mm': [0.001, 0.001],
        } for disc in t.m.SPINAL_DISCS
    }
    report = t.run(candidate)
    result['unrelated_remote_disc_surfaces'] = {
        'verdict': report['verdict'],
        'clearance_status': t.status(report, 'disc_endplate_clearance')['status'],
    }
    candidate['bones']['radius_left']['parent_relation'] = {'type': 'banana'}
    report = t.run(candidate)
    result['unknown_parent_relation'] = {
        'verdict': report['verdict'],
        'parent_status': t.status(report, 'parent_tree')['status'],
    }
    return result


if __name__ == '__main__':
    print(json.dumps(observe(), indent=2))
