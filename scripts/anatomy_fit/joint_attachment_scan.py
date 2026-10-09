#!/usr/bin/env python3
"""Joint attachment (closure) invariant over committed Phase 9 isolated-test samples (read-only; no geometry change).

For every articulation in the project inventory (427; participants from canonical_articulation inventory via
cp2_preflight.load_reference) and every sampled frame of every isolated test, each participant bone carries its own copy
of the joint centre (rest centre transformed by the world delta of that bone's nearest commanded ancestor; unmoved bones
keep it at rest). The joint OPENING is the largest distance between the participants' copies. A rigidly connected or
commanded-centre joint stays at 0; any other value means the sweep separates the two bones at that joint.

Reported, never tolerance-graded beyond numerics: openings below 1e-6 m are numerical zero; every larger opening is listed
with the tests and frames where it occurs, its articulation role/type, and whether it is shared by a003 and the candidate.

  joint_attachment_scan.py --record R.json --samples S.json --label NAME --out JSON [--stride 2]
"""
import argparse, hashlib, importlib.util, json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ZERO_M = 1e-6


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def articulations():
    spec = importlib.util.spec_from_file_location('cp2', HERE / 'cp2_preflight.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.load_reference()[1]


def scan(rec, samples, stride=2, partial=False):
    """partial=False: v1 (only articulations whose participants are ALL bones; 59 of 427 with a soft-tissue participant -
    TFCC, disc, cartilage, sesamoid track - were silently skipped, among them radiocarpal and sternoclavicular).
    partial=True: v2, every articulation with >= 2 BONE participants is checked on those bones; the soft-tissue
    participants dropped are listed."""
    B, J = rec['bones'], rec['joint_markers']
    parent = {n: B[n]['parent'] for n in B}
    if partial:
        arts, dropped = [], {}
        for a in articulations():
            ps = [p for p in a['participants'] if p in B]
            if a['id'] in J and len(ps) >= 2:
                arts.append({**a, 'participants': ps})
                if len(ps) < len(a['participants']):
                    dropped[a['id']] = [p for p in a['participants'] if p not in B]
    else:
        arts = [a for a in articulations() if a['id'] in J and len(a['participants']) >= 2 and all(p in B for p in a['participants'])]
        dropped = None

    def anc(n, deltas):
        m = n
        while m is not None:
            if m in deltas:
                return deltas[m]
            m = parent[m]
        return None
    worst = {}
    for tid, frames in samples.items():
        for fr in frames[::stride]:
            deltas = {k: np.array(v) for k, v in fr['moving_deltas'].items()}
            for a in arts:
                ds = [anc(p, deltas) for p in a['participants']]
                if all(d is None for d in ds):
                    continue
                c0 = np.array(J[a['id']]['centre_m'], float)
                pts = [c0 if d is None else d[:3, :3] @ c0 + d[:3, 3] for d in ds]
                op = max(float(np.linalg.norm(pts[i] - pts[j])) for i in range(len(pts)) for j in range(i + 1, len(pts)))
                if op > ZERO_M:
                    k = a['id']
                    w = worst.setdefault(k, {'role': a.get('role'), 'type': f"{a.get('structural_type')}/{a.get('subtype')}",
                                             'participants': a['participants'], 'max_opening_mm': 0.0, 'tests': {}})
                    w['tests'][tid] = max(w['tests'].get(tid, 0.0), round(op * 1000, 3))
                    if op * 1000 > w['max_opening_mm']:
                        w['max_opening_mm'] = round(op * 1000, 3); w['worst_test'] = tid; w['worst_frame'] = fr['frame']
    out_extra = {} if dropped is None else {'scan_version': 2, 'soft_tissue_participants_dropped': dropped}
    return {**out_extra, 'articulations_checked': len(arts), 'tests_scanned': len(samples), 'stride': stride,
            'opened': dict(sorted(worst.items(), key=lambda kv: -kv[1]['max_opening_mm']))}


def main():
    ap = argparse.ArgumentParser()
    for a in ('--record', '--samples', '--label', '--out'):
        ap.add_argument(a, required=True)
    ap.add_argument('--stride', type=int, default=2)
    ap.add_argument('--v2', action='store_true', help='also check articulations with soft-tissue participants on their bone participants')
    o = ap.parse_args()
    r = scan(json.loads(Path(o.record).read_text()), json.loads(Path(o.samples).read_text()), o.stride, partial=o.v2)
    out = {'schema_version': 1, 'created': '2026-10-09', 'label': o.label, 'status': 'MECHANICAL_SCAN_NO_GEOMETRY_CHANGE',
           'criterion': 'opening = max distance between participant copies of the rest joint centre; < 1e-6 m is numerical zero; larger openings reported, not graded',
           'inputs_sha256': {o.record: sha(o.record), o.samples: sha(o.samples)}, **r}
    Path(o.out).write_text(json.dumps(out, indent=1) + '\n')
    print(o.label, 'articulations', r['articulations_checked'], 'opened', len(r['opened']))
    for k, v in list(r['opened'].items())[:40]:
        print(f"  {k:42s} {v['role']:10s} {v['type']:28s} max {v['max_opening_mm']:8.2f} mm  tests {len(v['tests'])}  worst {v['worst_test']}")


if __name__ == '__main__':
    main()
