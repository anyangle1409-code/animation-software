"""Read-only source; reuse pinned 13 movement paths, 9 frames and original metrics.

python native_benchmarks_blender.py -- source.blend r57src NEW_REPORT.json
Run paths independently so one failing movement cannot hide the others.
No mesh saving, new activation rule, skeletal edit or threshold relaxation.
"""
import hashlib
import json
from pathlib import Path
import sys
import traceback

import bpy
from recovery_summary import summarize, verified_remesh_count

NAMES = ['squat', 'bent_over_row', 'shoulder_press', 'lunge', 'walk_stride', 'trunk_rotation',
         'grip', 'single_leg_stance', 'calf_raise', 'deadlift', 'push_up', 'forearm_rotation', 'wrist_circuit']


def sha(path):
    return hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    source, root, output = map(Path, args[:3])
    verification = Path(args[3]) if len(args) > 3 and args[3] != 'none' else None
    source, root, output = source.resolve(), root.resolve(), output.resolve()
    if output.exists() or source == output:
        raise ValueError('Output must be new and separate')
    before = sha(source)
    sys.path[:0] = [str(root / 'scripts'), str(root / 'scripts/anatomy_fit')]
    import build_original_review_candidate_r17_blender as r17
    import original_v1_press_extension as px
    import build_original_movement_benchmarks_blender as bench
    import build_functional_shoulder_correction_blender as correction
    import original_v1_review_candidate_drives as drives
    report = {'source_sha256': before, 'blender': bpy.app.version_string, 'benchmarks': {}, 'errors': {}, 'approved': False}
    original_builder = correction.build_corrected_scene
    try:
        for name in NAMES:
            try:
                correction.build_corrected_scene = original_builder
                bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
                body = bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
                if verification is not None:
                    declared = bpy.context.scene.get('hgpt_review_body_vertices')
                    count = verified_remesh_count(json.loads(verification.read_text()), before, len(body.data.vertices))
                    bpy.context.scene['hgpt_review_body_vertices'] = count
                    report['transient_remesh_declaration'] = {'saved_count': declared, 'verified_count': count,
                                                              'scope': 'memory only, source not saved'}
                elif before != '4c44b1fe14aeefd9a976f45baada60b4b81aaaa7cd736a300ca7cede2b0aaf2e':
                    raise ValueError('Only pinned R41 can run without a reconstruction verification report')
                result = original_builder()
                for key in result['body'].data.shape_keys.key_blocks[1:]: key.value = 0.0
                drives.setup(result)
                px.install()
                if 'hgpt_cap_fraction_ramp' in result['runtime'] or px._PATH['name'] != 'v4':
                    raise RuntimeError('Rejected cap ramp or unexpected press path')
                bench._reset(result['runtime'])
                correction.build_corrected_scene = lambda: result
                outcome = bench.run(only=[name], post_pose=lambda r: drives.drive(r['runtime'], r['body']))
                report['benchmarks'][name] = outcome['benchmarks'][name]
                print('NATIVE_PATH_DONE', name, flush=True)
            except Exception:
                report['errors'][name] = traceback.format_exc()
                print('NATIVE_PATH_FAILED', name, report['errors'][name], flush=True)
            report['summary'] = summarize(report['benchmarks'], NAMES, bench.FRAMES)
            report['source_unchanged'] = sha(source) == before
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2, default=str) + '\n')
    finally:
        correction.build_corrected_scene = original_builder
    if not report['summary']['complete'] or not report['source_unchanged']:
        raise SystemExit(1)
    # Diagnostic execution success is separate from quality_pass; downstream gates read both.


if __name__ == '__main__':
    main()
