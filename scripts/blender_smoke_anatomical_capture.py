#!/usr/bin/env python3
"""Live Blender smoke verification of the read-only anatomical capture adapter.

Builds synthetic .blend fixtures whose answers are known analytically, saves them in a
fresh output directory, re-opens each saved file and runs the real capture adapter
(`capture_anatomical_validation_blender.capture_character`). Expected values are computed
from hand-derived transforms or an independent forward-kinematics chain, never from the
adapter's own code path.

Run either with Blender:  blender --background --python scripts/blender_smoke_anatomical_capture.py -- --out DIR
or with the bpy module:   python3 scripts/blender_smoke_anatomical_capture.py --out DIR

Nothing in the repository or any character file is modified. The fixtures are synthetic;
passing this smoke test verifies the adapter mechanics only, not any anatomical fit.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import anatomical_blender_validation as core  # noqa: E402
import capture_anatomical_validation_blender as adapter  # noqa: E402

RIG = 'HGPT_SMOKE_RIG'
DECOY = 'HGPT_SMOKE_DECOY'
MARKER = 'HGPT_JOINT_tibiofemoral_left'
BONE_MARKER = 'HGPT_JOINT_patellofemoral_left'
CM = 0.01  # metres per Blender unit in the fixture (scene unit scale 0.01)
FPS, FPS_BASE = 30, 1.001
TOL = 1e-6


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def add_armature(name, location, rotation_z_deg, scale, femur_head_z):
    data = bpy.data.armatures.new(name + '_data')
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (0, 0, math.radians(rotation_z_deg))
    obj.scale = (scale, scale, scale)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    femur = data.edit_bones.new('anat_femur_left')
    femur.head, femur.tail, femur.roll = (0, 0, femur_head_z), (0, 0, 50), 0
    tibia = data.edit_bones.new('anat_tibia_left')
    tibia.head, tibia.tail, tibia.roll = (0, 0, 50), (0, 0, 10), 0
    tibia.parent, tibia.use_connect = femur, True
    ctrl = data.edit_bones.new('ctrl_knee_helper')  # untagged runtime helper
    ctrl.head, ctrl.tail, ctrl.roll = (10, 0, 50), (10, 0, 40), 0
    bpy.ops.object.mode_set(mode='OBJECT')
    return obj


def linear_keys(owner, path, index, pairs):
    for frame, value in pairs:
        if index is None:
            owner[path] = value
            owner.keyframe_insert(data_path='["%s"]' % path, frame=frame)
        else:
            getattr(owner, path)[index] = value
            owner.keyframe_insert(data_path=path, index=index, frame=frame)


def make_linear(anim_data):
    action = anim_data.action
    # Blender 4.4+ layered actions keep F-curves in channelbags; older versions expose action.fcurves.
    curves = []
    if hasattr(action, 'layers') and action.layers:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    curves.extend(bag.fcurves)
    else:
        curves = list(action.fcurves)
    for curve in curves:
        for key in curve.keyframe_points:
            key.interpolation = 'LINEAR'


def build_fixture(path, python_driver=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = CM
    scene.render.fps, scene.render.fps_base = FPS, FPS_BASE
    add_armature(DECOY, (0, 0, 0), 0, 1, 70)  # same bone names, different geometry
    rig = add_armature(RIG, (100, 0, 0), 90, 2, 90)
    pose = rig.pose.bones
    for bone in pose:
        bone.rotation_mode = 'XYZ'
    # Animated helper drives the tibia only through a constraint.
    linear_keys(pose['ctrl_knee_helper'], 'rotation_euler', 0, [(1, 0.0), (11, math.radians(90))])
    con = pose['anat_tibia_left'].constraints.new('COPY_ROTATION')
    con.target, con.subtarget = rig, 'ctrl_knee_helper'
    con.target_space = con.owner_space = 'LOCAL'
    # Animated object property drives the femur only through a driver.
    linear_keys(rig, 'hip_flex', None, [(1, 0.0), (11, math.radians(30))])
    fcurve = pose['anat_femur_left'].driver_add('rotation_euler', 0)
    driver = fcurve.driver
    driver.type = 'SCRIPTED'
    var = driver.variables.new()
    var.name, var.type = 'flex', 'SINGLE_PROP'
    var.targets[0].id_type, var.targets[0].id = 'OBJECT', rig
    var.targets[0].data_path = '["hip_flex"]'
    driver.expression = "flex + __import__('math').radians(0)" if python_driver else 'flex'
    make_linear(rig.animation_data)
    # Explicitly fitted joint marker: armature-parented, deliberately NOT at a bone head.
    marker = bpy.data.objects.new(MARKER, None)
    scene.collection.objects.link(marker)
    marker.parent = rig
    marker.location = (0, 2, 50)
    marker['hgpt_joint_id'] = 'tibiofemoral_left'
    # Bone-parented marker: follows the femur, offset in bone-tail space.
    bmarker = bpy.data.objects.new(BONE_MARKER, None)
    scene.collection.objects.link(bmarker)
    bmarker.parent, bmarker.parent_type, bmarker.parent_bone = rig, 'BONE', 'anat_femur_left'
    bmarker.location = (3, 0, 0)
    landmark = bpy.data.objects.new('LM_femoral_head_left', None)
    scene.collection.objects.link(landmark)
    landmark.location = (1, 2, 3)
    landmark['hgpt_landmark_id'] = 'femur_left/femoral_head_centre'
    # A landmark object that exists in the file but in another scene must not be captured.
    other = bpy.data.scenes.new('SMOKE_OTHER_SCENE')
    stray = bpy.data.objects.new('LM_stray_other_scene', None)
    other.collection.objects.link(stray)
    stray['hgpt_landmark_id'] = 'femur_left/stray'
    scene.frame_start, scene.frame_end = 1, 11
    scene.frame_set(3, subframe=0.25)
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    return path


def open_file(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))


def expected_chain(frame_value):
    """Independent FK: rest matrices from edit geometry, pose from the analytic animation."""
    t = (frame_value - 1) / 10
    hip, knee = math.radians(30) * t, math.radians(90) * t
    rig = bpy.data.objects[RIG]
    femur_rest = rig.data.bones['anat_femur_left'].matrix_local
    tibia_rest = rig.data.bones['anat_tibia_left'].matrix_local
    femur = femur_rest @ Matrix.Rotation(hip, 4, 'X')
    tibia = femur @ (femur_rest.inverted() @ tibia_rest) @ Matrix.Rotation(knee, 4, 'X')
    world = Matrix.Translation((100, 0, 0)) @ Matrix.Rotation(math.radians(90), 4, 'Z') @ Matrix.Scale(2, 4)
    tibia_tail = world @ tibia @ Vector((0, rig.data.bones['anat_tibia_left'].length, 0))
    femur_tail = world @ femur @ Vector((0, rig.data.bones['anat_femur_left'].length, 0))
    return {'tibia_tail_m': [v * CM for v in tibia_tail], 'femur_tail_m': [v * CM for v in femur_tail],
            'hip_deg': math.degrees(hip), 'knee_deg': math.degrees(knee)}


def close(a, b, tol=TOL):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def run(out):
    out = Path(out).resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('Use a fresh output directory')
    out.mkdir(parents=True, exist_ok=True)
    checks = {}

    def record(key, ok, detail):
        checks[key] = {'status': 'PASS' if ok else 'FAIL', 'detail': detail}

    fixture = build_fixture(out / 'smoke_fixture.blend')
    fixture_hash, fixture_mtime = sha(fixture), os.stat(fixture).st_mtime_ns
    open_file(fixture)
    scene = bpy.context.scene
    record('saved_initial_frame', scene.frame_current == 3 and abs(scene.frame_subframe - 0.25) < 1e-6,
           {'frame': scene.frame_current, 'subframe': scene.frame_subframe})
    plan = core.build_plan()
    plan['samples'] = [
        {'test_id': 'isolated_knee', 'frame': 1, 'subframe': 0, 'side': 'left', 'plane': 'sagittal',
         'direction': 'outbound', 'posture': 'synthetic', 'load': 'unloaded', 'measurement_mode': 'smoke'},
        {'test_id': 'isolated_knee', 'frame': 6, 'subframe': 0.5, 'side': 'left', 'plane': 'sagittal',
         'direction': 'outbound', 'posture': 'synthetic', 'load': 'unloaded', 'measurement_mode': 'smoke'},
        {'test_id': 'isolated_knee', 'frame': 11, 'subframe': 0, 'side': 'left', 'plane': 'sagittal',
         'direction': 'outbound', 'posture': 'synthetic', 'load': 'unloaded', 'measurement_mode': 'smoke'}]
    capture = adapter.capture_character(bpy, RIG, plan, CM)
    report = core.analyze_capture(capture, plan)
    core.write_new_json(out / 'smoke_capture.json', capture)
    core.write_new_json(out / 'smoke_report.json', report)
    rest = capture['rest_bones']
    record('armature_selection', set(rest) == {'anat_femur_left', 'anat_tibia_left', 'ctrl_knee_helper'}
           and close(rest['anat_femur_left']['head_world_m'], [1.0, 0.0, 1.8]),
           {'captured_bones': sorted(rest), 'femur_head_m': rest['anat_femur_left']['head_world_m'],
            'expected_m': [1.0, 0.0, 1.8], 'decoy_femur_head_m_if_wrong': [0.0, 0.0, 0.7]})
    record('rest_world_unit_conversion', close(rest['anat_tibia_left']['tail_world_m'], [1.0, 0.0, 0.2]),
           {'tibia_tail_m': rest['anat_tibia_left']['tail_world_m'], 'expected_m': [1.0, 0.0, 0.2],
            'derivation': 'R_z(90deg) * 2 * (0,0,10)BU + (100,0,0)BU, times 0.01 m/BU'})
    s0, s_mid, s_end = capture['samples']
    m0 = s0['joint_frames'].get('tibiofemoral_left')
    marker_pos = [m0['matrix_world'][i][3] for i in range(3)] if m0 else None
    tibia_head = s0['bones']['anat_tibia_left']['head_world_m']
    record('offset_marker_not_bone_head', marker_pos is not None and close(marker_pos, [0.96, 0.0, 1.0])
           and abs(math.dist(marker_pos, tibia_head) - 0.04) < TOL,
           {'marker_m': marker_pos, 'expected_m': [0.96, 0.0, 1.0], 'tibia_head_m': tibia_head,
            'expected_offset_m': 0.04})
    # Bone-parented marker: independent formula world @ pose_bone @ T(0,length,0) @ basis.
    fixture_rig = bpy.data.objects[RIG]
    end_chain = expected_chain(11)
    femur_tail_end = end_chain['femur_tail_m']
    bm = s_end['joint_frames'].get('patellofemoral_left')
    bm_pos = [bm['matrix_world'][i][3] for i in range(3)] if bm else None
    record('bone_parented_marker_follows_evaluated_pose', bm_pos is not None and
           abs(math.dist(bm_pos, femur_tail_end) - 0.06) < TOL,
           {'marker_m': bm_pos, 'femur_tail_m': femur_tail_end,
            'expected_distance_m': 0.06, 'derivation': '3 BU bone-space X offset times object scale 2 times 0.01'})
    for label, sample, frame_value in [('start', s0, 1), ('subframe', s_mid, 6.5), ('end', s_end, 11)]:
        exp = expected_chain(frame_value)
        got = sample['bones']['anat_tibia_left']['tail_world_m']
        record('evaluated_pose_' + label, close(got, exp['tibia_tail_m'], 1e-5),
               {'tibia_tail_m': got, 'expected_m': exp['tibia_tail_m'], 'knee_deg': exp['knee_deg'],
                'hip_deg': exp['hip_deg']})
    record('rest_differs_from_evaluated_pose',
           not close(rest['anat_tibia_left']['tail_world_m'], s_end['bones']['anat_tibia_left']['tail_world_m'], 1e-3),
           'Rest geometry stays rest; frame-11 evaluated tibia differs.')
    rel = {r['sample']: r['principal_rotation_from_first_deg'] for r in report['relative_bone_transforms']['anat_tibia_left']}
    femur_rel = {r['sample']: r['principal_rotation_from_first_deg'] for r in report['relative_bone_transforms']['anat_femur_left']}
    record('known_90_degree_rotation_via_constraint', abs(rel[2] - 90) < 1e-4 and abs(rel[1] - 49.5) < 1e-4,
           {'tibia_relative_to_femur_deg': rel, 'expected': {'1': 49.5, '2': 90.0},
            'mechanism': 'COPY_ROTATION constraint from untagged keyed helper'})
    record('driver_evaluation', abs(femur_rel[2] - 30) < 1e-4 and abs(femur_rel[1] - 16.5) < 1e-4,
           {'femur_world_rotation_change_deg': femur_rel, 'expected': {'1': 16.5, '2': 30.0},
            'mechanism': 'simple-expression driver from keyed object property'})
    times = [s['time_seconds'] for s in capture['samples']]
    fps = FPS / FPS_BASE
    # Blender stores fps_base in single precision (1.001 -> 1.00100004673), so compare relatively.
    expected_times = [1 / fps, 6.5 / fps, 11 / fps]
    record('sample_times_use_fps_base', all(abs(a - b) <= 1e-7 * b for a, b in zip(times, expected_times)),
           {'times_s': times, 'expected_s': expected_times, 'fps': fps})
    landmark_ids = sorted(l['landmark_id'] for l in s0['landmarks'].values())
    record('landmarks_only_from_active_scene', landmark_ids == ['femur_left/femoral_head_centre'],
           {'captured_landmark_ids': landmark_ids})
    prov = capture['provenance']
    record('frame_restored_after_success', prov['frame_restored'] and scene.frame_current == 3
           and abs(scene.frame_subframe - 0.25) < 1e-6, {'frame': scene.frame_current, 'subframe': scene.frame_subframe})
    record('unit_scale_consistency_recorded', abs(prov.get('scene_scale_length', 0) - CM) <= 1e-6 * CM and
           prov.get('unit_scale_consistent') is True, {k: prov.get(k) for k in
           ['scene_unit_system', 'scene_scale_length', 'unit_scale_consistent']})
    # Mismatched explicit conversion must not pass the units check.
    mismatch = adapter.capture_character(bpy, RIG, core.build_plan(), 1.0)
    mismatch_report = core.analyze_capture(mismatch, core.build_plan())
    record('unit_scale_mismatch_detected', mismatch['provenance'].get('unit_scale_consistent') is False and
           mismatch_report['checks']['units']['status'] != 'PASS',
           {'units_check': mismatch_report['checks']['units']})
    # Failure path: an invalid evidence image aborts mid-sampling; the frame must still be restored.
    bad = core.build_plan()
    bad['samples'] = [dict(plan['samples'][0]), dict(plan['samples'][2], evidence_images=['/nonexistent/x.png'])]
    raised = None
    try:
        adapter.capture_character(bpy, RIG, bad, CM)
    except ValueError as error:
        raised = str(error)
    record('frame_restored_after_failure', raised is not None and scene.frame_current == 3 and
           abs(scene.frame_subframe - 0.25) < 1e-6,
           {'raised': raised, 'frame': scene.frame_current, 'subframe': scene.frame_subframe})
    errors = {}
    for name in ['NOT_PRESENT', MARKER]:
        try:
            adapter.capture_character(bpy, name, core.build_plan(), CM)
        except ValueError as error:
            errors[name] = str(error)
    record('non_armature_names_refused', len(errors) == 2, errors)
    # A same-named joint marker that exists only in another scene must be refused, not silently measured.
    other_marker = bpy.data.objects.new('HGPT_JOINT_talocrural_left', None)
    bpy.data.scenes['SMOKE_OTHER_SCENE'].collection.objects.link(other_marker)
    try:
        adapter.capture_character(bpy, RIG, core.build_plan(), CM)
        outside = None
    except ValueError as error:
        outside = str(error)
    bpy.data.objects.remove(other_marker)
    record('marker_outside_scene_refused', outside is not None and 'outside the active scene' in outside,
           {'raised': outside})
    record('source_preserved', sha(fixture) == fixture_hash and os.stat(fixture).st_mtime_ns == fixture_mtime and
           prov['source_file_unchanged'] and prov['blend_sha256'] == fixture_hash,
           {'sha256': fixture_hash, 'after': sha(fixture)})
    record('report_scope', report['character_accepted'] is False and report['completed_tracker_gates'] == [],
           {'overall_status': report['overall_status']})
    # Python-expression driver: execution must be either evaluated or explicitly reported as failed.
    py_fixture = build_fixture(out / 'smoke_python_driver.blend', python_driver=True)
    open_file(py_fixture)
    py_plan = core.build_plan()
    py_plan['samples'] = [dict(plan['samples'][2])]
    py_capture = adapter.capture_character(bpy, RIG, py_plan, CM)
    py_report = core.analyze_capture(py_capture, py_plan)
    core.write_new_json(out / 'smoke_python_driver_capture.json', py_capture)
    evaluated = py_report['relative_bone_transforms']['anat_femur_left'][0]['matrix']
    femur_axis_z = evaluated[2][1]  # world Z component of bone Y axis
    expected_axis_z = -math.cos(math.radians(30))
    driver_ran = abs(femur_axis_z - expected_axis_z) < 1e-4
    flagged = py_capture['provenance'].get('automatic_python_execution_failed') is True
    record('python_driver_failure_not_silent', driver_ran != flagged and
           (py_report['checks']['provenance']['status'] != 'PASS' if flagged else True),
           {'driver_evaluated': driver_ran, 'reported_failed': flagged,
            'provenance_check': py_report['checks']['provenance'],
            'autoexec_enabled': bool(bpy.context.preferences.filepaths.use_scripts_auto_execute)})
    summary = {'blender_version': bpy.app.version_string, 'binary': bpy.app.binary_path or 'bpy module',
               'adapter_sha256': sha(Path(adapter.__file__)), 'core_sha256': sha(Path(core.__file__)),
               'fixture_sha256': fixture_hash, 'checks': checks,
               'overall': 'PASS' if all(c['status'] == 'PASS' for c in checks.values()) else 'FAIL',
               'scope': 'Synthetic adapter mechanics only; no anatomical fit or gate acceptance.'}
    core.write_new_json(out / 'smoke_summary.json', summary)
    for key, value in checks.items():
        print(value['status'], key)
    print('SMOKE', summary['overall'])
    return 0 if summary['overall'] == 'PASS' else 1


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    return run(parser.parse_args(argv).out)


if __name__ == '__main__':
    raise SystemExit(main())
