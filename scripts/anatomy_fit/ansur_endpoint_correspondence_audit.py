#!/usr/bin/env python3
"""ANSUR II endpoint correspondence audit for the arm chain and trunk anchors (read-only; selects nothing; no geometry
changed).

Definitions: Hotzman et al. 2011, Measurer's Handbook: US Army and Marine Corps Anthropometric Surveys 2010-2011,
NATICK/TR-11/017 (DTIC ADA548497), as SUPPLIED BY THE PROJECT OWNER on 8 October 2026 (section numbers and wording below).
The primary PDF could not be retrieved from this cloud environment (every route denied by the network policy; attempts
recorded), so the definitions are owner-supplied and NOT independently verified here; no PDF hash can be recorded.

For each ANSUR landmark, the audit classifies the closest current model element:
  DEFENSIBLE  - the model element is defined at the same anatomical point (same structure, same extremum) for the axis used
  BRACKETED   - mapped to a model segment with a stated construction; the exact point is bracketed
  UNRESOLVED  - the model element is a different anatomical point; the offset is unsourced here
and reports which arm-chain conclusions survive across an exploratory 0-15 mm offset bracket for each UNRESOLVED endpoint
(the bracket covers the project's existing 15 mm convention; it is not a sourced range).

  ansur_endpoint_correspondence_audit.py --out JSON
"""
import argparse, hashlib, json, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import arm_chain_ansur_audit as arm  # noqa: E402

