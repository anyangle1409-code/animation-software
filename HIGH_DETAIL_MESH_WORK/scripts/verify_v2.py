import json,struct,hashlib
from pathlib import Path
R=Path(r'C:\Users\Mark\Documents\animation-software\HIGH_DETAIL_MESH_WORK');S=next((R/'reference').iterdir());digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):
 b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),b[28+n:]
s,sb=load(S/'HOME_GYM_PT_GPT_MESH_HANDOFF/characters/HomeGymPT_Male_CORNER_FINAL_SHORTS.glb');v,vb=load(R/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v2.glb');bare,bb=load(R/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v2_BARE.glb')
assert all(s.get(k)==v.get(k) for k in ['nodes','skins','scenes','animations','materials','textures','images']);assert vb[:len(sb)]==sb
assert v['meshes'][1:]==s['meshes'][1:];assert vb==bb
expected=json.loads(json.dumps(v));del expected['nodes'][162]['mesh'];assert bare==expected
old=json.loads((R/'reports/final_integrity.json').read_text());assert all(digest(R/p)==v['sha256'] for p,v in old['artifacts'].items())
hashes=json.loads((R/'reports/reference_hashes.json').read_text());assert all(digest(S/p)==h for p,h in hashes.items());assert all(digest(p)==digest(R/'validation'/p.relative_to(S)) for p in (S/'src').rglob('*') if p.is_file())
report={'reference_files_unchanged':len(hashes),'v1_artifacts_unchanged':True,'production_source_copy_unchanged':True,'rig_nodes_skins_animations_exact':True,'original_binary_prefix_exact':True,'bare_difference':'Only shorts node mesh attachment removed; all body, rig and binary data identical','artifacts':{p.name:{'bytes':p.stat().st_size,'sha256':digest(p)} for p in R.glob('HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v2*') if p.suffix in ['.glb','.blend']}}
(R/'reports/final_integrity_v2.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
