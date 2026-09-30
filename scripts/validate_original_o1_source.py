"""Fail closed when an O1 modelling source differs from its clean-room record."""
import re


PINNED_PROFILE_COMMIT = 'e6ef05b4312a1928cc6fbb71b92a94ceaff1cc62'
PINNED_PROFILE_BLOB_SHA = 'ee56a49bfb2e32530520fd1811ed9427460256bd'
PINNED_MESH_ALGORITHM_BLOB_SHA = '0216035a6574a0b753f8716f49e603967923f68f'
PINNED_CLEAN_RIG_COMMIT = '287f72c6a6ac9b1dcd771946ef548d77a40b8ea1'
PINNED_CLEAN_RIG_BLOB_SHA = '5c0182ae6db57e8de99547aa96d80216105a36ba'


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

    pinned = (
        ('profile_commit', PINNED_PROFILE_COMMIT, 'profile commit'),
        ('profile_blob_sha', PINNED_PROFILE_BLOB_SHA, 'profile blob'),
        ('historical_mesh_algorithm_blob_sha', PINNED_MESH_ALGORITHM_BLOB_SHA, 'mesh algorithm blob'),
        ('historical_clean_rig_commit', PINNED_CLEAN_RIG_COMMIT, 'clean rig commit'),
        ('historical_clean_rig_blob_sha', PINNED_CLEAN_RIG_BLOB_SHA, 'clean rig blob'),
    )
    for key, expected_value, label in pinned:
        if scaffold.get(key) != expected_value:
            errors.append(label)

    return errors
