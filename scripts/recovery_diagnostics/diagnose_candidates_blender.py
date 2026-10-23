"""Apply unchanged benchmark paths to pinned recovered candidates as diagnostics only.

The 67-bone production bridge remains rejected for the 77-bone authoring rig. This
adapter uses saved reference guides and existing rig metadata instead of rebuilding
an original production scene. It cannot grant archive equivalence or anatomy approval.
"""
import hashlib
import json
from pathlib import Path
import sys
import traceback

PRODUCTION_BONES=67
CANDIDATE_BONES=77
SOURCES={
 '2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c':'W8',
 '5969aa98122e267b6bdd94fdfaf6d2877a1b27f7ea8d11c6a8e078b467b0ff91':'V14',
 'fb3b0acfc68bc59952b0fc6c45f7d7715717207fd9ba0b7f2b124e905ce2ddcb':'R120'}
NAMES=['squat','bent_over_row','shoulder_press','lunge','walk_stride','trunk_rotation','grip',
       'single_leg_stance','calf_raise','deadlift','push_up','forearm_rotation','wrist_circuit']


def candidate_name(digest):
    if digest not in SOURCES:raise ValueError('Source is not an inventoried recovered candidate')
    return SOURCES[digest]


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def rest_signature(rig,body):
    bones=[(b.name,b.parent.name if b.parent else None,list(b.head_local),list(b.tail_local),[list(row) for row in b.matrix_local]) for b in rig.data.bones]
    return hashlib.sha256(json.dumps(bones,sort_keys=True).encode()).hexdigest()


def loaded_result(bpy,correction,drives):
    rig=bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
    body=bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
    anatomy=bpy.data.objects['HGPT_ANATOMICAL_MASTER']
    if len(rig.data.bones)!=CANDIDATE_BONES or len(anatomy.data.bones)!=206:
        raise ValueError('Recovered candidate native inventory changed')
    for pb in rig.pose.bones:pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    guides={'sternum':bpy.data.objects['HGPT_authored_sternum_TMP']}
    for n in range(1,13):
        for side in ('left','right'):
            guides[f'rib_{n:02d}_{side}']=bpy.data.objects[f'HGPT_reference_rib_{n:02d}_{side}_TMP']
    result={'runtime':rig,'body':body,'anatomy':anatomy,'objects':guides,'humeral_rest_axial_deg':{}}
    for side,name in correction.HUMERI:
        b=rig.data.bones[name]
        result['humeral_rest_axial_deg'][name]=correction.corr.humeral_axial_angle_deg(
            tuple(b.tail_local-b.head_local),tuple(b.matrix_local.col[0].xyz),40.0,side)
    for key in body.data.shape_keys.key_blocks[1:]:key.value=0
    drives.setup(result)
    return result


def main():
    import bpy
    args=sys.argv[sys.argv.index('--')+1:]
    source,root,out=map(lambda x:Path(x).resolve(),args)
    if out.exists() or source==out:raise ValueError('Diagnostic report must be new and separate')
    digest=sha(source);name=candidate_name(digest)
    sys.path[:0]=[str(root/'scripts'),str(root/'scripts/anatomy_fit'),str(Path(__file__).resolve().parents[1]/'body_v2')]
    import build_original_review_candidate_r17_blender as r17
    import build_original_movement_benchmarks_blender as bench
    import build_functional_shoulder_correction_blender as correction
    import original_v1_review_candidate_drives as drives
    import original_v1_press_extension as px
    import original_v1_functional_fullbody as production
    from recovery_summary import summarize
    if production.EXPECTED_RUNTIME_BONES!=PRODUCTION_BONES:raise ValueError('Production bridge contract changed')
    report={'candidate':name,'source_sha256':digest,'blender':bpy.app.version_string,'benchmarks':{},'errors':{},
            'production_bridge':'INCOMPATIBLE — unchanged 67-bone contract; recovered authoring rig has 77',
            'archive_equivalence':'FAIL','anatomical_approval':'NOT_GRANTED','approved':False}
    from fixed_measurement_triangles import freeze_evaluated
    original=correction.build_corrected_scene
    original_evaluated=bench._evaluated
    report['measurement_tessellation']={}
    try:
        for path in NAMES:
            try:
                bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
                rig=bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL'];body=bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
                rest_before=rest_signature(rig,body)
                result=loaded_result(bpy,correction,drives)
                px.install()
                if 'hgpt_cap_fraction_ramp' in rig or px._PATH['name']!='v4':raise ValueError('Unexpected press setup')
                correction.build_corrected_scene=lambda:result
                def native_triangles(ob):
                    evaluated=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
                    mesh=evaluated.to_mesh()
                    try:
                        mesh.calc_loop_triangles()
                        return [tuple(t.vertices) for t in mesh.loop_triangles]
                    finally:evaluated.to_mesh_clear()
                bench._evaluated,tessellation=freeze_evaluated(original_evaluated,native_triangles)
                report['measurement_tessellation'][path]=tessellation
                outcome=bench.run(only=[path],post_pose=lambda r:drives.drive(r['runtime'],r['body']))
                report['benchmarks'][path]=outcome['benchmarks'][path]
                if rest_signature(rig,body)!=rest_before:raise ValueError('Transient setup changed candidate rest bones')
                print('CANDIDATE_PATH_DONE',name,path,flush=True)
            except Exception:
                report['errors'][path]=traceback.format_exc()
                print('CANDIDATE_PATH_FAILED',name,path,report['errors'][path],flush=True)
            report['summary']=summarize(report['benchmarks'],NAMES,bench.FRAMES)
            # Rest/source errors must never be hidden by a complete numerical result.
            if report['errors']:report['summary']['complete']=False;report['summary']['quality_pass']=False
            report['source_unchanged']=sha(source)==digest
            out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2,default=str)+'\n')
    finally:
        correction.build_corrected_scene=original
        bench._evaluated=original_evaluated
    if not report['summary']['complete'] or not report['source_unchanged']:raise SystemExit(1)

if __name__=='__main__':main()
