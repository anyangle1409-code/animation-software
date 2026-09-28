"""Fail closed when an O1 modelling source differs from its clean-room record."""
import re


def validate_o1_source(record, actual_blend_sha256):
    errors = []
    if record.get('asset_id') != 'HomeGymPT_Male_ORIGINAL_v1':
        errors.append('asset identity')
    if record.get('source_branch') != 'work/standalone-first-party-audit-20260927':
        errors.append('source branch')
    if record.get('clean_room') is not True or record.get('starting_geometry') != 'blank':
        errors.append('blank clean-room origin')
    if record.get('legacy_geometry_imported') is not False:
        errors.append('legacy geometry import')
    expected = record.get('blend_sha256')
    if not isinstance(expected, str) or not re.fullmatch(r'[0-9a-f]{64}', expected):
        errors.append('recorded blend hash')
    elif actual_blend_sha256 != expected:
        errors.append('blend hash mismatch')
    scaffold = record.get('scaffold') or {}
    for key, expected_count in (('vertex_count', 3890), ('triangle_count', 7280), ('bone_count', 53)):
        if scaffold.get(key) != expected_count:
            errors.append(f'O1 {key}')
    if scaffold.get('third_party_geometry_imported') is not False:
        errors.append('third-party geometry import')
    if scaffold.get('legacy_projection_used') is not False:
        errors.append('legacy projection')
    return errors
