#!/usr/bin/env python3
"""Diagnostic proposal P003 (NOT a candidate, NOT canonical, not c005): explicit intervertebral disc spaces L5-C3 by
re-partitioning c004's own spinal curve.

Proven defect (U5; canonical_spine_geometry_audit_v1.json, CP2): every C2/C3-L4/L5 motion segment has a 0.00 mm centre-line
gap; the vertebral sticks absorbed the discs.

Why a curve-preserving re-partition (spine_column_length_discriminator_v1.json, spine_rebuild_feasibility_p002_v1.json):
  * thoracic source A (THORACIC_BODY_DISC_2011 body heights) is incompatible with a 1.82 m man (ANSUR cervicale closure needs
    a 1.43-1.49 m source cohort); source B (THORACIC_CT_2016) with male MRI edge lumbar heights needs a 1.74 m cohort;
  * that stack (bodies + discs, L5 inferior endplate to C2/C3 disc) sums to within 1 % of c004's existing L5-head to
    C2-head arc, so the existing c004 curve can carry it without changing its length;
  * a bottom-up rebuild from the provisional P1 S1 anchor with mean angles moves the thoracic column 40-66 mm anterior and
    leaves the upper thoracic bodies only 40-56 mm behind the skin jugular notch (c004: 91 mm); the sagittal closure is
    therefore an OPEN problem and is deliberately NOT touched here.

Construction (isolated): the c004 polyline l5.head -> l5.tail=l4.head -> ... -> c3.tail=c2.head is kept exactly. Along its
arc length, from the fixed l5.head to the fixed c2.head, the sourced heights are laid out in order
  L5 body, L4/L5 disc, L4 body, ..., T12/L1 disc, T12 body, ..., T1 body, C7/T1 disc, C7 body, ..., C3 body, C2/C3 disc
with ONE uniform factor s (reported) so that the sum equals the c004 arc. Each vertebra's head/tail move to its arc
positions (points on the c004 curve). Disc markers move to the gap midpoint; facet markers translate with their disc
marker; marker frames rotate with their frame bone by the minimal rotation. Sacrum, L5/S1, C2, C1, skull, ribs, sternum
and every other bone are byte-identical to c004 (test-enforced). Rib heads are not moved; their offset from the level
they articulate with is reported before and after.

Heights: L1-L5 bodies and L1/L2-L4/L5 discs = mean of Hegazy 2014 male MRI anterior/posterior edge heights; T12/L1 =
LUMBAR_DISC_CT_2018 male; T1-T12 bodies = THORACIC_CT_2016 mean of anterior/posterior; thoracic discs =
THORACIC_BODY_DISC_2011 (the only committed per-level thoracic disc table); C7/T1 = 4.5 mm (anatomical; the 6.1 mm
radiographic value is the recorded conflict); C3-C7 bodies and C2/C3-C6/C7 discs = Yukawa 2012 male.

  build_proposal_p003_spine_discs.py --out-dir DIR
"""
import argparse, copy, hashlib, json, math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
BASE = ANAT / 'audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json'
BASE_SHA = '99500d94e06c66ca'
CHAIN = ['l5', 'l4', 'l3', 'l2', 'l1'] + [f't{i}' for i in range(12, 0, -1)] + ['c7', 'c6', 'c5', 'c4', 'c3']   # inferior->superior


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def disc_id(lower, upper):
    return f'disc_{upper}_{lower}'          # c004 ids name the superior vertebra first: disc_c7_t1, disc_l4_l5


