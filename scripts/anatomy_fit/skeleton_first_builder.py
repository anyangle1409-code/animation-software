#!/usr/bin/env python3
"""Explicit-coordinate skeletal construction, independent of all skin geometry.

This module never selects anatomical targets or grants canonical acceptance.
The legacy replay adapter is a historical reproduction, not a target builder.
Evidence claims are validation inputs; their metadata cannot prove anatomy.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

import cp2_preflight as cp2

BASIS = 'HGPT_LEFT_PLUS_X_POSTERIOR_PLUS_Y_SUPERIOR_PLUS_Z'
ANAT = Path(__file__).resolve().parents[2] / 'ORIGINAL_V1_WORK/anatomy'


def replay_contract(record, label):
    """Copy explicit skeletal data; do not consume surface skeleton_input."""
    return {'schema_version': 1, 'units': 'm', 'world_basis': BASIS,
            'coordinate_origin': 'legacy_audit_replay', 'label': label,
            'target_profile': {'sex': 'male', 'stature_m': 1.82, 'age_class': 'adult'},
            'record': {k: copy.deepcopy(record[k]) for k in ('bones', 'joint_markers')},
            'evidence_claims': {}, 'sources': {}, 'length_constraints': [], 'joint_constraints': []}


def _number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _vec(x):
    return isinstance(x, list) and len(x) == 3 and all(_number(n) for n in x)


def _evidence(contract, record):
    """Check completeness of source-bound claims, not their scientific truth."""
    required = [f'bone:{bid}:{end}' for bid in record['bones'] for end in ('head_m', 'tail_m', 'axis')]
    required += [f'joint:{jid}:{item}' for jid in record['joint_markers'] for item in ('centre_m', 'frame')]
    sources, claims = contract.get('sources', {}), contract.get('evidence_claims', {})
    unresolved = []
    for key in required:
        claim = claims.get(key, {})
        ids = claim.get('source_ids', [])
        independent = set()
        valid = (claim.get('review_status') == 'independently_reviewed' and
                 all(isinstance(claim.get(k), str) and claim[k].strip() for k in
                     ('measurement_definition', 'coordinate_derivation', 'review_record')) and
                 isinstance(ids, list) and bool(ids))
        for sid in ids if isinstance(ids, list) else []:
            src = sources.get(sid, {})
            if src.get('kind') not in ('primary_anatomy', 'primary_biomechanics', 'anthropometric_dataset'):
                valid = False
            if not all(isinstance(src.get(k), str) and src[k].strip() for k in
                       ('url', 'locator', 'independent_work_id')):
                valid = False
            independent.add(src.get('independent_work_id'))
        if not valid or len(independent - {None}) < 2:
            unresolved.append(key)
    # Replay always remains legacy even if someone attaches claim metadata.
    return {'required_claims': len(required), 'unresolved': unresolved,
            'claims_complete': not unresolved and contract['coordinate_origin'] == 'independent_anatomy',
            'source_truth_verified_by_code': False}


def _constraints(contract, record, articulations, additional):
    bones, joints = record['bones'], record['joint_markers']
    participants = {a['id']: {additional.get(p, {}).get('owner_bone', p)
                             for p in a['participants']} for a in articulations}
    failures, lengths, gaps = [], {}, {}
    for index, c in enumerate(contract.get('length_constraints', [])):
        name, band = c.get('bone'), c.get('range_mm')
        if (name not in bones or not isinstance(band, list) or len(band) != 2 or
                not all(_number(x) for x in band) or not 0 < band[0] <= band[1] or
                not c.get('measurement_definition') or not c.get('source_ids')):
            raise ValueError(f'invalid length constraint {index}')
        value = math.dist(bones[name]['head_m'], bones[name]['tail_m']) * 1000
        lengths[f'{index}:{name}'] = value
        if not band[0] <= value <= band[1]:
            failures.append(f'{name}: {value:.6f} mm outside endpoint-defined {band}')
    for index, c in enumerate(contract.get('joint_constraints', [])):
        jid, tol, refs = c.get('joint'), c.get('tolerance_m'), c.get('endpoints')
        if (jid not in joints or not _number(tol) or tol < 0 or not c.get('basis') or
                not isinstance(refs, list) or not refs):
            raise ValueError(f'invalid joint constraint {index}')
        centre = joints[jid]['centre_m']
        for ref in refs:
            if (not isinstance(ref, list) or len(ref) != 2 or ref[0] not in bones or
                    ref[1] not in ('head_m', 'tail_m')):
                raise ValueError(f'invalid endpoint constraint {index}')
            if ref[0] not in participants.get(jid, set()):
                raise ValueError(f'{jid}: endpoint constraint bone {ref[0]} is not a joint participant')
            gap = math.dist(bones[ref[0]][ref[1]], centre)
            gaps[f'{index}:{ref[0]}:{ref[1]}'] = gap * 1000
            if gap > tol:
                failures.append(f'{jid}: {ref} detached by {gap * 1000:.6f} mm')
    return {'status': 'FAIL' if failures else 'PASS' if lengths or gaps else 'UNVERIFIED',
            'failures': failures, 'lengths_mm': lengths, 'endpoint_to_joint_gaps_mm': gaps,
            'coverage_complete': False}  # full envelope/contact coverage is a separate gate


def construct(contract, strict=False):
    """Return isolated data and failures. Never repair coordinates to pass checks.