ROOT = HERE.parents[1]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
A003 = ANAT / 'character_fit_r95_a003.json'
C003 = ANAT / 'audit/candidates/shoulder_thorax_c003_ansur_coupled/candidate_record.json'
SOURCE = {
    'citation': "Hotzman J, Gordon CC, Bradtmiller B, Corner BD, Mucher M, Kristensen S, Paquette S, Blackwell CL. Measurer's Handbook: US Army and Marine Corps Anthropometric Surveys, 2010-2011. NATICK/TR-11/017 (2011).",
    'url': 'https://apps.dtic.mil/sti/tr/pdf/ADA548497.pdf', 'dtic_accession': 'ADA548497',
    'retrieval_attempts_2026_10_08': ['https://apps.dtic.mil/sti/tr/pdf/ADA548497.pdf', 'https://apps.dtic.mil/sti/pdfs/ADA548497.pdf',
                                      'https://archive.org/download/DTIC_ADA548497/DTIC_ADA548497.pdf',
                                      'https://web.archive.org/web/2020/https://apps.dtic.mil/sti/pdfs/ADA548497.pdf'],
    'retrieval_result': 'all denied by the cloud environment network policy (no bytes received)',
    'pdf_sha256': None,
    'definition_status': 'OWNER_SUPPLIED_NOT_INDEPENDENTLY_VERIFIED',
}
DEFS = {
    'acromion': {'section': '5.2.1 (owner-verified earlier)', 'text': 'palpated bony point: intersection of the lateral border of the acromion with the line from the trapezius point over the clavicle point toward the shoulder tip'},
    'cervicale': {'section': '5.2.5', 'text': 'most prominent palpable point of the C7 spinous process'},
    'radiale': {'section': '5.2.33', 'text': 'superior point on the outside (lateral) edge of the radius'},
    'stylion': {'section': '5.2.36', 'text': 'inferior point at the bottom of the radius (radial styloid)'},
    'suprasternale': {'section': '5.2.39', 'text': 'inferior point of the jugular notch'},
    'radiale_stylion_length': {'section': '6.4.68', 'text': 'radiale to stylion measured directly with a beam caliper parallel to the forearm'},
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def r1(x):
    return round(float(x), 1)


def build():
    a, c = json.loads(A003.read_text()), json.loads(C003.read_text())
    A = arm.ansur()
    z = lambda rec, k: float(rec['joint_markers'][k]['centre_m'][2]) * 1000
    rb = a['bones']['radius_left']
    corr = {
        'suprasternale': {'model': 'skeleton_input.trunk.ij_bone (sternum head)', 'axis_used': 'height (z) only',
                          'class': 'DEFENSIBLE', 'reason': 'the model point is the bony jugular-notch point; c003 uses only its height'},
        'acromion': {'model': 'Lee LM25-LM27 lateral-border crossing of the trapezius-clavicle line (c001-c003)', 'class': 'BRACKETED',
                     'reason': 'line construction bracketed (clavicle-axis vs lateral line through AC: 1497.7 vs 1502.2 mm in c003); see shoulder_ansur_acromion_correspondence_v1.json'},
        'cervicale': {'model': 'none (only vertebral body centres exist; C7 body centre z 1579.8 mm)', 'class': 'UNRESOLVED',
                      'reason': 'no C7 spinous-tip landmark; spinous tip lies caudal/posterior of the body centre by an unsourced amount'},
        'radiale': {'model': 'radius head = humeroradial articular centre (a003 radius recipe "Radial head to radial styloid"; head coincides with humeroradial marker)',
                    'class': 'UNRESOLVED', 'reason': 'ANSUR radiale is the superior point of the lateral radial-head rim; the model point is an articular centre; vertical offset unsourced here. The 15 mm radiale-below-EJC rule is a project convention, not a definition'},
        'stylion': {'model': 'radius tail (recipe: radial styloid)', 'class': 'UNRESOLVED',
                    'reason': 'label matches, but the tail sits exactly at the radiocarpal wrist-centre height (a003: %.1f vs %.1f mm), i.e. a placement coincidence; the styloid tip lies distal to the radiocarpal centre by an unsourced amount' % (rb['tail_m'][2] * 1000, z(a, 'radiocarpal_left'))},
        'radiale_stylion_length': {'model': 'no direct model span; radius stick = articular centre to wrist-centre height (a003 256.0 mm)', 'class': 'UNRESOLVED',
                                   'reason': 'both endpoints UNRESOLVED; EJC/WJC substitutes are not used as the measurement'},
    }
    # sensitivity: radiale = humeroradial centre - dr, stylion = radius tail - ds, dr, ds in 0..15 mm
    grid = np.arange(0, 15.1, 5.0)
    zs = lambda v, k: (v - A[k]['mean']) / A[k]['residual_sd']
    sens = {}
    for name, rec in (('a003', a), ('c003', c)):
        acr = arm.acromion_point(name, rec)[0][2]
        hr = z(rec, 'humeroradial_left'); tail = float(rec['bones']['radius_left']['tail_m'][2]) * 1000
        rows = []
        for dr in grid:
            for ds in grid:
                rad, sty = hr - dr, tail - ds
                rows.append({'radiale_offset_mm': float(dr), 'stylion_offset_mm': float(ds),
                             'acromion_radiale_z': round(zs(acr - rad, 'acromion_radiale'), 2),
                             'radiale_stylion_z': round(zs(rad - sty, 'radiale_stylion'), 2),
                             'stylion_height_z': round(zs(sty, 'stylion_height_wristheight'), 2)})
        key = lambda k: [min(r[k] for r in rows), max(r[k] for r in rows)]
        sens[name] = {'acromion_z_mm': r1(acr), 'rows': rows, 'ranges': {k: key(k) for k in ('acromion_radiale_z', 'radiale_stylion_z', 'stylion_height_z')}}
    rc = sens['c003']['ranges']
    robust = {
        'forearm_radiale_stylion_short_on_c003': bool(rc['radiale_stylion_z'][1] < -1),
        'wrist_high_on_c003': bool(rc['stylion_height_z'][0] > 1),
        'upper_arm_drop_short_on_c003': bool(rc['acromion_radiale_z'][1] < -1),
    }
    return {
        'schema_version': 1, 'created': '2026-10-08', 'status': 'AUDIT_ONLY_NO_TARGET_SELECTED_NO_GEOMETRY_CHANGED',
        'source': SOURCE, 'definitions_owner_supplied': DEFS,
        'inputs_sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in (A003, C003, arm.CSV)},
        'correspondence': corr,
        'sensitivity_bracket': 'exploratory 0-15 mm for each UNRESOLVED arm endpoint (covers the existing 15 mm convention; not a sourced range)',
        'sensitivity': sens,
        'robust_across_bracket': robust,
        'decision': {
            'humerus_or_forearm_target': 'NOT SELECTED: radiale and stylion correspondences are unresolved, so no endpoint mapping justifies a length change',
            'c003_geometry': 'unchanged',
            'arm_chain_audit_status': 'its EJC/WJC-proxy z-scores stay labelled as proxies; only the conclusions in robust_across_bracket hold whatever the unsourced offsets are',
        },
        'needed': ['primary handbook PDF (hash and page numbers for 5.2.5, 5.2.33, 5.2.36, 5.2.39, 6.4.68 and the wrist-height landmark)',
                   'radial-head rim to humeroradial articular centre offset (source)', 'radial styloid tip to radiocarpal centre offset (source)',
                   'C7 spinous tip relative to the C7 body (source)'],
    }


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True)
    o = ap.parse_args()
    r = build()
    Path(o.out).write_text(json.dumps(r, indent=1) + '\n')
    print(json.dumps({'classes': {k: v['class'] for k, v in r['correspondence'].items()}, 'ranges': {k: v['ranges'] for k, v in r['sensitivity'].items()},
                      'robust': r['robust_across_bracket']}, indent=1))


if __name__ == '__main__':
    main()
