import sys, json, hashlib, bpy
argv = sys.argv[sys.argv.index('--')+1:]
src, out, params, solver = argv[:4]
geo_receipt = argv[4] if len(argv) > 4 else None
bpy.ops.wm.open_mainfile(filepath=src)
sc = bpy.context.scene
disabled = {k: sc[k] for k in ('hgpt_shoulder_corrective', 'hgpt_flexion_corrective', 'hgpt_scapular_corrective') if k in sc}
for k in disabled: del sc[k]
sc['hgpt_disabled_r95_corrective_specs'] = json.dumps(disabled)
sc['hgpt_correctives_state'] = 'r95 shoulder corrective shape keys retained at value 0 with their driver configs removed: r98 is a weights-only foundation candidate (no corrective fitted)'
sc['hgpt_candidate_revision'] = 'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r98'
sc['hgpt_candidate_parent_sha256'] = '8a39a22d3fec36f82c1cd53f6d0a976748a8cf97de14d81e62b5789178403bdd'
sc['hgpt_candidate_parent_export_sha256'] = 'c4b8e388e624a4a3d22510b40c1fc45017b3374b1ff9de2cae79f2dbb0797c85'
sc['hgpt_rig_revision'] = 'rev2e_scapula_ac_pivot_gh_helpers'
sh = lambda p: hashlib.sha256(open(p,'rb').read()).hexdigest()
sc['hgpt_weight_solution'] = json.dumps({'solver': 'scripts/r97/solve_weights.py', 'solver_sha256': sh(solver), 'params': 'ORIGINAL_V1_WORK/candidates/r98/r98_weight_solve_params.json', 'params_sha256': sh(params), 'method': 'mirror-symmetric cotangent-Laplacian harmonic solve on the surface between anatomical anchors, trunk/helper/humerus split, <=4 influences'})
sc['hgpt_not_production'] = True
sc['hgpt_r98_parent_candidate'] = json.dumps({'revision': 'r97', 'sha256': '8b2fbe50781dfcf9123178615efc926945847959ed2b897def920f0b3c48962f', 'build': 'rebuilt from r95 working reconstruction with r97 mechanics; r97 file not modified'})
if geo_receipt: sc['hgpt_r98_topology_rest_receipt_file'] = open(geo_receipt).read()
body = next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('HGPT_ORIGINAL_V1_BODY'))
for kb in body.data.shape_keys.key_blocks[1:]: kb.value = 0.0
bpy.ops.wm.save_as_mainfile(filepath=out, compress=False)
print('saved', out)
