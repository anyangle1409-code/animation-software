#!/usr/bin/env python3
"""Validate development-only real-human evidence for ORIGINAL-v1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / 'ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json'

REQUIRED_VISUAL_PRIMITIVES = (
    'shoulder_flexion',
    'shoulder_abduction',
    'shoulder_axial_rotation',
)
VISUAL_SOURCE_TYPES = {'photo_series', 'figure_series', 'supplementary_video', 'clinical_video'}
SOURCE_TYPES = VISUAL_SOURCE_TYPES | {'primary_study', 'anatomy_article', 'normative_dataset'}
PERMITTED_CONCLUSIONS = {
    # Geometry / appearance observations
    'bone_motion',
    'surface_contour',
    'fold_boundaries',
    'volume_continuity',
    'inter_subject_variation',
    'movement_timing',
    # Joint and coordination observations
    'joint_kinematics',
    'joint_coupling',
    'interjoint_coordination',
    'center_of_mass_relationship',
    'symmetry',
    # Hand / wrist observations
    'finger_joint_flexion',
    'diameter_dependent_grip_posture',
    'thumb_opposition',
    'relative_digit_motion',
    'movement_smoothness',
    'force_transmission',
    'load_path',
    'wrist_alignment',
    'extension_loading',
    'contact_shift',
    # Tendon / soft-tissue mechanics observations
    'tendon_behavior',
    'attachment_relationship',
    'multi_joint_tissue_behavior',
    'tendon_path_continuity',
    'surface_load_transfer',
}
REVIEW_STATES = {'verified', 'needs_review', 'rejected'}
REQUIRED_FIELDS = (
    'id', 'region', 'movement_primitive', 'source_type', 'source',
    'movement_phase', 'view', 'diversity', 'observable_landmarks',
    'permissible_conclusions', 'uncertainty', 'development_only',
    'review_status',
)


def _nonempty_strings(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(x, str) and x.strip() for x in value)


def validate_manifest(path_or_manifest: Path | dict[str, Any]) -> list[str]:
    if isinstance(path_or_manifest, Path):
        manifest = json.loads(path_or_manifest.read_text(encoding='utf-8-sig'))
    else:
        manifest = path_or_manifest
    errors: list[str] = []
    if manifest.get('schema_version') != 1:
        errors.append('schema_version must be 1')
    if manifest.get('asset') != 'HomeGymPT_Male_ORIGINAL_v1':
        errors.append('asset identity mismatch')
    entries = manifest.get('entries')
    if not isinstance(entries, list) or not entries:
        return errors + ['entries must be a non-empty list']

    seen: set[str] = set()
    visual_primitives: set[str] = set()
    for index, row in enumerate(entries):
        label = str(row.get('id') or f'entry[{index}]') if isinstance(row, dict) else f'entry[{index}]'
        if not isinstance(row, dict):
            errors.append(label+': entry must be an object')
            continue
        for field in REQUIRED_FIELDS:
            if field not in row:
                errors.append(label+': missing '+field)
        evidence_id = row.get('id')
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            errors.append(label+': id must be non-empty')
        elif evidence_id in seen:
            errors.append(label+': duplicate evidence id')
        else:
            seen.add(evidence_id)
        for field in ('region', 'movement_primitive', 'movement_phase', 'uncertainty'):
            if not isinstance(row.get(field), str) or not row.get(field, '').strip():
                errors.append(label+': '+field+' must be non-empty')
        source_type = row.get('source_type')
        if source_type not in SOURCE_TYPES:
            errors.append(label+': unsupported source_type')
        source = row.get('source')
        if not isinstance(source, dict):
            errors.append(label+': source must be an object')
        else:
            if not any(isinstance(source.get(key), str) and source[key].strip() for key in ('url', 'capture_id')):
                errors.append(label+': source requires URL or capture_id')
            if not isinstance(source.get('license_use_note'), str) or not source['license_use_note'].strip():
                errors.append(label+': source.license_use_note must be non-empty')
            if not isinstance(source.get('citation'), str) or not source['citation'].strip():
                errors.append(label+': source.citation must be non-empty')
        diversity = row.get('diversity')
        if not isinstance(diversity, dict) or not isinstance(diversity.get('notes'), str) or not diversity.get('notes', '').strip():
            errors.append(label+': diversity.notes must be non-empty')
        if not _nonempty_strings(row.get('view')):
            errors.append(label+': view must be a non-empty string list')
        if not _nonempty_strings(row.get('observable_landmarks')):
            errors.append(label+': observable_landmarks must be a non-empty string list')
        conclusions = row.get('permissible_conclusions')
        if not _nonempty_strings(conclusions):
            errors.append(label+': permissible_conclusions must be a non-empty string list')
        else:
            for conclusion in conclusions:
                if conclusion not in PERMITTED_CONCLUSIONS:
                    errors.append(label+': unsupported permissible conclusion '+conclusion)
        if row.get('development_only') is not True:
            errors.append(label+': development_only must be true')
        if row.get('review_status') not in REVIEW_STATES:
            errors.append(label+': invalid review_status')
        if source_type in VISUAL_SOURCE_TYPES and row.get('review_status') == 'verified':
            visual_primitives.add(row.get('movement_primitive'))

    for primitive in REQUIRED_VISUAL_PRIMITIVES:
        if primitive not in visual_primitives:
            errors.append('no visual source for required movement primitive '+primitive)
    return errors


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('manifest', type=Path, nargs='?', default=DEFAULT_MANIFEST)
    args=parser.parse_args()
    try:
        errors=validate_manifest(args.manifest)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print('HUMAN EVIDENCE INVALID: '+str(exc))
        return 2
    if errors:
        print('HUMAN EVIDENCE INVALID')
        for error in errors: print('- '+error)
        return 1
    print('HUMAN EVIDENCE VERIFIED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
