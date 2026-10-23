"""Preserve recovered bytes in per-model artifacts and expose all archive discrepancies.
No source writes, model edits, guard changes or anatomical acceptance.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys

MODELS={'W8':'W8/body_v2.blend','V14':'V14/body_v2_legs.blend','R120':'R120/body_v2_rebuilt.blend'}


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def differences(a,b,path=''):
    if isinstance(a,dict) and isinstance(b,dict):
        result=[]
        for key in sorted(set(a)|set(b)):
            if key not in a or key not in b:result.append({'path':path+'/'+key,'archive':a.get(key),'rebuilt':b.get(key),'kind':'missing_key'})
            else:result.extend(differences(a[key],b[key],path+'/'+key))
        return result
    if a!=b:return [{'path':path,'archive':a,'rebuilt':b}]
    return []


def package(root,out,repo=None):
    out.mkdir(parents=True,exist_ok=False)
    report={'status':'recovered_candidates_archive_mismatch','anatomical_approval':'NOT_GRANTED',
            'PT_MODEL_VERSION':'1.0','models':{},'missing':[],
            'source_run':39918805189,'native_movement_status':'blocked_before_pose_by_67_vs_77_bone_contract',
            'muscle_attachment':'BLOCKED — archive/structure gates not passed'}
    evidence=out/'evidence';evidence.mkdir()
    for name in ('verify','ci'):
        if (root/name).exists():shutil.copytree(root/name,evidence/name)
    for name in ('MANIFEST.sha256','MANIFEST_HEADER.json'):
        if (root/name).exists():shutil.copyfile(root/name,evidence/('original_'+name))
    for model,relative in MODELS.items():
        source=root/relative
        if not source.exists():report['missing'].append(relative);continue
        before=sha(source); folder=out/model;folder.mkdir()
        shutil.copyfile(source,folder/source.name)
        if sha(folder/source.name)!=before or sha(source)!=before:raise RuntimeError('Source/copy integrity mismatch')
        report['models'][model]={'file':source.name,'bytes':source.stat().st_size,'sha256':before,
                                 'status':'EXPERIMENTAL' if model=='R120' else 'UNVERIFIED_RECONSTRUCTION'}
        (folder/'SHA256SUMS.txt').write_text(f'{before}  {source.name}\n')
        (folder/'README.txt').write_text('Recovered candidate. Archive verification failed; no anatomy or production approval. Preserve source and validate SHA256SUMS.txt before use. R120 is experimental.\n')
        for image in (root/model).rglob('*.png'):
            target=evidence/'renders'/model/image.relative_to(root/model);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(image,target)
        for name in ('body_v2_report.json','skeleton_edits.json','legs_v2_report.json','rebuild_report.json'):
            if (root/model/name).exists():
                target=evidence/'model_reports'/model/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/model/name,target)
    if repo:
        archive=repo/'review-assets/body_v2'
        comparisons=[('W8','skeleton_edits.json','draft_v13s_standing'),('W8','body_v2_report.json','draft_v13s_standing'),('V14','legs_v2_report.json','draft_v14b_torso')]
        full={}
        for model,name,tag in comparisons:
            a=archive/tag/name;b=root/model/name
            if a.exists() and b.exists():full[model+'/'+name]=differences(json.loads(a.read_text()),json.loads(b.read_text()))
        (evidence/'all_archive_json_discrepancies.json').write_text(json.dumps(full,indent=2)+'\n')
        for tag in ('draft_v13s_standing','draft_v14b_torso'):
            target=evidence/'archived_renders'/tag;target.mkdir(parents=True,exist_ok=True)
            for image in (archive/tag).glob('skin_stand_*.jpg'):shutil.copyfile(image,target/image.name)
    (evidence/'ACCESS_RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
    (evidence/'README.md').write_text('# Recovered candidates — verification incomplete\n\nActual Blender files and renders were produced. Archive differences remain failed. W8 offset maximum difference is 3.59286 mm against 0.01 mm; proportion maximum difference 0.837573 mm. v14 has 238,065 vertices against archived 238,067. All exact JSON differences are in all_archive_json_discrepancies.json (no tolerance or causal inference applied). Native inventories succeeded, but recovered-model movement setup fails the older 67-bone guard on the 77-bone rig before posing. This is not movement acceptance or a proven deformation defect. Muscle staging remains blocked.\n\nThe original combined artifact exceeds the connector 512 MiB download cap. Separate model artifacts preserve exact bytes and hashes so Claude and ChatGPT can retrieve them. Production assets and PT_MODEL_VERSION 1.0 are unchanged.\n')
    return report

if __name__=='__main__':
    root,out=map(Path,sys.argv[1:3]);repo=Path(sys.argv[3]) if len(sys.argv)>3 else None
    print(json.dumps(package(root,out,repo),indent=2))
