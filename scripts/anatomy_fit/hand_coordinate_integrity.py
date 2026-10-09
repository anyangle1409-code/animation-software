#!/usr/bin/env python3
"""Independent stored-coordinate audit; no builder, probe or containment imports.

Rigid correspondence and numerical continuity are reproducibility findings,
never proof of correct anatomy. Carpal sticks are not contact envelopes.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ANAT = Path(__file__).resolve().parents[2] / 'ORIGINAL_V1_WORK/anatomy'
PATHS = (ANAT / 'character_fit_r95_a003.json', ANAT /
         'audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json')
ENDS = ('head_m', 'tail_m')
NUMERIC_M = 1e-6  # coordinate rounding only; not an anatomical tolerance


def load_records():
    return tuple(json.loads(p.read_text()) for p in PATHS)


def vector(value):
    x = np.asarray(value, float)
    if x.shape != (3,) or not np.isfinite(x).all():
        raise ValueError('expected finite 3-vector')
    return x


def analyse(a, c):
    rows, translated, wrist, mirrors, connections, markers = [], [], [], [], [], []
    names = []
    for side in ('left', 'right'):
        shift = vector(c['joint_markers'][f'glenohumeral_{side}']['centre_m']) - vector(
            a['joint_markers'][f'glenohumeral_{side}']['centre_m'])
        w0 = vector(a['skeleton_input']['sides'][side]['WJC'])
        w1 = vector(c['skeleton_input']['sides'][side]['WJC'])
        if np.linalg.norm(w1 - w0 - shift) > NUMERIC_M:
            raise ValueError('wrist centre not a rigid translation')
        for group in ('carpals', 'hand'):
            source = a['skeleton_input']['sides'][side][group]
            expected_keys = ({'scaphoid', 'lunate', 'triquetrum', 'pisiform', 'trapezium',
                              'trapezoid', 'capitate', 'hamate'} if group == 'carpals' else
                             {f'mc{i}' for i in range(1, 6)} | {'th_pp', 'th_dp'} |
                             {f'd{i}_{p}' for i in range(2, 6) for p in ('pp', 'mp', 'dp')})
            if set(source) != expected_keys:
                raise ValueError('hand input identity changed')
            for key, pair in source.items():
                if group == 'carpals':
                    name = f'{key}_{side}'
                elif key.startswith('mc'):
                    name = f'metacarpal_{key[2:]}_{side}'
                else:
                    digit, part = key.split('_')
                    prefix = 'thumb' if digit == 'th' else f'digit{digit[1:]}'
                    name = f'{prefix}_{dict(pp="proximal", mp="middle", dp="distal")[part]}_phalanx_{side}'
                names.append(name)
                if len(pair) != 2:
                    raise ValueError('endpoint pair required')
                for index, end in enumerate(ENDS):
                    inp, old, new = vector(pair[index]), vector(a['bones'][name][end]), vector(c['bones'][name][end])
                    residual = float(np.linalg.norm(new - old - shift))
                    if residual > NUMERIC_M:
                        raise ValueError(f'{name}:{end} not a rigid translation')
                    translated.append(residual * 1000)
                    offset = float(np.linalg.norm(inp - old))
                    if offset > 1e-9:
                        if 'distal_phalanx' not in name or end != 'tail_m':
                            raise ValueError('unresolved point outside distal tip')
                        recorded = a['bones'][name].get('containment_adjustment_m', {}).get(end)
                        if recorded is None or abs(offset - recorded) > 1e-9:
                            raise ValueError('tip offset not explained by recorded containment')
                    stale = c['skeleton_input']['sides'][side][group][key][index] == pair[index]
                    if not stale:
                        raise ValueError('stale input premise changed')
                    rows.append({'bone': name, 'endpoint': end, 'source_offset_mm': offset * 1000,
                                 'classification': 'EXACT' if offset <= 1e-9 else 'UNRESOLVED_TIP'})
                    if group == 'carpals':
                        wrist.append(float(np.linalg.norm((new - w1) - (old - w0))) * 1000)
                if group == 'hand' and not key.startswith('mc'):
                    b = c['bones'][name]
                    gap = float(np.linalg.norm(vector(b['head_m']) - vector(c['bones'][b['parent']]['tail_m'])))
                    if gap > NUMERIC_M:
                        raise ValueError(f'digit continuity: {name}')
                    connections.append(gap * 1000)
                    prefix = 'thumb' if key.startswith('th') else f'digit{key[1]}'
                    joint = ('mcp' if key.endswith('pp') else 'ip' if prefix == 'thumb' else
                             'pip' if key.endswith('mp') else 'dip')
                    centre = vector(c['joint_markers'][f'{prefix}_{joint}_{side}']['centre_m'])
                    error = float(np.linalg.norm(centre - vector(b['head_m'])))
                    if error > NUMERIC_M:
                        raise ValueError(f'digit marker: {name}')
                    markers.append(error * 1000)
        # Wrist forearm endpoint offsets are measured, not forced to connect to
        # carpal stick endpoints (those are not articular-surface landmarks).
        for bone in ('radius', 'ulna'):
            name = f'{bone}_{side}'
            p0, p1 = vector(a['bones'][name]['tail_m']), vector(c['bones'][name]['tail_m'])
            wrist.append(float(np.linalg.norm((p1 - w1) - (p0 - w0))) * 1000)
    for name in names:
        if name.endswith('_left'):
            right = name[:-5] + '_right'
            error = max(float(np.linalg.norm(vector(c['bones'][name][e]) * [-1, 1, 1] -
                                             vector(c['bones'][right][e]))) for e in ENDS)
            if error > NUMERIC_M:
                raise ValueError(f'hand mirror: {name}')
            mirrors.append(error * 1000)
    return {'kind': 'INDEPENDENT_STORED_HAND_COORDINATE_AUDIT', 'points': len(rows),
            'exact': sum(x['classification'] == 'EXACT' for x in rows),
            'unresolved': sum(x['classification'] == 'UNRESOLVED_TIP' for x in rows),
            'translation_residual_max_mm': max(translated), 'paired_bones': len(mirrors),
            'mirror_max_mm': max(mirrors), 'digit_connections': len(connections),
            'digit_connection_max_mm': max(connections), 'digit_marker_max_mm': max(markers),
            'wrist_reference_points': len(wrist), 'wrist_relative_residual_max_mm': max(wrist),
            'anatomical_acceptance': False, 'promotion_allowed': False,
            'limitations': ['Wrist relative placement preserved, not independently sourced.',
                            'Carpal centroids, contact surfaces and axes remain unaccepted.',
                            'All ten distal tails require bone-versus-soft-tissue endpoint evidence.'],
            'details': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    report = analyse(*load_records())
    report['input_sha256'] = {str(p.relative_to(ANAT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in PATHS}
    with args.out.open('x') as f:
        json.dump(report, f, indent=2, allow_nan=False)
        f.write('\n')
    print({k: v for k, v in report.items() if k not in ('details', 'input_sha256')})


if __name__ == '__main__':
    main()
