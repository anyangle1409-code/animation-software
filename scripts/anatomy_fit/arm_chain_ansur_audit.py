#!/usr/bin/env python3
"""Arm-chain consistency under the ANSUR shoulder (read-only audit; selects nothing).

c003 placed the bony acromion at ANSUR acromial height and moved the arm rigidly with GH; this checks what that does to
the elbow and wrist against ANSUR's own stature-conditioned (1.82 m, n = 4,082, OLS) standing relations, for a003, c001,
c002 and c003 on identical rules:
  * radiale height  = per-subject acromial height - acromion-radiale length (regressed as a difference)
  * stylion height  = ANSUR wrist height (standing; wrist landmark = stylion)
  * radiale-stylion = ANSUR radiale-stylion length
Model proxies (labelled): radiale = elbow centre (humeroulnar marker) - 15 mm in z (project convention in
proportion_audit.py, unsourced here; results also shown without it); stylion = radiocarpal marker height. Acromion = the
candidate's ANSUR-border acromion point (c001/c002/c003: Lee LM25-LM27 crossing of the clavicle-axis line); a003 has no
bony acromion landmarks, so its authored-mesh acromion skin point (AC + 12 mm, generator rule) is used and labelled.
Values are z-scores against ANSUR residual SDs; no tolerance is applied.

  arm_chain_ansur_audit.py --out JSON
"""
import argparse, csv, hashlib, json, math, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import shoulder_ansur_acromion_audit as au  # noqa: E402

ROOT = HERE.parents[1]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
CSV = ANAT / 'sources/ansur2/ANSUR_II_MALE_Public.csv'
RECORDS = {
    'a003': ANAT / 'character_fit_r95_a003.json',
    'c001': ANAT / 'audit/candidates/shoulder_proposal_c001/candidate_record.json',
    'c002': ANAT / 'audit/candidates/shoulder_proposal_c002_ansur_height/candidate_record.json',
    'c003': ANAT / 'audit/candidates/shoulder_thorax_c003_ansur_coupled/candidate_record.json',
}
RADIALE_BELOW_EJC_MM = 15.0
H = 1820.0


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def r1(x):
    return round(float(x), 1)


def ansur():
    with open(CSV, encoding='latin-1') as f:
        rows = list(csv.DictReader(f))
    s = np.array([float(r['stature']) for r in rows])
    col = lambda k: np.array([float(r[k]) for r in rows])
    out = {}
    for name, y in (('acromial_height', col('acromialheight')), ('radiale_height', col('acromialheight') - col('acromionradialelength')),
                    ('stylion_height_wristheight', col('wristheight')), ('acromion_radiale', col('acromionradialelength')),
                    ('radiale_stylion', col('radialestylionlength'))):
        b = np.polyfit(s, y, 1); res = y - np.polyval(b, s)
        out[name] = {'mean': r1(np.polyval(b, H)), 'residual_sd': r1(res.std(ddof=2))}
    out['_n'] = len(rows)
    return out


def acromion_point(name, rec):
    """World mm of the candidate's ANSUR acromion correspondence (left side)."""
    if name == 'a003':
        return np.asarray(rec['joint_markers']['acromioclavicular_left']['centre_m'], float) * 1000 + [0, 0, 12.0], 'a003 authored-mesh acromion skin point (AC + 12 mm generator rule); not a bony landmark'
    L = np.asarray(rec['candidate']['scapula_landmarks_world_mm']['left'], float)
    sc = np.asarray(rec['joint_markers']['sternoclavicular_left']['centre_m'], float) * 1000
    ac = np.asarray(rec['joint_markers']['acromioclavicular_left']['centre_m'], float) * 1000
    d = np.array([ac[1] - sc[1], ac[0] - sc[0]])                 # world transverse plane (y, x); pitch ignored (<0.2 mm here)
    a25, a27 = L[24], L[26]
    M = np.array([[d[0], a25[1] - a27[1]], [d[1], a25[0] - a27[0]]])
    s_, t = np.linalg.solve(M, np.array([a25[1] - ac[1], a25[0] - ac[0]]))
    return a25 + t * (a27 - a25), f'Lee LM25-LM27 lateral-border crossing of the clavicle-axis line (t = {t:.3f})'


