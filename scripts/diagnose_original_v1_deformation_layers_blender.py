"""Read-only shoulder deformation-layer capture for the exact r95 candidate.

Loads the frozen P3a pose-construction section, samples generic flexion and
abduction arcs, isolates weights and each corrective family in memory, writes
one hash-bound JSON report, and never saves the Blend.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

SCRIPT=Path(__file__).resolve()
ROOT=SCRIPT.parents[1]
EXPECTED_REVISION='r95'
EXPECTED_SHA='8a39a22d3fec36f82c1cd53f6d0a976748a8cf97de14d81e62b5789178403bdd'
argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if not argv: raise SystemExit('usage: blender <r95.blend> --python diagnose_original_v1_deformation_layers_blender.py -- <report.json>')
REPORT_OUT=Path(argv[0]).resolve()

candidate=Path(bpy.data.filepath).resolve()
candidate_sha=hashlib.sha256(candidate.read_bytes()).hexdigest()
if candidate_sha!=EXPECTED_SHA: raise SystemExit('candidate SHA-256 is not exact r95: '+candidate_sha)

# Execute only the frozen production pose/driver definition section. The metrics
# and render loop are intentionally not executed.
pose_path=SCRIPT.with_name('pose_test_original_v1_o4_candidate_blender.py')
pose_source=pose_path.read_text(encoding='utf-8')
prefix=pose_source.split('# ---------------------------------------------------------------- metrics',1)[0]
saved_argv=list(sys.argv); diagnostic_file=__file__
sys.argv=[str(pose_path),'--',str(REPORT_OUT.parent),'']
globals()['__file__']=str(pose_path)
exec(compile(prefix,str(pose_path),'exec'),globals(),globals())
globals()['__file__']=diagnostic_file;sys.argv=saved_argv

# The flexion/scapular driver is installed immediately after the hash-frozen
# pose-definition marker in the production renderer. Install that same module
# explicitly because this diagnostic intentionally skips the metrics section.
import importlib.util
driver_path=SCRIPT.with_name('original_v1_flexion_driver.py')
driver_spec=importlib.util.spec_from_file_location('original_v1_flexion_driver',str(driver_path))
driver_module=importlib.util.module_from_spec(driver_spec)
driver_spec.loader.exec_module(driver_module)
driver_module.install(globals())

sys.path.insert(0,str(SCRIPT.parent))
from original_v1_deformation_layers import LAYER_KEYS,REQUIRED_KEYS,activation_snapshot,summarize_activation_arc,summarize_zone_displacement

# Preserve source vertex indices by disabling the presentation-only dressed mask
# in memory. The source file is never saved.
for modifier in body.modifiers:
    if modifier.type=='MASK':
        modifier.show_viewport=False
        modifier.show_render=False
bpy.context.view_layer.update()


def read_json(path): return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))


def zone_from(path):
    data=read_json(path)
    midline=set(data.get('midline_vertex_ids',[]))
    strict_left=[vertex_id for vertex_id in data['left_owned_vertex_ids'] if vertex_id not in midline]
    right=data['mirror_of_strict_left_vertex_ids']
    if len(strict_left)!=len(right): raise ValueError('declared mirror zone is not pair-complete: '+path)
    return {'left':strict_left,'right':right}


ZONES={
    'shoulder_yoke':zone_from('ORIGINAL_V1_WORK/candidates/repair_preparation/r93_clavicle_top_shape_limits_declared/shoulder_corrective_mask_declared_before_solve.json'),
    'posterior_axillary_lobe':zone_from('ORIGINAL_V1_WORK/candidates/repair_preparation/r95_scapular_lobe_corrective_declared/scapular_lobe_mask_declared_before_solve.json'),
    'anterior_axilla':zone_from('ORIGINAL_V1_WORK/candidates/repair_preparation/r77_axilla_pit_declared/axilla_pit_mask_declared_before_edit.json'),
}


def positions():
    bpy.context.view_layer.update()
    obj=body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return [tuple(obj.matrix_world @ vertex.co) for vertex in obj.data.vertices]


def skeleton_state():
    bpy.context.view_layer.update()
    names=['clavicle_l','clavicle_r','scapula_l','scapula_r','upperarm_l','upperarm_r','spine_03']
    return {name:{'head':list(rig.matrix_world @ pb(name).head),'tail':list(rig.matrix_world @ pb(name).tail)} for name in names}


def set_values(values):
    blocks=body.data.shape_keys.key_blocks
    for name in REQUIRED_KEYS: blocks[name].value=float(values.get(name,0.0))
    bpy.context.view_layer.update()


def build_pose(plane,angle_deg,rotation_deg):
    reset();rig.location=(0,0,0);rig.rotation_euler=(0,0,0);bpy.context.view_layer.update()
    theta=math.radians(angle_deg)
    for side in 'lr':
        horizontal=F if plane=='flexion' else lat(side)
        target=(D*math.cos(theta)+horizontal*math.sin(theta)).normalized()
        girdle_for_elevation(side,target)
        aim('upperarm_'+side,target)
        if abs(rotation_deg)>1e-9: rot('upperarm_'+side,bdir('upperarm_'+side),rotation_deg)
    upd()


samples=[]
arc_inputs={}
for plane in ('flexion','abduction'):
    for rotation_deg in (-30,0,30):
        arc_key=f'{plane}_rotation_{rotation_deg:+d}'
        arc_inputs[arc_key]=[]
        for angle in (0,30,60,90,120,150,165):
            build_pose(plane,angle,rotation_deg)
            production=activation_snapshot(scene,body,rig)
            production_values=production['values']
            states={}
            set_values({});states['rest']=positions()
            states['weights_only']=states['rest']
            for layer,pair in LAYER_KEYS.items():
                set_values({pair[0]:production_values[pair[0]],pair[1]:production_values[pair[1]]})
                states[layer+'_only']=positions()
            set_values(production_values);states['combined']=positions()
            displacement=summarize_zone_displacement(states,ZONES)
            layer_values={layer:(production['layers'][layer]['left']+production['layers'][layer]['right'])/2 for layer in LAYER_KEYS}
            arc_inputs[arc_key].append({'angle_deg':angle,'values':layer_values})
            samples.append({
                'plane':plane,'angle_deg':angle,'axial_rotation_deg':rotation_deg,
                'skeleton':skeleton_state(),'production_activation':production,
                'displacement_from_weights_only':displacement,
            })

report={
    'schema_version':1,
    'candidate_revision':EXPECTED_REVISION,
    'candidate_sha256':candidate_sha,
    'candidate_file':candidate.name,
    'blender_version':bpy.app.version_string,
    'production_pose_script':'scripts/'+pose_path.name,
    'production_pose_script_sha256':hashlib.sha256(pose_path.read_bytes()).hexdigest(),
    'diagnostic_script':'scripts/'+SCRIPT.name,
    'diagnostic_script_sha256':hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
    'angles_deg':[0,30,60,90,120,150,165],
    'planes':['flexion','abduction'],
    'axial_rotation_variants_deg':[-30,0,30],
    'zones':{name:{'left_count':len(row['left']),'right_count':len(row['right'])} for name,row in ZONES.items()},
    'activation_arcs':{name:summarize_activation_arc(rows) for name,rows in arc_inputs.items()},
    'samples':samples,
    'saved_blend':False,
    'production_approved':False,
    'interpretation_boundary':'Diagnostic measurements only. Visual anatomical review and whole-body regression evidence remain required.',
}
REPORT_OUT.parent.mkdir(parents=True,exist_ok=True)
REPORT_OUT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('DEFORMATION LAYERS CAPTURED',REPORT_OUT,len(samples),'samples')