def sourced_heights():
    stack = json.loads((ANAT / 'canonical_spine_level_stack_v1.json').read_text())
    edges = json.loads((ANAT / 'canonical_lumbar_edge_height_crosscheck_v1.json').read_text())
    props = json.loads((ANAT / 'canonical_proportion_sources_v1.json').read_text())
    srcB = _find_source(props, 'THORACIC_CT_2016_INDIA')['body_height_anterior_posterior_mm']
    body, disc, prov = {}, {}, {}
    for lv in ['L1', 'L2', 'L3', 'L4', 'L5']:
        e = edges['body_edge_heights'][lv]; body[lv.lower()] = (e['anterior_mean_mm'] + e['posterior_mean_mm']) / 2
        prov[lv.lower()] = 'HEGAZY_2014_LUMBAR_MRI male edge mean'
    for a, b in [('L1', 'L2'), ('L2', 'L3'), ('L3', 'L4'), ('L4', 'L5')]:
        e = edges['disc_edge_gaps'][f'{a}/{b}']; disc[(b.lower(), a.lower())] = (e['anterior_mean_mm'] + e['posterior_mean_mm']) / 2
        prov[disc_id(b.lower(), a.lower())] = 'HEGAZY_2014_LUMBAR_MRI male edge mean'
    disc[('l1', 't12')] = stack['disc_gaps_mm']['T12/L1']['candidate']; prov['disc_t12_l1'] = 'LUMBAR_DISC_CT_2018 male'
    for i in range(1, 13):
        a, p = srcB[f'T{i}']; body[f't{i}'] = (a + p) / 2; prov[f't{i}'] = 'THORACIC_CT_2016_INDIA mean anterior/posterior'
    for i in range(1, 12):
        disc[(f't{i + 1}', f't{i}')] = stack['disc_gaps_mm'][f'T{i}/T{i + 1}']['candidate']
        prov[disc_id(f't{i + 1}', f't{i}')] = 'THORACIC_BODY_DISC_2011 direct anatomical'
    disc[('t1', 'c7')] = stack['disc_gaps_mm']['C7/T1']['candidate']; prov['disc_c7_t1'] = 'THORACIC_BODY_DISC_2011 (radiographic 6.1 recorded conflict)'
    for c in ['C3', 'C4', 'C5', 'C6', 'C7']:
        body[c.lower()] = stack['vertebral_bodies_mm'][c]['candidate']; prov[c.lower()] = 'YUKAWA_2012 male'
    for a, b in [('C2', 'C3'), ('C3', 'C4'), ('C4', 'C5'), ('C5', 'C6'), ('C6', 'C7')]:
        disc[(b.lower(), a.lower())] = stack['disc_gaps_mm'][f'{a}/{b}']['candidate']; prov[disc_id(b.lower(), a.lower())] = 'YUKAWA_2012 male'
    return body, disc, prov


def _find_source(x, sid):
    if isinstance(x, dict):
        if x.get('id') == sid:
            return x
        for v in x.values():
            r = _find_source(v, sid)
            if r is not None:
                return r
    elif isinstance(x, list):
        for v in x:
            r = _find_source(v, sid)
            if r is not None:
                return r
    return None


class Polyline:
    def __init__(self, pts):
        self.p = [np.asarray(x, float) for x in pts]
        self.s = np.concatenate([[0.0], np.cumsum([np.linalg.norm(b - a) for a, b in zip(self.p, self.p[1:])])])

    def at(self, s):
        if s <= 0:
            return self.p[0].copy()
        if s >= self.s[-1]:
            return self.p[-1].copy()
        i = int(np.searchsorted(self.s, s) - 1)
        t = (s - self.s[i]) / (self.s[i + 1] - self.s[i])
        return self.p[i] + t * (self.p[i + 1] - self.p[i])


def min_rotation(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); c = float(a @ b)
    if np.linalg.norm(v) < 1e-15:
        return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * (1 / (1 + c))


def rib_levels(B):
    """Rib head (bone head) vertical offset from its articular level: rib 1 -> T1 body centre; ribs 2-9 -> disc between
    T(n-1) and T(n) (demifacets); ribs 10-12 -> own vertebra body centre (standard costovertebral anatomy)."""
    out = {}
    for n in range(1, 13):
        for side in ('left', 'right'):
            h = np.asarray(B[f'rib_{n:02d}_{side}']['head_m'])
            if 2 <= n <= 9:
                lo, up = B[f't{n}'], B[f't{n - 1}']
                level = (np.asarray(lo['tail_m']) + np.asarray(up['head_m'])) / 2
                kind = f'T{n - 1}/T{n} disc'
            else:
                v = B[f't{n}']; level = (np.asarray(v['head_m']) + np.asarray(v['tail_m'])) / 2
                kind = f'T{n} body centre'
            out[f'rib_{n:02d}_{side}'] = {'level': kind, 'head_minus_level_z_mm': round(float(h[2] - level[2]) * 1000, 2)}
    return out


