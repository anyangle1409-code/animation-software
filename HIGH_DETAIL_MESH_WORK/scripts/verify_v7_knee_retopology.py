"""Verify V7 knee-only changes and zero posed UV-seam gap."""
import hashlib,io,json,os,struct,subprocess,tarfile
from pathlib import Path
import numpy as np
from scripts.candidate_quick_check import load_glb,accessor,topology_stats

root=Path(__file__).resolve().parents[1]
base=root/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.glb'
candidate=root/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v7_knee_retopology.glb'
bare=root/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v7_knee_retopology_BARE.glb'
blend=root/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v7_knee_retopology.blend'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(base)=='ff39e07735697d5423968a8ec1c05f2c6c68fced0d757ea1b4047096bc7a5306'
bd,bb=load_glb(base);cd,cb=load_glb(candidate);dd,db=load_glb(bare)
assert bd==cd
assert cb==db
for field in ('nodes','skins','scenes','animations','materials','textures','images','samplers'):
    assert bd.get(field)==cd.get(field),field
bp=bd['meshes'][0]['primitives'][0];cp=cd['meshes'][0]['primitives'][0]
for attr in bp['attributes']:
    if attr not in ('POSITION','NORMAL'):
        assert np.array_equal(accessor(bd,bb,bp['attributes'][attr]),accessor(cd,cb,cp['attributes'][attr])),attr
assert np.array_equal(accessor(bd,bb,bp['indices']),accessor(cd,cb,cp['indices']))
old=accessor(bd,bb,bp['attributes']['POSITION']).astype(float)
new=accessor(cd,cb,cp['attributes']['POSITION']).astype(float)
changed=np.flatnonzero(np.any(old!=new,axis=1))
assert len(changed)>0
assert np.all((np.abs(old[changed,0])>.025)&(np.abs(old[changed,0])<.28))
assert np.all((old[changed,1]>.40)&(old[changed,1]<.68))
assert np.linalg.norm(new-old,axis=1).max()<.026
stats=topology_stats(cd,cb)
assert stats['degenerate_triangles']==0 and stats['nonmanifold_edges_gt2']==0
seams=json.loads((root/'reports/knee_seam_v5.json').read_text())['knees']
max_rest_gap=0.
for side in seams.values():
    a,b=side['paths'];max_rest_gap=max(max_rest_gap,float(np.linalg.norm(new[a]-new[b],axis=1).max()*1000))
assert max_rest_gap<1e-4
poses={}
for file in sorted((root/'reports/poses_v7_knee_retopology').glob('*_candidate.json')):
    points=np.asarray(json.loads(file.read_text())['meshes'][0]['positions'])
    poses[file.stem]={}
    for side,entry in seams.items():
        a,b=entry['paths'];poses[file.stem][side]=float(np.linalg.norm(points[a]-points[b],axis=1).max()*1000)
assert len(poses)==28,len(poses)
max_pose_gap=max(v for p in poses.values() for v in p.values())
assert max_pose_gap<1e-4,max_pose_gap
hashes=json.loads((root/'reports/reference_hashes.json').read_text())
reference_root=root/'reference'
ref=next(reference_root.iterdir(),None) if reference_root.is_dir() else None
use_local=ref is not None and not os.environ.get('VERIFY_V7_FORCE_GIT_ARCHIVE') and all((ref/name).is_file() for name in hashes)
if use_local:
    for name,digest in hashes.items():assert sha(ref/name)==digest,name
    reference_source='local pinned archive'
else:
    archive=subprocess.check_output(['git','archive','--format=tar','f9cca7c34880a2c5e30b63a42c762d7fd99205e8'],cwd=root.parent)
    checked=set()
    with tarfile.open(fileobj=io.BytesIO(archive),mode='r:') as stream:
        for member in stream:
            name=member.name.replace('/','\\')
            if name in hashes and member.isfile():
                content=stream.extractfile(member).read()
                raw_hash=hashlib.sha256(content).hexdigest()
                normalized_hash=hashlib.sha256(content.replace(b'\r\n',b'\n')).hexdigest()
                assert hashes[name] in (raw_hash,normalized_hash),name
                checked.add(name)
    assert checked==set(hashes),len(checked)
    reference_source='pinned Git archive f9cca7c'
report={'v6_sha256_unchanged':sha(base),'pinned_source_files_unchanged':len(hashes),
        'reference_source':reference_source,
        'glb_document_equal_to_v6':True,'uv_skin_weights_indices_equal_to_v6':True,
        'changed_position_vertices':len(changed),'max_rest_move_mm':float(np.linalg.norm(new-old,axis=1).max()*1000),
        'changed_positions_knee_region_only':True,'body_stats':stats,
        'paired_seam_rest_gap_mm':max_rest_gap,'saved_pose_count':len(poses),'max_paired_seam_pose_gap_mm':max_pose_gap,
        'artifacts':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in (candidate,bare,blend)}}
(root/'reports/final_integrity_v7_knee_retopology.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
