#!/usr/bin/env python3
"""Raw body/garment capture and paired evidence; no approval or clearance inference."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys
from audit_original_v1_changes import audit,validate
from original_v1_production_control import ROOT,digest,evidence,ensure_finite
from original_v1_locked_rig import load_locked_rig,blender_armature_issues
from verify_original_v1_production_promotion import safe_path

NAMES={'body':'HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE','garment':'HGPT_ORIGINAL_V1_SHORTS_CANDIDATE'}
SCRIPT='scripts/snapshot_original_v1_model_blender.py'
HELPER='scripts/original_v1_garment_evidence.py'


def capture(bpy,scope):
    if scope not in NAMES:raise ValueError('body or garment scope required')
    source=Path(bpy.data.filepath);manifest=source.with_suffix('.json')
    if not source.is_file() or not bpy.context.scene.get('hgpt_not_production'):raise ValueError('saved candidate-only scene required')
    sha=digest(source);data=json.loads(manifest.read_text(encoding='utf-8-sig'))
    if data.get('candidate_sha256')!=sha or data.get('candidate')!=source.name:raise ValueError('source manifest identity differs')
    contract=load_locked_rig(ROOT)
    rig=bpy.data.objects.get(contract['object_name']);mesh=bpy.data.objects.get(NAMES[scope])
    rig_issues=blender_armature_issues(rig,contract)
    if rig_issues:raise ValueError('locked rev2c rig required: '+'; '.join(rig_issues))
    if mesh is None or mesh.type!='MESH' or mesh.find_armature()!=rig:raise ValueError('owned mesh bound to locked rev2c rig required')
    coords=[list(v.co) for v in mesh.data.vertices]
    names={g.index:g.name for g in mesh.vertex_groups};deform={b.name for b in rig.data.bones if b.use_deform}
    weights=[{names[g.group]:g.weight for g in v.groups if names[g.group] in deform} for v in mesh.data.vertices]
    nondeform={name:[next((g.weight for g in v.groups if g.group==idx),0) for v in mesh.data.vertices] for idx,name in names.items() if name not in deform}
    if scope=='body':
        regions=json.loads(bpy.context.scene['hgpt_region_names']);labels=mesh.data.attributes['hgpt_region'].data
        labels=[regions[d.value] for d in labels]
    else:labels=['garment']*len(coords)
    quant=lambda p:tuple(round(float(x)/1e-6) for x in p)
    lookup={};pairs=[];ambiguous=[]
    for i,p in enumerate(coords):lookup.setdefault(quant(p),[]).append(i)
    for i,p in enumerate(coords):
        twin=lookup.get(quant((-p[0],p[1],p[2])),[])
        if len(twin)==1 and i<=twin[0]:pairs.append([i,twin[0]])
        elif len(twin)>1:ambiguous.append(i)
    rest=[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),
           'matrix':[list(row) for row in b.matrix_local],'use_deform':b.use_deform} for b in sorted(rig.data.bones,key=lambda x:x.name)]
    modifiers=[]
    for m in mesh.modifiers:
        row={'name':m.name,'type':m.type,'show_viewport':m.show_viewport,'show_render':m.show_render}
        if m.type=='MASK':row.update(vertex_group=m.vertex_group,invert_vertex_group=m.invert_vertex_group,mode=m.mode,threshold=m.threshold)
        if m.type=='ARMATURE':row.update(object=m.object.name if m.object else None,use_vertex_groups=m.use_vertex_groups,use_bone_envelopes=m.use_bone_envelopes,use_deform_preserve_volume=m.use_deform_preserve_volume)
        modifiers.append(row)
    result={'schema_version':2,'source_candidate':source.name,'candidate_sha256':sha,'rig_id':contract['identity'],
        'locked_rig':{'revision':contract['revision'],'rig_structure_sha256':contract['rig_structure_sha256'],
            'bone_count':contract['bone_count'],'deform_bone_count':contract['deform_bone_count'],
            'lock':contract['lock'],'payload':contract['payload']},
        'scene_unit_scale_length':bpy.context.scene.unit_settings.scale_length,'coordinate_space':'raw mesh local Blender coordinates in metres',
        'vertices':coords,'faces':[list(p.vertices) for p in mesh.data.polygons],'regions':labels,'weights':weights,
        'mirror_pairs':pairs,'ambiguous_mirror_vertex_ids':ambiguous,'left_x_sign':-1 if rig.data.bones['upperarm_l'].head_local.x<0 else 1,
        'mesh_matrix_world':[list(row) for row in mesh.matrix_world],'rig_matrix_world':[list(row) for row in rig.matrix_world],'rig_rest_bones':rest,
        'ignored_non_deform_groups':sorted(set(names.values())-deform),'bone_names':sorted(deform),'blender_version':bpy.app.version_string,
        'snapshot_script_sha256':digest(ROOT/SCRIPT),'snapshot_helper_sha256':digest(ROOT/HELPER),
        'mesh_object':mesh.name,'snapshot_scope':scope,'modifiers':modifiers,'non_deform_group_weights':nondeform,
        'source_candidate_manifest':{'file':manifest.name,'sha256':digest(manifest)},
        'source_git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'capture_command':list(sys.argv),'generated_utc':datetime.now(timezone.utc).isoformat(),
        'production_approved':False,'note':'Raw undeformed mesh/weights. Modifier inventory is partial; no evaluated clearance or dressed motion. Confirm index correspondence from operation history before change comparisons.'}
    ensure_finite(result)
    if digest(source)!=sha or digest(manifest)!=result['source_candidate_manifest']['sha256']:raise ValueError('source changed during capture')
    return result



def snapshot_locked_rig_issues(snapshot,contract):
    issues=[]
    if snapshot.get('rig_id')!=contract['identity']:issues.append('raw snapshot rig identity differs')
    rows=snapshot.get('rig_rest_bones')
    if not isinstance(rows,list):return issues+['raw snapshot rig-rest rows missing']
    hierarchy=sorted([{'name':str(r.get('name','')),'parent':r.get('parent')} for r in rows],key=lambda r:r['name'])
    if hierarchy!=contract['bones']:issues.append('raw snapshot locked rev2c hierarchy differs')
    deform=[r.get('name') for r in rows if r.get('use_deform') is True]
    if len(deform)!=contract['deform_bone_count']:issues.append('raw snapshot locked rev2c deform count differs')
    if sorted(snapshot.get('bone_names',[]))!=sorted(deform):issues.append('raw snapshot deform-bone inventory differs')
    locked=snapshot.get('locked_rig')
    if locked is not None:
        expected={'revision':contract['revision'],'rig_structure_sha256':contract['rig_structure_sha256'],
                  'bone_count':contract['bone_count'],'deform_bone_count':contract['deform_bone_count'],
                  'lock':contract['lock'],'payload':contract['payload']}
        if locked!=expected:issues.append('raw snapshot locked-rig receipt differs')
    return issues

def inspect_pair(body,garment):
    for s,scope in ((body,'body'),(garment,'garment')):
        validate(s)
        if s.get('production_approved',False) is not False:raise ValueError('raw snapshot cannot claim approval')
        if s.get('mesh_object')!=NAMES[scope] or s.get('snapshot_scope')!=scope:raise ValueError('mesh identity/scope differs')
        if not isinstance(s.get('modifiers'),list) or not isinstance(s.get('non_deform_group_weights'),dict):raise ValueError('modifier/coverage inventory required')
        for row in s['modifiers']:
            if not isinstance(row,dict) or not all(k in row for k in ('name','type','show_viewport','show_render')):raise ValueError('invalid modifier inventory')
            if row['type']=='MASK' and not all(k in row for k in ('vertex_group','invert_vertex_group')):raise ValueError('mask configuration missing')
        for values in s['non_deform_group_weights'].values():
            if len(values)!=len(s['vertices']) or any(type(v) not in (int,float) or v<0 for v in values):raise ValueError('raw coverage rows differ')
    if body['candidate_sha256']!=garment['candidate_sha256'] or body['source_candidate']!=garment['source_candidate']:raise ValueError('candidate identity differs between pair')
    for key in ('snapshot_script_sha256','snapshot_helper_sha256','blender_version'):
        if not body.get(key) or body[key]!=garment.get(key):raise ValueError('capture source/version differs')
    if (sorted(body['rig_rest_bones'],key=lambda b:b['name'])!=sorted(garment['rig_rest_bones'],key=lambda b:b['name']) or
        body['rig_matrix_world']!=garment['rig_matrix_world'] or body['left_x_sign']!=garment['left_x_sign'] or set(body['bone_names'])!=set(garment['bone_names'])):raise ValueError('rig identity differs')
    # Reuse existing raw-weight diagnostic semantics without claiming correspondence.
    weights=audit(garment,garment,{'before_candidate_sha256':garment['candidate_sha256'],'candidate_sha256':garment['candidate_sha256'],'index_correspondence_confirmed':False})['weights']
    weights['cross_side_status']='RAW_RIG_ALIGNED_X_DIAGNOSTIC'
    if garment['mesh_matrix_world']!=garment['rig_matrix_world']:
        weights['cross_side_vertex_ids']=None
        weights['cross_side_status']='UNRESOLVED_COORDINATE_FRAME'
    return {'schema_version':1,'status':'EVIDENCE_ONLY','candidate_sha256':body['candidate_sha256'],'phase_complete':False,'production_approved':False,
        'body_vertex_count':len(body['vertices']),'garment_vertex_count':len(garment['vertices']),'garment_face_count':len(garment['faces']),
        'body_matrix_world':body['mesh_matrix_world'],'garment_matrix_world':garment['mesh_matrix_world'],'garment_weights':weights,
        'body_coverage':{'mask_modifiers':[m for m in body['modifiers'] if m['type']=='MASK'],'non_deform_group_weights':body['non_deform_group_weights']},
        'garment_modifiers':garment['modifiers'],'unresolved_checks':['posed_clearance_and_intersections','dressed_motion_and_contact','bare_before_after_equivalence','garment_authoring_provenance','evaluated_modifier_configuration','shape_keys_custom_normals_and_full_modifier_settings','actual_review_images'],
        'limits':'Raw pair only. No body-to-garment correspondence, clearance, hidden-skin exemption, repair permission, Phase 7 PASS or approval inferred.'}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('body',type=Path);ap.add_argument('garment',type=Path)
    ap.add_argument('--candidate-manifest',type=Path,required=True);ap.add_argument('--json-out',type=Path,required=True);args=ap.parse_args()
    try:
        paths=[safe_path(ROOT,p.resolve().relative_to(ROOT).as_posix()) for p in (args.body,args.garment,args.candidate_manifest,args.json_out)]
        if len(set(paths))!=4 or paths[-1].exists():raise ValueError('output collision/alias; preserve evidence')
        body,garment,manifest=[json.loads(p.read_text(encoding='utf-8-sig')) for p in paths[:3]]
        result=inspect_pair(body,garment)
        contract=load_locked_rig(ROOT)
        for snapshot,label in ((body,'body'),(garment,'garment')):
            rig_issues=snapshot_locked_rig_issues(snapshot,contract)
            if rig_issues:raise ValueError(label+' snapshot is not locked rev2c: '+'; '.join(rig_issues))
        result['locked_rig']={'revision':contract['revision'],'rig_structure_sha256':contract['rig_structure_sha256'],
                              'bone_count':contract['bone_count'],'deform_bone_count':contract['deform_bone_count'],
                              'lock':contract['lock'],'payload':contract['payload']}
        if manifest.get('candidate_sha256')!=result['candidate_sha256'] or manifest.get('candidate')!=body['source_candidate']:raise ValueError('supplied candidate manifest differs')
        source=safe_path(ROOT,(paths[2].parent/manifest['candidate']).relative_to(ROOT).as_posix())
        result['local_blend_verification']='UNAVAILABLE'
        if source.exists():
            if not source.is_file() or digest(source)!=result['candidate_sha256']:raise ValueError('local candidate bytes differ')
            result['local_blend_verification']='VERIFIED'
        for s in (body,garment):
            for key,name in (('snapshot_script_sha256',SCRIPT),('snapshot_helper_sha256',HELPER)):
                if s[key]!=digest(ROOT/name):raise ValueError('capture script hash differs; use recorded source checkout')
            if s.get('source_candidate_manifest')!={'file':paths[2].name,'sha256':digest(paths[2])}:raise ValueError('capture manifest bytes differ')
        result['source_evidence']=[evidence(ROOT,p.relative_to(ROOT).as_posix()) for p in paths[:3]]+[evidence(ROOT,name) for name in (SCRIPT,HELPER,'scripts/audit_original_v1_changes.py')]
        result['command']=['python',*sys.argv];result['source_git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();result['generated_utc']=datetime.now(timezone.utc).isoformat()
        paths[-1].parent.mkdir(parents=True,exist_ok=True)
        with paths[-1].open('x',encoding='utf-8') as handle:handle.write(json.dumps(result,indent=2)+'\n')
        print('GARMENT RAW EVIDENCE WRITTEN — unresolved dressed checks remain');return 0
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as exc:print('STOP — '+str(exc));return 2

if __name__=='__main__':raise SystemExit(main())