def build():
    A = ansur()
    out = {}
    for name, p in RECORDS.items():
        rec = json.loads(p.read_text()); J = rec['joint_markers']
        z = lambda k: float(J[k]['centre_m'][2]) * 1000
        acr, acr_def = acromion_point(name, rec)
        gh, ejc, wjc = z('glenohumeral_left'), z('humeroulnar_left'), z('radiocarpal_left')
        rad = ejc - RADIALE_BELOW_EJC_MM
        zs = lambda v, k: round((v - A[k]['mean']) / A[k]['residual_sd'], 2)
        clear = None
        if name != 'a003':
            L = np.asarray(rec['candidate']['scapula_landmarks_world_mm']['left'], float); ghp = np.asarray(J['glenohumeral_left']['centre_m'], float) * 1000
            clear = {f'LM{i}': r1(np.linalg.norm(L[i - 1] - ghp) - 24.0) for i in (15, 16, 17, 18, 19, 25, 26, 27)}
        out[name] = {
            'acromion_definition': acr_def,
            'landmark_clearance_from_24mm_head_sphere_mm': clear,
            'acromion_z_mm': r1(acr[2]), 'acromion_z_vs_ANSUR': zs(acr[2], 'acromial_height'),
            'GH_depth_below_acromion_mm': r1(acr[2] - gh),
            'EJC_z_mm': r1(ejc), 'radiale_proxy_z_mm': r1(rad), 'radiale_z_vs_ANSUR': zs(rad, 'radiale_height'),
            'radiale_z_vs_ANSUR_without_15mm_offset': zs(ejc, 'radiale_height'),
            'acromion_minus_radiale_proxy_mm': r1(acr[2] - rad), 'acromion_radiale_z': zs(acr[2] - rad, 'acromion_radiale'),
            'WJC_z_mm': r1(wjc), 'stylion_z_vs_ANSUR_wristheight': zs(wjc, 'stylion_height_wristheight'),
            'radiale_proxy_minus_WJC_mm': r1(rad - wjc), 'radiale_stylion_z': zs(rad - wjc, 'radiale_stylion'),
        }
    return {
        'schema_version': 1, 'created': '2026-10-08', 'status': 'AUDIT_ONLY_NO_TARGET_SELECTED',
        'inputs_sha256': {str(p.relative_to(ROOT)): sha(p) for p in list(RECORDS.values()) + [CSV]},
        'ansur_at_182_mm': A,
        'proxies': {'radiale': f'elbow centre (humeroulnar) - {RADIALE_BELOW_EJC_MM} mm in z (project convention, proportion_audit.py; unsourced here)',
                    'stylion': 'radiocarpal marker height', 'note': 'vertical differences with the arm hanging; ANSUR lengths are caliper spans parallel to the segment'},
        'candidates': out,
        'reading': ('Raising the shoulder to bony-model geometry (c001) or lowering it to ANSUR (c003) moves the whole a003 arm with GH, '
                    'so elbow/wrist heights follow GH while the a003 arm lengths are kept. Compare acromion-radiale (upper-arm drop) '
                    'and radiale-stylion (forearm) z across candidates; the forearm shortness belongs to a003 and is unchanged by any '
                    'shoulder candidate. No arm target is selected here. In c003 the shoulder is on ANSUR but the elbow (radiale proxy) '
                    'sits high (acromion-radiale about 19 mm short, z -1.82): candidate causes are the a003 humerus GH-EJC length with '
                    'the bony GH, and the unsourced 15 mm radiale convention; unresolved. The shallow GH depth below the ANSUR acromion '
                    'point (26.5 mm) is not a collision: the point lies near the low posterolateral corner LM25, and every acromion '
                    'landmark clears the 24 mm head sphere by 17-25 mm while the glenoid rim lies 0-6 mm outside it (seated head).'),
    }


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True)
    o = ap.parse_args()
    r = build()
    Path(o.out).write_text(json.dumps(r, indent=1) + '\n')
    print(json.dumps({'ansur': r['ansur_at_182_mm'], 'c': r['candidates']}, indent=1))


if __name__ == '__main__':
    main()
