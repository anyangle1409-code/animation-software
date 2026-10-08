"""Measured scapula landmarks: source-bound, rigidly aligned, never mesh-fitted.

Reads the published Lee/Lawrence/Rainbow workbook with the standard library.
The workbook incorrectly declares A1-only sheet dimensions; actual cells and
subject IDs, not those dimensions or row order, determine coverage.

The output is a provisional relative envelope. No SC/AC/GH centre, neutral
thorax-relative orientation, or production bone geometry is invented.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / 'ORIGINAL_V1_WORK/anatomy/sources/scapula_lee2024/SubjectDemographicsAndLandmarks.xlsx'
DEFAULT_REPORT = ROOT / 'ORIGINAL_V1_WORK/anatomy/canonical_scapula_measured_landmark_model_v1.json'
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
DISTANCES = {
    'superior_inferior_angles': (3, 7),
    'medial_spine_to_exterior_acromion': (5, 25),
    'medial_spine_to_interior_acromion': (5, 26),
    'medial_spine_to_lateral_distal_acromion': (5, 27),
    'medial_spine_to_glenoid_shallowest_point': (5, 19),
    'glenoid_superior_inferior_rim': (15, 18),
    'glenoid_anterior_posterior_rim': (16, 17),
    'exterior_acromion_to_inferior_angle': (25, 7),
    'medial_spine_to_inferior_angle': (5, 7),
    'exterior_acromion_to_glenoid_shallowest_point': (25, 19),
}


def _sheet_rows(z, path, strings):
    rows = []
    for row in ET.fromstring(z.read(path)).findall(f'{NS}sheetData/{NS}row'):
        values = {}
        for cell in row.findall(NS + 'c'):
            letters = re.match(r'[A-Z]+', cell.attrib['r'])[0]
            col = 0
            for char in letters:
                col = col * 26 + ord(char) - ord('A') + 1
            v = cell.find(NS + 'v')
            value = None if v is None else v.text
            if cell.attrib.get('t') == 's':
                value = strings[int(value)]
            elif cell.attrib.get('t') == 'inlineStr':
                value = ''.join(cell.itertext())
            elif value is not None and cell.attrib.get('t', 'n') == 'n':
                value = float(value)
            values[col - 1] = value
        if values:
            rows.append([values.get(i) for i in range(max(values) + 1)])
    return rows


def load_subjects(path=DEFAULT_SOURCE):
    with zipfile.ZipFile(path) as z:
        strings = [''.join(si.itertext()) for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        workbook = ET.fromstring(z.read('xl/workbook.xml'))
        rels = {r.attrib['Id']: r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        sheets = {}
        rid = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
        for sheet in workbook.find(NS + 'sheets'):
            target = rels[sheet.attrib[rid]]
            if target.startswith('/'):
                target = target.lstrip('/')
            else:
                target = 'xl/' + target
            sheets[sheet.attrib['name']] = _sheet_rows(z, target, strings)
    return join_subjects(sheets['SubjectInfo'], sheets['Landmarks'])


def join_subjects(info, landmarks):
    if info[0] != ['ID', 'Sym', 'FTT', 'Age', 'Sex', 'Height']:
        raise ValueError('unexpected demographic header')
    if landmarks[0][1:] != [f'pts.{i}' for i in range(1, 88)]:
        raise ValueError('unexpected landmark coordinate ordering')
    def indexed(rows):
        out = {}
        for row in rows[1:]:
            if not row[0] or row[0] in out:
                raise ValueError('missing or duplicate subject ID')
            out[row[0]] = row
        return out
    persons, points = indexed(info), indexed(landmarks)
    if set(persons) != set(points):
        raise ValueError('landmark/demographic subject IDs do not match')
    result = []
    for sid, row in persons.items():
        p = np.asarray(points[sid][1:], dtype=float)
        if p.shape != (87,) or not np.isfinite(p).all():
            raise ValueError(f'{sid}: require 29 finite XYZ landmarks')
        if row[4] not in ('Male', 'Female'):
            raise ValueError('unrecognized source sex label')
        h = row[5]
        if isinstance(h, (int, float)):
            if not math.isfinite(h) or not 100 < h < 250:
                raise ValueError('height must be finite centimetres')
        elif h in (None, '#N/A'):
            h = None
        else:
            raise ValueError('unrecognized missing height marker')
        result.append({'id': sid, 'sex': row[4], 'height_cm': h,
                       'age_years': row[3], 'symptoms': row[1], 'FTT': row[2],
                       'points_mm': p.reshape(29, 3).tolist()})
    return result


def anatomical_local(points_mm):
    """Right-scapula basis: x anterior, y superior, z toward exterior acromion.

    LM25 is the origin; LM5→LM25 defines z. LM7 defines the blade plane.
    LM17 vs LM16 independently checks anterior sign. LM14 ('root of spine')
    is a separate lateral landmark and must not replace medial LM5.
    """
    p = np.asarray(points_mm, dtype=float)
    if p.shape != (29, 3) or not np.isfinite(p).all():
        raise ValueError('require 29 finite XYZ points')
    def unit(v):
        length = np.linalg.norm(v)
        if length < 1e-8:
            raise ValueError('degenerate scapular landmark plane')
        return v / length
    z = unit(p[24] - p[4])
    x = unit(np.cross(z, p[6] - p[4]))
    y = unit(np.cross(z, x))
    frame = np.column_stack((x, y, z))
    local = (p - p[24]) @ frame
    if local[16, 0] <= local[15, 0] or local[6, 1] >= 0:
        raise ValueError('source chirality/anterior direction does not match right template')
    return local, frame


def regression(heights_cm, values, target_cm):
    x, y = np.asarray(heights_cm, float), np.asarray(values, float)
    if (x.ndim != 1 or y.shape[0] != len(x) or len(x) < 3
            or not np.isfinite(x).all() or not np.isfinite(y).all()
            or not math.isfinite(target_cm) or np.ptp(x) <= 1e-8):
        raise ValueError('regression requires finite paired data and varying stature')
    if not x.min() <= target_cm <= x.max():
        raise ValueError('target would require stature extrapolation')
    X = np.column_stack((np.ones(len(x)), x - x.mean()))
    coefficients = np.linalg.lstsq(X, y, rcond=None)[0]
    predicted = coefficients[0] + (target_cm - x.mean()) * coefficients[1]
    residual = y - X @ coefficients
    sd = np.sqrt(np.sum(residual**2, axis=0) / (len(x) - 2))
    return {'n': len(x), 'height_range_cm': [float(x.min()), float(x.max())],
            'predicted': np.asarray(predicted).tolist(), 'residual_sd': np.asarray(sd).tolist(),
            'slope_per_cm': np.asarray(coefficients[1]).tolist(),
            'method': 'direct OLS measurement-on-stature; not inverted stature-on-bone equation'}


def build_report(subjects, *, target_height_cm):
    groups = {
        'all_males': [s for s in subjects if s['sex'] == 'Male'],
        'asymptomatic_no_FTT_males': [s for s in subjects if s['sex'] == 'Male'
                                     and s['symptoms'] == 'Asym' and s['FTT'] == 'no'],
    }
    reports = {}
    for name, group in groups.items():
        distances = {}
        known = [s for s in group if s['height_cm'] is not None]
        for label, (a, b) in DISTANCES.items():
            values = np.array([np.linalg.norm(np.asarray(s['points_mm'])[a-1]
                                             - np.asarray(s['points_mm'])[b-1]) for s in group])
            entry = {'landmark_pair_1based': [a, b], 'n': len(group),
                     'mean': float(values.mean()), 'sd': float(values.std(ddof=1)),
                     'range': [float(values.min()), float(values.max())]}
            if len(known) >= 3:
                entry['direct_stature_regression'] = regression(
                    [s['height_cm'] for s in known],
                    [np.linalg.norm(np.asarray(s['points_mm'])[a-1] - np.asarray(s['points_mm'])[b-1]) for s in known],
                    target_height_cm)
            distances[label] = entry
        local = np.array([anatomical_local(s['points_mm'])[0] for s in group])
        reports[name] = {'n': len(group), 'n_with_stature': len(known),
                         'distances_mm': distances,
                         'mean_local_landmarks_mm': local.mean(axis=0).tolist(),
                         'sd_local_landmarks_mm': local.std(axis=0, ddof=1).tolist()}
        if len(known) >= 3:
            reports[name]['stature_conditioned_local_landmarks'] = regression(
                [s['height_cm'] for s in known],
                np.array([anatomical_local(s['points_mm'])[0] for s in known]).reshape(len(known), 87),
                target_height_cm)
    local = np.asarray(reports['asymptomatic_no_FTT_males']['stature_conditioned_local_landmarks']['predicted']).reshape(29, 3)
    # A proper rotation maps the right local basis to HGPT. Anatomical left
    # points reflect world X afterwards; that reflection is NOT a pose rotation.
    R = np.array([[0, 0, -1], [-1, 0, 0], [0, 1, 0]], dtype=float)
    right = local @ R.T
    left = right * [-1, 1, 1]
    return {'schema_version': 1, 'source': 'LEE_2024_SCAPULA_RAW_3D',
            'status': 'PROVISIONAL_MEASURED_RELATIVE_ENVELOPE_NOT_GLOBAL_TARGET',
            'freeze_ready': False, 'target_height_cm': target_height_cm,
            'groups': reports,
            'frame_definition': {'origin': 'LM25 exterior acromial angle',
                'medial_spine_point': 'LM5 intersection of spine with vertebral border',
                'inferior_angle': 'LM7', 'independent_anterior_sign': 'LM17 anterior rim minus LM16 posterior rim',
                'local_axes': ['anterior', 'superior', 'lateral (right scapula)'],
                'note': 'LM14 root of spine is not medial-border LM5. LM25 exterior and LM26 interior acromial angles are separate.'},
            'relative_HGPT_landmarks_mm': {'right': right.tolist(), 'left': left.tolist(),
                'pose': 'basis-aligned shape only; neutral standing rotations and absolute thorax translation unapplied',
                'left_policy': 'reflect point geometry in world X, never use improper reflection as a pose rotation'},
            'unmeasured_joint_centres': {'SC': None, 'AC': None, 'GH': None},
            'limitations': ['No subject bone mesh is imported.',
                'These sparse landmarks do not recover a complete bone surface, joint cartilage or humeral-head sphere.',
                'The healthy male subgroup is small; provisional predictions require independent endpoint-matched evidence.',
                'Do not identify a glenoid rim midpoint/shallowest point with GH sphere centre.',
                'Coordinatewise OLS shape predictions and distance OLS predictions differ; retain both, never force equality.']}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    ap.add_argument('--height-cm', type=float, required=True)
    ap.add_argument('--out', type=Path, default=DEFAULT_REPORT)
    args = ap.parse_args()
    report = build_report(load_subjects(args.source), target_height_cm=args.height_cm)
    report['source_sha256'] = hashlib.sha256(args.source.read_bytes()).hexdigest()
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': report['status'], 'groups': {k: {'n': v['n'], 'with_stature': v['n_with_stature']} for k,v in report['groups'].items()}}))


if __name__ == '__main__':
    main()
