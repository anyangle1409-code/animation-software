"""Read-only raw rest-mesh/weights snapshot from one verified ORIGINAL candidate.

blender --background --factory-startup <candidate.blend> --python-exit-code 1
 --python scripts/snapshot_original_v1_model_blender.py -- <new snapshot.json>
Never saves or renormalizes the Blend; no third-party Python dependencies.
"""
import hashlib
import json
import sys
from pathlib import Path
import bpy

args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if len(args)!=1:raise SystemExit('new snapshot JSON output path required')
out=Path(args[0])
if out.exists():raise SystemExit('STOP — snapshot output already exists')
source=Path(bpy.data.filepath)
if not source.is_file() or not bpy.context.scene.get('hgpt_not_production'):raise SystemExit('candidate-only snapshot requires a saved candidate')
rig=bpy.data.objects.get('HGPT_CANONICAL_V4_ORIGINAL')
if rig is None or len(rig.data.bones)!=63:raise SystemExit('canonical 63-bone rig required')
body=next(o for o in bpy.data.objects if o.type=='MESH' and o.find_armature()==rig and 'SHORTS' not in o.name)
manifest=source.with_suffix('.json')
sha=hashlib.sha256(source.read_bytes()).hexdigest()
if not manifest.is_file() or json.loads(manifest.read_text(encoding='utf-8-sig')).get('candidate_sha256')!=sha:raise SystemExit('source candidate does not match manifest')
regions=json.loads(bpy.context.scene['hgpt_region_names']);labels=body.data.attributes['hgpt_region'].data
coords=[list(v.co) for v in body.data.vertices]
names={g.index:g.name for g in body.vertex_groups};deform={b.name for b in rig.data.bones if b.use_deform}
weights=[{names[g.group]:g.weight for g in v.groups if names[g.group] in deform} for v in body.data.vertices]
# Exact quantized coordinate twins, never nearest-surface projection or weight transfer.
quant=lambda p:tuple(round(float(x)/1e-6) for x in p)
lookup={};pairs=[];ambiguous=[]
for i,p in enumerate(coords):lookup.setdefault(quant(p),[]).append(i)
for i,p in enumerate(coords):
    twin=lookup.get(quant((-p[0],p[1],p[2])),[])
    if len(twin)==1 and i<=twin[0]:pairs.append([i,twin[0]])
    elif len(twin)>1:ambiguous.append(i)
x=rig.data.bones['upperarm_l'].head_local.x
result={'schema_version':1,'source_candidate':source.name,'candidate_sha256':sha,
        'rig_id':'hgpt_canonical_v4_original','coordinate_space':'raw mesh local Blender coordinates in metres',
        'vertices':coords,'faces':[list(p.vertices) for p in body.data.polygons],
        'regions':[regions[d.value] for d in labels],'weights':weights,
        'mirror_pairs':pairs,'ambiguous_mirror_vertex_ids':ambiguous,'left_x_sign':-1 if x<0 else 1,
        'mesh_matrix_world':[list(row) for row in body.matrix_world],
        'bone_names':sorted(deform),'blender_version':bpy.app.version_string,
        'snapshot_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'note':'Raw weights; index correspondence must be explicitly confirmed by operation history before change comparison.'}
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('MODEL SNAPSHOT',source.name,sha,out)
