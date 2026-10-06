"""Rebuild an r95-equivalent working .blend: committed r82 (identical rest mesh/rig/metadata, quads, region attribute, shorts)
+ r95's skin weights and all six corrective shape keys from the identity-verified r95 BARE GLB export (vertex-index transfer)."""
import sys, json, bpy, numpy as np
argv = sys.argv[sys.argv.index('--')+1:]
r82, glb, out = argv
# 1. read r95 GLB data
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb, bone_heuristic='BLENDER')
g = next(o for o in bpy.data.objects if o.type=='MESH' and o.find_armature())
n = len(g.data.vertices)
gnames = [vg.name for vg in g.vertex_groups]
W = np.zeros((n, len(gnames)))
for v in g.data.vertices:
    for e in v.groups: W[v.index, e.group] = e.weight
basis = np.empty(n*3); g.data.shape_keys.key_blocks[0].data.foreach_get('co', basis)
keys = {}
for kb in g.data.shape_keys.key_blocks[1:]:
    a = np.empty(n*3); kb.data.foreach_get('co', a); keys[kb.name] = (a - basis)
# 2. open r82 and transfer
bpy.ops.wm.open_mainfile(filepath=r82)
rig = bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
body = next(o for o in bpy.data.objects if o.type=='MESH' and o.find_armature()==rig and 'SHORTS' not in o.name)
me = body.data
assert len(me.vertices) == n
rb = np.empty(n*3); me.vertices.foreach_get('co', rb)
assert np.abs(rb-basis).max() < 1e-5, np.abs(rb-basis).max()
for vg in list(body.vertex_groups):
    if vg.name not in gnames: print('non-bone group in r82 (kept unchanged):', vg.name)
for vg in body.vertex_groups:
    if vg.name in gnames: vg.remove(list(range(n)))
for j, name in enumerate(gnames):
    vg = body.vertex_groups.get(name) or body.vertex_groups.new(name=name)
    nz = np.nonzero(W[:, j] > 0)[0]
    for i in nz: vg.add([int(i)], float(W[i, j]), 'REPLACE')
# shape keys: replace with r95's
if me.shape_keys:
    body.active_shape_key_index = 0
    body.shape_key_clear()
body.shape_key_add(name='Basis', from_mix=False)
for name, delta in keys.items():
    kb = body.shape_key_add(name=name, from_mix=False)
    kb.data.foreach_set('co', basis + delta); kb.value = 0.0
sc = bpy.context.scene
sc['hgpt_candidate_revision'] = 'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r95_RECONSTRUCTED'
sc['hgpt_candidate_parent_sha256'] = '6dfcd85a65e77fd832c9eb91cbe7eda04c81dc635201d260d6cbcf0eee508984'
sc['hgpt_r95_reconstruction'] = json.dumps({'base': 'r82 .blend (identical rest mesh, rig rev2c, metadata)', 'weights_and_keys_from': 'HomeGymPT_Male_ORIGINAL_v1_CANDIDATE_r95_BARE.glb', 'glb_sha256': 'c4b8e388e624a4a3d22510b40c1fc45017b3374b1ff9de2cae79f2dbb0797c85', 'r95_blend_sha256': '8a39a22d3fec36f82c1cd53f6d0a976748a8cf97de14d81e62b5789178403bdd', 'note': 'GLB weights are limited to 4 influences per vertex, as exported for runtime'})
sc['hgpt_shoulder_corrective'] = json.dumps({'theta0_deg': 40.0, 'theta1_deg': 150.0, 'keys': {'l': 'HGPT_SHOULDER_CORR_L', 'r': 'HGPT_SHOULDER_CORR_R'}})
sc['hgpt_flexion_corrective'] = json.dumps({'theta0_deg': 45.0, 'theta1_deg': 120.0, 'keys': {'l': 'HGPT_SHOULDER_FLEX_L', 'r': 'HGPT_SHOULDER_FLEX_R'}})
sc['hgpt_scapular_corrective'] = json.dumps({'u0_deg': 25.0, 'u1_deg': 75.0, 'keys': {'l': 'HGPT_SHOULDER_SCAP_L', 'r': 'HGPT_SHOULDER_SCAP_R'}})
print('groups', len(body.vertex_groups), 'keys', [k.name for k in me.shape_keys.key_blocks])
bpy.ops.wm.save_as_mainfile(filepath=out, compress=False)
