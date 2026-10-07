#!/usr/bin/env python3
"""Read-only capture of an explicitly selected local armature and authored animation frames.

No poses, markers or bones are created. No .blend is saved. Run on an isolated audit copy.
The numerical/report code can be tested outside Blender; this adapter still requires a local smoke test.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from anatomical_blender_validation import (analyze_capture,atlas_hashes,build_plan,
    report_markdown,sample_with_frame_restore,write_new_json)


def capture_character(bpy,armature_name,plan,scale):
    if type(scale) not in (int,float) or not math.isfinite(scale) or scale<=0:
        raise ValueError('Explicit positive metres per Blender world unit required')
    canonical=build_plan()
    for key in ['atlas_sha256','expected_bones','joint_markers','profile_cases','functional_cases','bone_frames','landmark_recipes']:
        if plan.get(key)!=canonical[key]:raise ValueError('Stale or altered reference contract: '+key)
    scene=bpy.context.scene
    in_scene={obj.name for obj in scene.objects}
    rig=bpy.data.objects.get(armature_name)
    if rig is None or rig.type!='ARMATURE':raise ValueError('Explicit armature name does not identify an armature')
    if rig.name not in in_scene:raise ValueError('Armature is not in the active scene; its evaluated pose is not measurable')
    source=Path(bpy.data.filepath).resolve()
    if not bpy.data.filepath or not source.is_file() or source.suffix!='.blend':
        raise ValueError('Open a saved audit .blend first; unsaved scenes have no source identity')
    source_before=hashlib.sha256(source.read_bytes()).hexdigest()
    initial_frame,initial_subframe=scene.frame_current,scene.frame_subframe
    dirty=bool(bpy.data.is_dirty)
    fps=scene.render.fps/scene.render.fps_base
    if not math.isfinite(fps) or fps<=0:raise ValueError('Positive evaluated scene FPS required')
    unit_system=scene.unit_settings.system
    scale_length=float(scene.unit_settings.scale_length)
    # The scene unit scale is single precision; compare relatively. NONE declares no physical unit.
    unit_consistent=None if unit_system=='NONE' else abs(scale_length-scale)<=1e-6*max(scale_length,scale)
    reverse_names={v:k for k,v in plan['expected_bones'].items()}
    def matrix_world_m(matrix):
        result=[[float(matrix[r][c]) for c in range(4)] for r in range(4)]
        for r in range(3):result[r][3]*=scale
        return result
    def point_world_m(matrix,local):return [float(v)*scale for v in matrix@local]
    depsgraph=bpy.context.evaluated_depsgraph_get()
    evaluated=rig.evaluated_get(depsgraph)
    rest={}
    for bone in rig.data.bones:
        anatomical_id=bone.get('hgpt_anatomical_id',reverse_names.get(bone.name))
        rest[bone.name]={'anatomical_id':anatomical_id,'parent':bone.parent.name if bone.parent else None,
            'head_world_m':point_world_m(evaluated.matrix_world,bone.head_local),
            'tail_world_m':point_world_m(evaluated.matrix_world,bone.tail_local),
            'matrix_world':matrix_world_m(evaluated.matrix_world@bone.matrix_local)}
    requests=plan.get('samples',[])
    if not isinstance(requests,list):raise ValueError('Plan samples must be a list')
    if not requests:
        requests=[{'test_id':'unassigned_current_pose','frame':initial_frame,'subframe':initial_subframe,
                   'side':'unspecified','plane':'unspecified','direction':'static',
                   'posture':'current saved scene','load':'unspecified','measurement_mode':'unspecified'}]
    def collect(request):
        depsgraph=bpy.context.evaluated_depsgraph_get()
        obj=rig.evaluated_get(depsgraph)
        bones={}
        for bone in obj.pose.bones:
            bones[bone.name]={'parent':bone.parent.name if bone.parent else None,
                'head_world_m':point_world_m(obj.matrix_world,bone.head),
                'tail_world_m':point_world_m(obj.matrix_world,bone.tail),
                'matrix_world':matrix_world_m(obj.matrix_world@bone.matrix)}
        markers={}
        for key,binding in plan['joint_markers'].items():
            marker=bpy.data.objects.get(binding['object_name'])
            if marker is None:continue
            if marker.name not in in_scene:raise ValueError('Joint marker exists outside the active scene: '+marker.name)
            if marker.type!='EMPTY':raise ValueError('Joint-frame reference must be an explicit EMPTY: '+marker.name)
            if marker.get('hgpt_joint_id',key)!=key:raise ValueError('Marker joint-ID/name mismatch: '+marker.name)
            measured=marker.evaluated_get(depsgraph)
            markers[key]={'object_name':marker.name,'frame_id':binding['frame_id'],
                          'matrix_world':matrix_world_m(measured.matrix_world)}
        landmarks={}
        for marker in scene.objects:
            landmark_id=marker.get('hgpt_landmark_id')
            if landmark_id:
                measured=marker.evaluated_get(depsgraph)
                landmarks[marker.name]={'landmark_id':str(landmark_id),
                    'position_world_m':[float(v)*scale for v in measured.matrix_world.translation]}
        images=[]
        for filename in request.get('evidence_images',[]):
            path=Path(filename)
            if not path.is_absolute() or not path.is_file():raise ValueError('Evidence images must identify existing absolute paths')
            images.append({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        metadata={key:request.get(key) for key in plan['sample_fields']}
        return dict(metadata,time_seconds=(request['frame']+request.get('subframe',0))/fps,bones=bones,joint_frames=markers,
                    landmarks=landmarks,evidence_images=images)
    samples=sample_with_frame_restore(scene,requests,collect)
    after=hashlib.sha256(source.read_bytes()).hexdigest()
    return {'schema_version':1,'units':'metres','metres_per_world_unit':scale,
        'provenance':{'blend_path':str(source),'blend_sha256':source_before,'blend_sha256_after':after,
            'source_file_unchanged':after==source_before,'dirty_before_capture':dirty,
            'dirty_after_capture':bool(bpy.data.is_dirty),'blender_version':bpy.app.version_string,
            'armature':armature_name,'atlas_sha256':atlas_hashes(),
            'automatic_python_execution_failed':bool(bpy.app.autoexec_fail),
            'scene_fps':fps,'scene_unit_system':unit_system,
            'scene_scale_length':scale_length,'unit_scale_consistent':unit_consistent,
            'initial_frame':initial_frame,'initial_subframe':initial_subframe,
            'rest_world_basis':'Rest bone geometry transformed by evaluated object matrix at initial scene frame.',
            'frame_restored':scene.frame_current==initial_frame and scene.frame_subframe==initial_subframe},
        'rest_bones':rest,'samples':samples,'character_accepted':False}


def main():
    import bpy
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--armature',required=True);parser.add_argument('--plan')
    parser.add_argument('--blend',help='Open this saved audit .blend first (bpy-module use); Blender CLI users pass it to blender instead')
    parser.add_argument('--metres-per-unit',type=float,required=True);parser.add_argument('--out-directory',required=True)
    options=parser.parse_args(args)
    out=Path(options.out_directory).resolve()
    names=['capture.json','report.json','report.md']
    if any((out/name).exists() for name in names):raise FileExistsError('Use a new audit output directory; outputs are never overwritten')
    plan=json.loads(Path(options.plan).read_text()) if options.plan else build_plan()
    if options.blend:bpy.ops.wm.open_mainfile(filepath=str(Path(options.blend).resolve()))
    capture=capture_character(bpy,options.armature,plan,options.metres_per_unit)
    result=analyze_capture(capture,plan)
    write_new_json(out/'capture.json',capture);write_new_json(out/'report.json',result)
    with (out/'report.md').open('x',encoding='utf-8') as stream:stream.write(report_markdown(result))
    print('Anatomical capture written:',out,'status:',result['overall_status'],'character remains unaccepted')
    return 1 if result['overall_status']=='FAIL' else 0

if __name__=='__main__':raise SystemExit(main())
