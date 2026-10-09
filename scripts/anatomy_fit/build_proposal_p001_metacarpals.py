#!/usr/bin/env python3
"""Diagnostic proposal P001 (NOT a candidate, NOT canonical): metacarpals 2-4 at the male radiographic means.

Proven defect (canonical_hand_ray_target_constraints_v1.json, canonical_evidence_convergence_v1.json): a003/c004 M2/M3/M4
CMC-to-MCP spans 58.4 / 54.0 / 51.6 mm are below two independent male sources that agree with each other within 2.1 mm:
Aydinlioglu 1998 AP radiographs (50 men; 68+-4 / 64+-4 / 58+-4 mm) and the 2025 CT series (67.7 / 66.1 / 58.0 mm).
Target used here: the Aydinlioglu means, because every other hand comparison in the project uses that study's endpoint
definition (head/base midpoints); the CT means are recorded as the independent confirmation. M1 and M5 are within 1 SD and
unchanged.

Construction (isolated; nothing else changes): base on c004. For d in 2,3,4: the metacarpal head (CMC end) is FIXED; its tail
(MCP end) moves along the existing metacarpal axis to the target length; the whole digit chain (proximal, middle, distal
phalanx) and its MCP / PIP / DIP joint markers translate by the same vector (asserted coincident before moving). CMC and
intermetacarpal markers, the carpus and every other bone are untouched. Because exact canonical CMC positions are BLOCKED
(carpal geometry), this proposal only demonstrates the direction and its consequences; it must not be promoted.

  build_proposal_p001_metacarpals.py --out-dir DIR
"""
import argparse, copy, hashlib, json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
BASE = ANAT / 'audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json'
BASE_SHA = '99500d94e06c66ca'
TARGET_MM = {2: 68.0, 3: 64.0, 4: 58.0}
CT_MM = {2: 67.7, 3: 66.1, 4: 58.0}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build():
    assert sha(BASE).startswith(BASE_SHA)
    base = json.loads(BASE.read_text()); out = copy.deepcopy(base)
    B, J = out['bones'], out['joint_markers']; table = []
    for side in ('left', 'right'):
        for d, Lt in TARGET_MM.items():
            mc = B[f'metacarpal_{d}_{side}']
            h, t = np.asarray(mc['head_m']), np.asarray(mc['tail_m']); L0 = np.linalg.norm(t - h); u = (t - h) / L0
            new_t = h + u * Lt / 1000; delta = new_t - t
            chain = [f'digit{d}_{p}_phalanx_{side}' for p in ('proximal', 'middle', 'distal')]
            assert np.allclose(B[chain[0]]['head_m'], t, atol=1e-9), 'proximal phalanx not seated on the MC head'
            markers = [f'digit{d}_{j}_{side}' for j in ('mcp', 'pip', 'dip')]
            ends = [t] + [np.asarray(B[c]['tail_m']) for c in chain[:2]]
            for m, e in zip(markers, ends):
                assert np.allclose(J[m]['centre_m'], e, atol=1e-9), f'{m} not at its chain endpoint'
            mc['tail_m'] = new_t.tolist()
            for c in chain:
                for e in ('head_m', 'tail_m'):
                    B[c][e] = (np.asarray(B[c][e]) + delta).tolist()
            for m in markers:
                J[m]['centre_m'] = (np.asarray(J[m]['centre_m']) + delta).tolist()
            table.append({'side': side, 'metacarpal': d, 'before_mm': round(L0 * 1000, 3), 'after_mm': Lt, 'ct_mean_mm': CT_MM[d],
                          'translation_mm': [round(x * 1000, 3) for x in delta], 'translated_bones': chain, 'translated_markers': markers})
    out['candidate'] = {'id': 'P001_METACARPAL_M2_M4_DIAGNOSTIC_PROPOSAL', 'status': 'DIAGNOSTIC_PROPOSAL_NOT_A_CANDIDATE_NOT_CANONICAL', 'freeze_ready': False,
                        'derived_from': {'record': str(BASE.relative_to(ROOT)), 'sha256': sha(BASE)}, 'changes': table,
                        'evidence': ['DOGAN_1998_HAND_RELATIONS (Aydinlioglu 1998)', 'BEREDJIKLIAN_2025_METACARPAL_HEIGHT'],
                        'not_changed': 'carpus, CMC and intermetacarpal markers, M1, M5, thumb, all other bones; skeleton_input left as in c004 (stale hand points are a recorded c004 residue)'}
    return out, table


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out-dir', required=True); o = ap.parse_args()
    d = Path(o.out_dir)
    if d.exists():
        raise FileExistsError(d)
    out, table = build(); d.mkdir(parents=True)
    (d / 'proposal_record.json').write_text(json.dumps(out, indent=1) + '\n')
    for t in table:
        print(t['side'], t['metacarpal'], t['before_mm'], '->', t['after_mm'], 'translation', t['translation_mm'])


if __name__ == '__main__':
    main()
