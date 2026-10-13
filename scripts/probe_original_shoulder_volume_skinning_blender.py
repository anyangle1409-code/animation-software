"""Compare native linear vs volume-preserving skinning; source bytes immutable."""
import bpy,json,sys,runpy,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
out=Path(sys.argv[sys.argv.index('--')+1]).resolve();out.mkdir(parents=True,exist_ok=True)
source=Path(bpy.data.filepath);digest=hashlib.sha256(source.read_bytes()).hexdigest()
body=bpy.data.objects['HGPT_BODY_SHOULDER_REFIT_TRIAL']
modifier=next(m for m in body.modifiers if m.type=='ARMATURE')
assert not modifier.use_deform_preserve_volume,'Baseline already uses volume preservation'
script=ROOT/'scripts/locate_original_shoulder_skin_distortion_blender.py'
baseline_path=out/'linear_shoulder_distortion.json'
sys.argv=['blender','--',str(baseline_path)];runpy.run_path(str(script))
modifier.use_deform_preserve_volume=True
volume_path=out/'volume_shoulder_distortion.json'
sys.argv=['blender','--',str(volume_path)];runpy.run_path(str(script))
before=json.loads(baseline_path.read_text());after=json.loads(volume_path.read_text())
candidate=out/'HomeGymPT_ORIGINAL_v1_SHOULDER_VOLUME_SKINNING_TRIAL.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(candidate))
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
report={'input_candidate_sha256':digest,'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
    'changed_setting':'copied body Armature.use_deform_preserve_volume False->True',
    'before':{k:before[k] for k in ('area_ratio_below_0_1_count','area_ratio_above_2_count')},
    'after':{k:after[k] for k in ('area_ratio_below_0_1_count','area_ratio_above_2_count')},
    'before_minimum_region_area_ratio':before['worst_compressed'][0]['area_ratio'],
    'after_minimum_region_area_ratio':after['worst_compressed'][0]['area_ratio'],
    'source_file_unchanged':True,'weights_refitted':False,'shape_correctives_authored':False,
    'production_approved':False,'anatomical_approval':False,'motion_accepted':False,
    'limits':['Native dual-quaternion volume preservation, not muscle simulation.',
        'GLB/runtime linear skinning will NOT preserve this modifier behavior; no GLB exported.',
        'Area ratios remain distortion diagnostics; source frame/ROM and original foot defects unchanged.']}
(out/'volume_skinning_comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print('VOLUME_SKINNING_COMPARISON',report)