Strict mode rejects any CP2 failure, unverified geometry, missing evidence or
incomplete constraint coverage. Diagnostic mode preserves data to expose gaps.
"""
    if contract.get('schema_version') != 1:
        raise ValueError('unsupported schema_version')
    if contract.get('units') != 'm':
        raise ValueError('units must be m')
    if contract.get('world_basis') != BASIS:
        raise ValueError('world_basis must use the HGPT anatomical basis')
    if contract.get('coordinate_origin') not in ('independent_anatomy', 'legacy_audit_replay'):
        raise ValueError('coordinate_origin cannot be mesh fit or skin containment')
    profile = contract.get('target_profile', {})
    if (profile.get('sex') not in ('male', 'female') or profile.get('age_class') != 'adult' or
            not _number(profile.get('stature_m')) or profile['stature_m'] <= 0):
        raise ValueError('target_profile requires explicit adult sex and positive stature')
    record = copy.deepcopy(contract['record'])
    if not isinstance(record.get('bones'), dict) or not isinstance(record.get('joint_markers'), dict):
        raise ValueError('record requires explicit bones and joint_markers')
    for name, bone in record['bones'].items():
        if not all(_vec(bone.get(end)) for end in ('head_m', 'tail_m')):
            raise ValueError(f'{name}: coordinates must be finite 3-vectors')
        if math.dist(bone['head_m'], bone['tail_m']) == 0:
            raise ValueError(f'{name}: zero-length bone')
    for name, marker in record['joint_markers'].items():
        if not _vec(marker.get('centre_m')):
            raise ValueError(f'{name}: centre must be finite')
        frame = marker.get('frame_axes_columns_XYZ')
        if not isinstance(frame, list) or len(frame) != 3 or not all(_vec(row) for row in frame):
            raise ValueError(f'{name}: expected finite frame 3x3')
    reference = cp2.load_reference()
    validation = cp2.check_candidate(record, *reference)
    constraints = _constraints(contract, record, reference[1], reference[2])
    evidence = _evidence(contract, record)
    axes = contract.get('anatomical_axes', {})
    missing_axes = []
    for name in record['bones']:
        axis = axes.get(name)
        if axis is None:
            missing_axes.append(name)
        elif not _vec(axis) or abs(math.hypot(*axis) - 1) > 1e-6:
            raise ValueError(f'{name}: anatomical axis must be a finite unit vector')
    if strict and (validation['verdict'] != 'STRUCTURE_PASS_EVIDENCE_REVIEW_STILL_REQUIRED' or
                   constraints['status'] != 'PASS' or not constraints['coverage_complete'] or
                   not evidence['claims_complete'] or missing_axes):
        raise ValueError('skeleton not validated: geometry/evidence/coverage incomplete')
    return {'schema_version': 1, 'kind': 'EXPLICIT_COORDINATE_CONSTRUCTION_DIAGNOSTIC',
            'coordinate_origin': contract['coordinate_origin'], 'target_profile': copy.deepcopy(profile),
            'record': record, 'validation': validation, 'constraints': constraints,
            'evidence': evidence, 'missing_anatomical_axes': missing_axes,
            'promotion_allowed': False, 'anatomical_acceptance': False}


def skin_diagnostic(record, clearance):
    """Read-only signed skin distances. No skeleton or callback relocation path."""
    snapshot = copy.deepcopy(record)
    rows = []
    for name, bone in snapshot['bones'].items():
        for end in ('head_m', 'tail_m'):
            if not _vec(bone[end]):
                raise ValueError('skin diagnostic requires finite skeletal points')
            distance = clearance(tuple(bone[end]))
            if not _number(distance):
                raise ValueError('expected finite clearance in metres')
            rows.append({'bone': name, 'endpoint': end, 'clearance_m': distance})
    return {'kind': 'SKIN_DIAGNOSTIC_ONLY', 'points': len(rows),
            'outside': sum(x['clearance_m'] < 0 for x in rows),
            'skeleton_relocation_allowed': False, 'details': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay-record', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    source = args.replay_record.read_bytes()
    report = construct(replay_contract(json.loads(source), args.label))
    report['input_sha256'] = hashlib.sha256(source).hexdigest()
    data = json.dumps(report, indent=2, allow_nan=False) + '\n'
    with args.out.open('x') as f:
        f.write(data)
    print({'validation': report['validation']['verdict'], 'anatomical_acceptance': False,
           'missing_evidence_claims': len(report['evidence']['unresolved'])})


if __name__ == '__main__':
    main()
