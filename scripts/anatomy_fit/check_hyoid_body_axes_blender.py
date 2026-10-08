"""Check corrected body dimension labels in bpy; not a hyoid shape or pose."""
import argparse
import hashlib
import json
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scratch-blend', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.scratch_blend.exists() or args.out.exists():
        raise FileExistsError('Fresh immutable output paths required')
    source = ROOT / 'ORIGINAL_V1_WORK/anatomy/canonical_hyoid_geometry_targets_v1.json'
    data = json.loads(source.read_text())
    dims = data['provisional_local_geometry']['direct_2025_male_nominals_mm']
    # Independent Table 1/Figure 1 mapping, not iteration over stored axis labels.
    expected = {'X': ('AA_prime', 'body_width', 24.3),
                'Y': ('CC_prime', 'body_AP_thickness', 6.99),
                'Z': ('BB_prime', 'body_SI_height', 11.32)}
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for index, (axis, (label, key, value)) in enumerate(expected.items()):
        assert dims[key] == value
        for sign in (-1, 1):
            marker = bpy.data.objects.new(f'DIMENSION_ONLY_{axis}_{sign}', None)
            bpy.context.collection.objects.link(marker)
            marker.location[index] = sign * value / 2000
            marker['source_label'] = label
            marker['not_anatomical_landmark'] = True
    bpy.ops.wm.save_as_mainfile(filepath=str(args.scratch_blend))
    bpy.ops.wm.open_mainfile(filepath=str(args.scratch_blend))
    spans = {}
    for index, (axis, (label, key, value)) in enumerate(expected.items()):
        pair = [bpy.data.objects[f'DIMENSION_ONLY_{axis}_{s}'] for s in (-1, 1)]
        for marker in pair:
            assert marker['source_label'] == label and marker['not_anatomical_landmark']
            assert all(abs(marker.location[j]) < 1e-12 for j in range(3) if j != index)
        spans[axis] = (pair[1].location - pair[0].location).length * 1000
        assert abs(spans[axis] - value) < 1e-5
    report = {
        'status': 'VERIFIED_DIMENSION_AXIS_FIXTURE_ONLY',
        'blender_version': bpy.app.version_string,
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'fixture_sha256': hashlib.sha256(args.scratch_blend.read_bytes()).hexdigest(),
        'body_extent_spans_mm': spans,
        'marker_count': 6,
        'max_span_error_mm': max(abs(spans[k] - v[2]) for k, v in expected.items()),
        'whole_hyoid_geometry_created': False,
        'neutral_body_tilt_defined': False,
        'absolute_C3_position_defined': False,
        'canonical_candidate_created': False,
        'completed_gates': [],
    }
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