def build():
    assert sha(BASE).startswith(BASE_SHA)
    base = json.loads(BASE.read_text()); out = copy.deepcopy(base)
    B, J = out['bones'], out['joint_markers']
    for lo, up in zip(CHAIN, CHAIN[1:]):
        assert np.allclose(B[lo]['tail_m'], B[up]['head_m'], atol=1e-9), f'{lo}->{up} not contiguous in c004'
    assert np.allclose(B['c3']['tail_m'], B['c2']['head_m'], atol=1e-9)
    pts = [B[v]['head_m'] for v in CHAIN] + [B['c3']['tail_m']]
    poly = Polyline(pts)
    body, disc, prov = sourced_heights()
    seq = []
    for i, v in enumerate(CHAIN):
        seq.append(('body', v, body[v]))
        nxt = CHAIN[i + 1] if i + 1 < len(CHAIN) else 'c2'
        seq.append(('disc', (v, nxt), disc[(v, nxt)]))
    total = sum(h for _, _, h in seq)
    s = poly.s[-1] * 1000 / total
    pos, table, before = 0.0, [], rib_levels(base['bones'])
    old = {v: (np.asarray(B[v]['head_m']), np.asarray(B[v]['tail_m'])) for v in CHAIN}
    disc_rows = {}
    for kind, key, h in seq:
        a = poly.at(pos / 1000); pos += h * s; b = poly.at(pos / 1000)
        if kind == 'body':
            B[key]['head_m'], B[key]['tail_m'] = a.tolist(), b.tolist()
            o_h, o_t = old[key]
            table.append({'bone': key, 'source': prov[key], 'source_height_mm': round(h, 3), 'scaled_height_mm': round(h * s, 3),
                          'c004_length_mm': round(float(np.linalg.norm(o_t - o_h)) * 1000, 3),
                          'centre_shift_mm': round(float(np.linalg.norm((a + b) / 2 - (o_h + o_t) / 2)) * 1000, 3)})
        else:
            lo, up = key
            disc_rows[disc_id(lo, up)] = {'source': prov[disc_id(lo, up)], 'source_height_mm': round(h, 3), 'scaled_height_mm': round(h * s, 3),
                                          'gap_start': a.tolist(), 'gap_end': b.tolist()}
    assert abs(pos / 1000 - poly.s[-1]) < 1e-12
    # markers: disc centre to the gap midpoint; facets translate with it; frames rotate with the frame bone
    rot = {v: min_rotation(old[v][1] - old[v][0], np.asarray(B[v]['tail_m']) - np.asarray(B[v]['head_m'])) for v in CHAIN}
    moved = []
    for did, row in disc_rows.items():
        m = J[did]
        new_c = (np.asarray(row['gap_start']) + np.asarray(row['gap_end'])) / 2
        delta = new_c - np.asarray(m['centre_m'])
        m['centre_m'] = new_c.tolist(); moved.append(did)
        lvl = did[len('disc_'):]
        for side in ('left', 'right'):
            f = J[f'facet_{lvl}_{side}']
            f['centre_m'] = (np.asarray(f['centre_m']) + delta).tolist(); moved.append(f'facet_{lvl}_{side}')
        row['marker_shift_mm'] = round(float(np.linalg.norm(delta)) * 1000, 3)
    for k, m in J.items():
        if m.get('frame_bone') in rot:
            R = rot[m['frame_bone']]
            m['frame_axes_columns_XYZ'] = (R @ np.asarray(m['frame_axes_columns_XYZ'])).tolist()
    after = rib_levels(B)
    ribs = {k: {'level': before[k]['level'], 'c004_head_minus_level_z_mm': before[k]['head_minus_level_z_mm'],
                'p003_head_minus_level_z_mm': after[k]['head_minus_level_z_mm']} for k in before}
    out['candidate'] = {
        'id': 'P003_SPINE_DISC_REPARTITION_DIAGNOSTIC_PROPOSAL', 'status': 'DIAGNOSTIC_PROPOSAL_NOT_A_CANDIDATE_NOT_CANONICAL', 'freeze_ready': False,
        'derived_from': {'record': str(BASE.relative_to(ROOT)), 'sha256': sha(BASE)},
        'uniform_scale_to_c004_arc': round(s, 6), 'c004_arc_l5head_to_c2head_mm': round(poly.s[-1] * 1000, 3),
        'sourced_sum_mm': round(total, 3), 'bodies': table, 'discs': {k: {x: v for x, v in r.items() if x not in ('gap_start', 'gap_end')}
                                                                       for k, r in disc_rows.items()},
        'rib_head_levels': ribs, 'moved_markers': sorted(moved),
        'evidence': ['spine_column_length_discriminator_v1.json', 'spine_rebuild_feasibility_p002_v1.json', 'canonical_spine_level_stack_v1.json',
                     'canonical_lumbar_edge_height_crosscheck_v1.json', 'canonical_proportion_sources_v1.json (THORACIC_CT_2016_INDIA)'],
        'not_changed': 'sacrum, L5/S1 relation, C2, C1, skull, ribs, sternum, girdles, limbs; the c004 curve itself (sagittal closure '
                       'S1/P1 vs thorax depth is OPEN); thoracic per-level wedging; skeleton_input as in c004',
    }
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out-dir', required=True); o = ap.parse_args()
    d = Path(o.out_dir)
    if d.exists():
        raise FileExistsError(d)
    out = build(); d.mkdir(parents=True)
    (d / 'proposal_record.json').write_text(json.dumps(out, indent=1) + '\n')
    c = out['candidate']
    print('scale', c['uniform_scale_to_c004_arc'], 'arc', c['c004_arc_l5head_to_c2head_mm'], 'sourced', c['sourced_sum_mm'])
    for r in c['bodies']:
        print(f"  {r['bone']:4s} {r['c004_length_mm']:7.2f} -> {r['scaled_height_mm']:6.2f}  centre shift {r['centre_shift_mm']:5.2f}")
    for k, r in c['discs'].items():
        print(f"  {k:12s} {r['scaled_height_mm']:5.2f}  marker shift {r['marker_shift_mm']:5.2f}")


if __name__ == '__main__':
    main()
