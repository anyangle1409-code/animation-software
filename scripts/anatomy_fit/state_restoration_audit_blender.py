#!/usr/bin/env python3
"""Scene / frame / state restoration audit of the Phase 9 isolated runner (bpy). The runner itself is NOT modified.

Drives run_isolated_tests_blender.main() on a source blend under four scenarios and records what is left behind:
  normal                      - full run
  fail_mid_measure            - RuntimeError raised by isolated_tests.measure on its 200th call
  interrupt_mid_measure       - KeyboardInterrupt raised by isolated_tests.measure on its 200th call
  fail_during_authoring       - RuntimeError raised by the runner's author() before anything is saved
For each: source-file sha256 before/after; whether the test blend / report / samples exist; the saved test blend hash
against the authored hash; the live session's frame/subframe against the value at measurement start; and full state
snapshots (frame, subframe, active object, selection, object mode, scene frame range and fps, armature pose bases,
constraint and driver settings on every object) of (a) the source re-opened after the run against before, and (b) the
saved test blend re-opened against the source (only keyframe animation may differ).

  python3.13 state_restoration_audit_blender.py --source-blend B --record R --work-dir SCRATCH --out JSON
"""
import argparse, hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpy  # noqa: E402

FAIL_AT = 200


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def snapshot():
    sc = bpy.context.scene; vl = bpy.context.view_layer
    arm = bpy.data.objects.get('HGPT_ANATOMICAL_MASTER')
    cons, drv = {}, {}
    for ob in bpy.data.objects:
        for c in ob.constraints:
            cons[f'{ob.name}/{c.name}'] = [c.type, bool(c.mute), round(float(getattr(c, 'influence', 1.0)), 9)]
        if ob.type == 'ARMATURE':
            for pb in ob.pose.bones:
                for c in pb.constraints:
                    cons[f'{ob.name}/{pb.name}/{c.name}'] = [c.type, bool(c.mute), round(float(c.influence), 9)]
        ad = ob.animation_data
        if ad:
            for d in ad.drivers:
                drv[f'{ob.name}/{d.data_path}[{d.array_index}]'] = [bool(d.mute), d.driver.expression]
    pose = {}
    if arm is not None:
        for pb in arm.pose.bones:
            pose[pb.name] = [round(x, 6) + 0.0 for row in pb.matrix_basis for x in row]   # +0.0 folds -0.0 into 0.0
    return {'frame': sc.frame_current, 'subframe': round(sc.frame_subframe, 6), 'frame_range': [sc.frame_start, sc.frame_end],
            'fps': [sc.render.fps, round(sc.render.fps_base, 6)],
            'active_object': vl.objects.active.name if vl.objects.active else None,
            'selected': sorted(o.name for o in bpy.data.objects if o.select_get()),
            'mode': bpy.context.mode, 'constraints': cons, 'drivers': drv, 'pose_bases_digest': hashlib.sha256(json.dumps(pose, sort_keys=True).encode()).hexdigest(),
            'armature_has_action': bool(arm and arm.animation_data and arm.animation_data.action)}


def diff(a, b, ignore=()):
    return sorted(k for k in a if k not in ignore and a[k] != b.get(k))


def run(rt, it, scenario, src, rec, work):
    out_blend, out_dir = work / scenario / 'test.blend', work / scenario / 'run'
    measure, author = it.measure, rt.author
    calls = {'n': 0}
    observed = {}

    def bad_measure(*a, **k):
        calls['n'] += 1
        if calls['n'] == 1:
            sc = bpy.context.scene
            observed['measure_start_frame'] = sc.frame_current
        if calls['n'] == FAIL_AT:
            observed['frame_at_failure'] = bpy.context.scene.frame_current
            raise (KeyboardInterrupt if scenario == 'interrupt_mid_measure' else RuntimeError)('induced by state_restoration_audit')
        return measure(*a, **k)

    def bad_author(*a, **k):
        raise RuntimeError('induced by state_restoration_audit (authoring)')
    if scenario in ('fail_mid_measure', 'interrupt_mid_measure'):
        it.measure = bad_measure
    if scenario == 'fail_during_authoring':
        rt.author = bad_author
    before = sha(src)
    sys.argv = ['run', '--source-blend', str(src), '--record', str(rec), '--out-blend', str(out_blend), '--out-dir', str(out_dir)]
    raised = None
    try:
        rt.main()
    except (Exception, KeyboardInterrupt) as e:
        raised = f'{type(e).__name__}: {e}'
    finally:
        it.measure, rt.author = measure, author
    sc = bpy.context.scene
    res = {'raised': raised, 'source_sha256_unchanged': sha(src) == before,
           'test_blend_exists': out_blend.exists(), 'report_exists': (out_dir / 'isolated_report.json').exists(),
           'samples_exists': (out_dir / 'isolated_samples.json').exists(),
           'session_frame_after': [sc.frame_current, round(sc.frame_subframe, 6)], 'observed': observed}
    if out_blend.exists():
        res['test_blend_sha256'] = sha(out_blend)
        if res['report_exists']:
            rep = json.loads((out_dir / 'isolated_report.json').read_text())
            res['report_frame_restored'] = rep['provenance']['frame_restored']
            res['report_test_blend_sha_matches_file'] = rep['provenance']['test_blend_sha256'] == res['test_blend_sha256'] == rep['provenance']['test_blend_sha256_after_measurement']
    return res


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    for a in ('--source-blend', '--record', '--work-dir', '--out'):
        ap.add_argument(a, required=True)
    o = ap.parse_args(argv)
    src, rec, work = Path(o.source_blend).resolve(), Path(o.record).resolve(), Path(o.work_dir).resolve()
    work.mkdir(parents=True, exist_ok=False)
    import run_isolated_tests_blender as rt
    it = rt.it
    bpy.ops.wm.open_mainfile(filepath=str(src)); snap0 = snapshot()
    out = {'source_blend': str(src), 'source_sha256': sha(src), 'fail_at_measure_call': FAIL_AT,
           'runner_sha256': sha(HERE / 'run_isolated_tests_blender.py'), 'blender': bpy.app.version_string,
           'source_snapshot': {k: v for k, v in snap0.items() if k not in ('constraints', 'drivers')},
           'source_constraint_count': len(snap0['constraints']), 'source_driver_count': len(snap0['drivers']), 'scenarios': {}}
    for scenario in ('normal', 'fail_mid_measure', 'interrupt_mid_measure', 'fail_during_authoring'):
        r = run(rt, it, scenario, src, rec, work)
        bpy.ops.wm.open_mainfile(filepath=str(src)); s1 = snapshot()
        r['source_reopened_state_diff_vs_before'] = diff(snap0, s1)
        tb = work / scenario / 'test.blend'
        if tb.exists():
            bpy.ops.wm.open_mainfile(filepath=str(tb)); s2 = snapshot()
            r['test_blend_state_diff_vs_source'] = diff(snap0, s2)
            r['test_blend_constraints_equal_source'] = s2['constraints'] == snap0['constraints']
            r['test_blend_drivers_equal_source'] = s2['drivers'] == snap0['drivers']
            r['test_blend_frame'] = [s2['frame'], s2['subframe']]
        out['scenarios'][scenario] = r
        print(scenario, json.dumps(r)[:600])
    Path(o.out).parent.mkdir(parents=True, exist_ok=True)
    Path(o.out).write_text(json.dumps(out, indent=1) + '\n')


if __name__ == '__main__':
    main()
