#!/usr/bin/env python3
"""Candidate-isolated export identity, receipt verification and optional laptop capture."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import subprocess
import sys
from original_v1_production_control import ROOT,CAND,build,digest,evidence,ensure_finite
from audit_original_v1_candidate_glbs import parse_glb,audit_candidate_set
from verify_original_v1_production_promotion import safe_path

SETTINGS={'export_format':'GLB','use_selection':True,'export_apply':True,'export_skins':True,
          'export_animations':False,'export_yup':True,'export_texcoords':False,
          'export_materials':'EXPORT','export_extras':True}
BODY='HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE'
SHORTS='HGPT_ORIGINAL_V1_SHORTS_CANDIDATE'
SCRIPT='scripts/export_original_v1_candidate_glb_blender.py'
RIG_LOCK='ORIGINAL_V1_WORK/SKELETON_MOTION_LOCK_rev2_forearm_twist_only.json'
RIG_PAYLOAD='ORIGINAL_V1_WORK/hgpt_canonical_v4_original_rev2c.json'


def locked_rig(root):
    lock_path=root/RIG_LOCK;payload_path=root/RIG_PAYLOAD
    lock=json.loads(lock_path.read_text(encoding='utf-8-sig'));rig=lock['rig']
    if rig.get('payload',{}).get('path')!=RIG_PAYLOAD or digest(payload_path)!=rig.get('payload',{}).get('sha256'):
        raise ValueError('locked rev2c rig payload identity differs')
    payload=json.loads(payload_path.read_text(encoding='utf-8-sig'))
    if (payload.get('identity')!=rig.get('identity') or payload.get('bone_count')!=rig.get('bone_count') or
        payload.get('rig_structure_sha256')!=rig.get('rig_structure_sha256')):
        raise ValueError('locked rev2c rig payload contract differs')
    return {'identity':rig['identity'],'revision':rig['revision'],'bone_count':rig['bone_count'],
        'deform_bone_count':rig['deform_bone_count'],'rig_structure_sha256':rig['rig_structure_sha256'],
        'lock':evidence(root,RIG_LOCK),'payload':evidence(root,RIG_PAYLOAD)}


def local(root,path):
    return safe_path(root,Path(path).resolve().relative_to(root.resolve()).as_posix())


def filenames(revision):
    if not re.fullmatch(r'r\d+',revision):raise ValueError('numbered candidate revision required')
    return {v:f'HomeGymPT_Male_ORIGINAL_v1_CANDIDATE_{revision}_{v.upper()}.glb' for v in ('bare','dressed')}


def plan(root,candidate,manifest,out,revision):
    candidate,manifest,out=[local(root,p) for p in (candidate,manifest,out)]
    if out.exists():raise ValueError('output folder already exists; preserve historical/partial exports')
    data=json.loads(manifest.read_text(encoding='utf-8-sig'));ensure_finite(data)
    if manifest!=candidate.with_suffix('.json') or data.get('candidate')!=candidate.name:
        raise ValueError('candidate source filename/manifest differs')
    if not re.search(r'(?:^|_)'+re.escape(revision)+r'\.blend$',candidate.name):raise ValueError('candidate filename revision differs')
    sha=data.get('candidate_sha256')
    if not re.fullmatch('[0-9a-f]{64}',str(sha)) or digest(candidate)!=sha:raise ValueError('candidate source hash differs')
    return {'candidate_revision':revision,'candidate_sha256':sha,'source_candidate':evidence(root,candidate.relative_to(root).as_posix()),
        'candidate_manifest':evidence(root,manifest.relative_to(root).as_posix()),'output_directory':out.relative_to(root).as_posix(),
        'files':filenames(revision)}


def bound_glb(path,sha,revision,variant):
    document,_=parse_glb(path)
    meshes=[n for n in document.get('nodes',[]) if n.get('mesh') is not None]
    expected={BODY}|({SHORTS} if variant=='dressed' else set())
    if len(meshes)!=len(expected) or {n.get('name') for n in meshes}!=expected:raise ValueError('export mesh selection differs: '+variant)
    for node in meshes:
        extras=node.get('extras',{})
        if (extras.get('hgpt_export_source_candidate_sha256')!=sha or
            extras.get('hgpt_export_candidate_revision')!=revision or
            extras.get('hgpt_export_production_approved') is not False):raise ValueError('GLB candidate extras are unbound or claim approval')


def record(root,p,blender_version,git_commit,script_sha,settings):
    source=safe_path(root,p['source_candidate']['path']);manifest=safe_path(root,p['candidate_manifest']['path'])
    if digest(source)!=p['candidate_sha256'] or digest(manifest)!=p['candidate_manifest']['sha256']:
        raise ValueError('source bytes changed during export; preserve partial output')
    if not isinstance(blender_version,str) or not blender_version.strip() or not re.fullmatch('[0-9a-f]{40}',git_commit):raise ValueError('actual Blender version/source commit required')
    if digest(root/SCRIPT)!=script_sha:raise ValueError('export script source differs')
    if settings!=SETTINGS:raise ValueError('export settings differ from candidate protocol')
    exports={}
    for variant,name in p['files'].items():
        path=root/p['output_directory']/name;bound_glb(path,p['candidate_sha256'],p['candidate_revision'],variant)
        exports[variant]={'file':name,'bytes':path.stat().st_size,'sha256':digest(path),
            'candidate_sha256':p['candidate_sha256'],'dressed':variant=='dressed'}
    rig=locked_rig(root)
    return {'schema_version':2,'stage':'candidate review export (not production)','rig':'hgpt_canonical_v4_original',
        'rig_revision':rig['revision'],'rig_structure_sha256':rig['rig_structure_sha256'],
        'rig_bone_count':rig['bone_count'],'rig_deform_bone_count':rig['deform_bone_count'],
        'rig_lock':rig['lock'],'rig_payload':rig['payload'],
        'candidate_revision':p['candidate_revision'],'candidate_sha256':p['candidate_sha256'],
        'source_candidate':p['source_candidate'],'candidate_manifest':p['candidate_manifest'],
        'output_directory':p['output_directory'],'exports':exports,'export_settings':dict(settings),
        'export_script':{'path':SCRIPT,'sha256':script_sha},'blender_version':blender_version,
        'source_git_commit':git_commit,'generated_utc':datetime.now(timezone.utc).isoformat(),
        'pose_position':'REST','exporter':'Blender bundled io_scene_gltf2',
        'production_approved':False,'visual_review_available':False,
        'limits':'Capture identity only. Structural, anatomy, dressed deformation, real runtime and final owner gates remain separate.'}


def verify(root,manifest_path):
    manifest_path=local(root,manifest_path);data=json.loads(manifest_path.read_text(encoding='utf-8-sig'));ensure_finite(data)
    if (data.get('schema_version')!=2 or data.get('stage')!='candidate review export (not production)' or
        data.get('rig')!='hgpt_canonical_v4_original' or data.get('production_approved') is not False or data.get('pose_position')!='REST'):
        raise ValueError('candidate export identity/schema differs; historical exports remain unchanged')
    locked=locked_rig(root)
    if (data.get('rig_revision')!=locked['revision'] or data.get('rig_structure_sha256')!=locked['rig_structure_sha256'] or
        data.get('rig_bone_count')!=locked['bone_count'] or data.get('rig_deform_bone_count')!=locked['deform_bone_count'] or
        data.get('rig_lock')!=locked['lock'] or data.get('rig_payload')!=locked['payload']):
        raise ValueError('candidate export is not bound to the locked rev2c rig')
    sha=data['candidate_sha256'];revision=data['candidate_revision'];names=filenames(revision)
    if not re.fullmatch('[0-9a-f]{64}',str(sha)):raise ValueError('invalid candidate SHA')
    if data.get('export_settings')!=SETTINGS or any(type(data['export_settings'][k]) is not type(v) for k,v in SETTINGS.items()):raise ValueError('export settings differ')
    if not isinstance(data.get('blender_version'),str) or not data['blender_version'].strip() or not re.fullmatch('[0-9a-f]{40}',str(data.get('source_git_commit',''))):raise ValueError('capture version/source commit required')
    stamp=datetime.fromisoformat(data['generated_utc'].replace('Z','+00:00'))
    if stamp.tzinfo is None:raise ValueError('capture timestamp timezone required')
    for key in ('candidate_manifest','export_script'):
        ref=data[key];path=safe_path(root,ref['path'])
        if digest(path)!=ref['sha256']:raise ValueError(key+' source hash differs')
    candidate=safe_path(root,data['source_candidate']['path']);source_manifest=safe_path(root,data['candidate_manifest']['path'])
    source=json.loads(source_manifest.read_text(encoding='utf-8-sig'))
    if (source.get('candidate_sha256')!=sha or data['source_candidate']['sha256']!=sha or
        source.get('candidate')!=candidate.name or candidate.with_suffix('.json')!=source_manifest or
        not re.search(r'(?:^|_)'+re.escape(revision)+r'\.blend$',candidate.name)):raise ValueError('candidate source identity differs')
    local_status='UNAVAILABLE'
    if candidate.exists():
        if not candidate.is_file() or digest(candidate)!=sha:raise ValueError('local candidate source hash differs')
        local_status='VERIFIED'
    if safe_path(root,data['output_directory'])!=manifest_path.parent:raise ValueError('export directory differs')
    if set(data.get('exports',{}))!={'bare','dressed'}:raise ValueError('exact bare/dressed exports required')
    refs=[]
    for variant,name in names.items():
        entry=data['exports'][variant]
        if entry.get('file')!=name or entry.get('candidate_sha256')!=sha or entry.get('dressed') is not (variant=='dressed'):
            raise ValueError('revision/variant export entry differs')
        path=manifest_path.parent/name
        if type(entry.get('bytes')) is not int or path.stat().st_size!=entry['bytes'] or digest(path)!=entry['sha256']:raise ValueError('export bytes/hash differ')
        bound_glb(path,sha,revision,variant);refs.append(evidence(root,path.relative_to(root).as_posix()))
    return {'schema_version':1,'status':'EXPORT_IDENTITY_VERIFIED','candidate_revision':revision,'candidate_sha256':sha,
        'local_blend_verification':local_status,'source_evidence':[evidence(root,manifest_path.relative_to(root).as_posix()),data['candidate_manifest'],data['export_script'],*refs],
        'production_approved':False,'visual_review_available':False,
        'note':'Export identity only; no production/anatomy/dressed/runtime approval. Missing local Blend is reported explicitly.'}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('revision');ap.add_argument('--out-dir',required=True,type=Path)
    ap.add_argument('--capture',action='store_true');ap.add_argument('--json-out',type=Path);args=ap.parse_args()
    try:
        out=local(ROOT,args.out_dir);receipt=local(ROOT,args.json_out) if args.json_out else None
        if receipt and receipt.exists():raise ValueError('verification output already exists; preserve it')
        reserved={out/'CANDIDATE_GLB_EXPORT.json',*(out/name for name in filenames(args.revision).values())}
        if receipt in reserved:raise ValueError('verification output aliases an exported file or capture manifest')
        if args.capture:
            state,_=build(ROOT)
            if args.revision!=state['current_candidate'] or state['candidate_state']=='rejected':raise ValueError('latest complete non-rejected candidate required')
            candidate=ROOT/CAND/f'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{args.revision}.blend'
            candidate_manifest=candidate.with_suffix('.json');plan(ROOT,candidate,candidate_manifest,out,args.revision)
            from original_v1_session_preflight import blender_path,run
            start_head=run(['git','rev-parse','HEAD'])
            subprocess.run([sys.executable,'scripts/original_v1_session_preflight.py','--evidence-only'],cwd=ROOT,check=True)
            blender=blender_path()
            if not blender:raise ValueError('Blender unavailable after preflight')
            subprocess.run([str(blender),'--background','--factory-startup',str(candidate),'--python-exit-code','1',
                '--python',SCRIPT,'--','--out-dir',str(out),'--candidate-manifest',str(candidate_manifest),'--revision',args.revision],cwd=ROOT,check=True)
            branch=state['branch'];head=run(['git','rev-parse','HEAD'])
            live=run(['git','ls-remote','--exit-code','origin','refs/heads/'+branch]).split()[0]
            if head!=start_head or head!=live:raise ValueError('local/live branch advanced during export; preserve output and reconcile')
        manifest=out/'CANDIDATE_GLB_EXPORT.json';result=verify(ROOT,manifest)
        if result['candidate_revision']!=args.revision:raise ValueError('requested export revision differs')
        structural=audit_candidate_set(manifest,ROOT/RIG_PAYLOAD)
        result['structural_audit']=structural
        if receipt:
            receipt.parent.mkdir(parents=True,exist_ok=True)
            with receipt.open('x',encoding='utf-8') as handle:handle.write(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2));return 0 if structural['pass'] else 1
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as exc:
        print('STOP — '+str(exc));return 2

if __name__=='__main__':raise SystemExit(main())
