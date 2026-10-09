#!/usr/bin/env python3
"""Compare historical distal spans with radiographic context; never infer world endpoints."""
import argparse
import hashlib
import json
import math
from numbers import Real
from pathlib import Path

BONES = ('thumb_distal_phalanx', 'digit2_distal_phalanx', 'digit3_distal_phalanx',
         'digit4_distal_phalanx', 'digit5_distal_phalanx')
INPUT_KEYS = ('th_dp', 'd2_dp', 'd3_dp', 'd4_dp', 'd5_dp')
ROOT = Path(__file__).resolve().parents[2]


def point(value):
    if not isinstance(value, (list, tuple)) or len(value) != 3 or not all(
            isinstance(x, Real) and not isinstance(x, bool) and math.isfinite(x) for x in value):
        raise ValueError('finite XYZ required')
    return tuple(value)


def positive(value):
    if not isinstance(value, Real) or isinstance(value, bool) or not math.isfinite(value) or value <= 0:
        raise ValueError('positive finite source mean/SD and span required')
    return float(value)


def analyse(rec, source):
    if source.get('pmid') != '9823781':
        raise ValueError('expected Aydinlioglu 1998 radiographic source identity')
    rows = []
    for side in ('left', 'right'):
        for name, key in zip(BONES, INPUT_KEYS):
            h, t = (point(p) for p in rec['skeleton_input']['sides'][side]['hand'][key])
            bone = rec['bones'][name + '_' + side]
            bh, bt = point(bone['head_m']), point(bone['tail_m'])
            if math.dist(h, bh) > 1e-6:
                raise ValueError('input and bone frames disagree; register coordinates explicitly before tip-offset comparison')
            mean = positive(source['male_mean_sd_mm'][name]['mean'])
            sd = positive(source['male_mean_sd_mm'][name]['sd'])
            raw, stored = positive(math.dist(h, t) * 1000), positive(math.dist(bh, bt) * 1000)
            raw_z, stored_z = (raw - mean) / sd, (stored - mean) / sd
            if not math.isfinite(raw_z) or not math.isfinite(stored_z):
                raise ValueError('finite standardized comparison required')
            offset_m = math.dist(t, bt)
            history = bone.get('containment_adjustment_m', {}).get('tail_m')
            origin = 'UNVERIFIED'
            if history is not None:
                if (not isinstance(history, Real) or isinstance(history, bool) or not math.isfinite(history)
                        or history <= 0 or abs(history - offset_m) > 1e-9):
                    raise ValueError('containment metadata differs from observed raw/stored displacement')
                origin = 'RECORDED_CONTAINMENT_DISPLACEMENT'
            rows.append({'bone_base': name, 'side': side, 'raw_span_mm': raw, 'stored_span_mm': stored,
                         'source_mean_mm': mean, 'source_sd_mm': sd,
                         'raw_context_standardized_difference': raw_z,
                         'stored_context_standardized_difference': stored_z,
                         'raw_head_to_stored_head_mm': math.dist(h, bh) * 1000,
                         'tip_offset_mm': offset_m * 1000, 'endpoint_origin': origin,
                         'coordinate_status': 'UNVALIDATED', 'source_projection_equivalence_verified': False})
    return {'schema_version': 1, 'kind': 'READ_ONLY_HAND_TIP_LENGTH_CONTEXT',
            'source': {'legacy_id': source['id'], 'authors': ['Aydinlioglu', 'Akpinar', 'Tosun'],
                       'doi': '10.1620/tjem.185.209', 'pmid': '9823781',
                       'locator': 'Methods p210, Figure1 p211, Table5 p213',
                       'measurement': 'AP radiographic bony head/base boundary midpoints; not skin tip or necessarily joint rotation centre'},
            'model_measurement': '3D Euclidean head-to-tail station span',
            'stored_endpoint_origin': ('legacy_mesh_containment_not_anatomical_evidence'
                if all(x['endpoint_origin'] == 'RECORDED_CONTAINMENT_DISPLACEMENT' for x in rows)
                else 'UNVERIFIED_RECORD_ENDPOINT_ORIGIN'),
            'origin_claim_basis': 'Where recorded, scalar adjustments were checked against displacement; operation history not independently established by this function.',
            'anatomical_acceptance': False, 'coordinate_replacement_allowed': False,
            'limitations': ['Population mean/SD is context, not an individual target or hard limit.',
                           'AP projection versus 3D joint-station endpoints remains unresolved.',
                           'No stature-conditioned 1.82 m target or world-coordinate derivation.',
                           'Agreement after containment cannot validate a skeletal endpoint.'], 'rows': rows}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--record', required=True); ap.add_argument('--out', required=True)
    o = ap.parse_args()
    p = ROOT / 'ORIGINAL_V1_WORK/anatomy/canonical_proportion_sources_v1.json'
    source = next(s for s in json.loads(p.read_text())['sources'] if s['id'] == 'DOGAN_1998_HAND_RELATIONS')
    r = analyse(json.loads(Path(o.record).read_text()), source)
    r['inputs_sha256'] = {o.record: hashlib.sha256(Path(o.record).read_bytes()).hexdigest(),
                          str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()}
    content = json.dumps(r, indent=2, allow_nan=False) + '\n'
    with Path(o.out).open('x') as f:
        f.write(content)
    print({'points': len(r['rows']), 'anatomical_acceptance': r['anatomical_acceptance'],
           'raw_context_standardized_difference_range': [min(x['raw_context_standardized_difference'] for x in r['rows']),
                                                        max(x['raw_context_standardized_difference'] for x in r['rows'])]})


if __name__ == '__main__':
    main()
