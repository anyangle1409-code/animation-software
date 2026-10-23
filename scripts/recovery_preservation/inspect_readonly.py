"""Read-only preservation inspection; never saves any Blender file."""
import sys,os,json,hashlib,runpy,shutil,tempfile
from pathlib import Path
import bpy,numpy as np

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
source=Path(sys.argv[1]).resolve()
expected=sys.argv[2]
verifier=Path(sys.argv[3]).resolve()
out=Path(sys.argv[4]).resolve()
assert not out.exists(), 'Inspection destination must be new'
out.mkdir(parents=True)
assert sha(source)==expected,'Input SHA256 mismatch'
copydir=Path(tempfile.mkdtemp(prefix='preservation_readonly_copy_',dir=out))
copy=copydir/source.name
shutil.copy2(source,copy)
copy.chmod(0o444)
assert sha(copy)==expected
bpy.context.preferences.filepaths.use_scripts_auto_execute=False
sys.argv=[str(verifier),'--',str(copy),'none',str(out/'unused_expected.json'),str(out/'claude_verifier.json')]
runpy.run_path(str(verifier),run_name='__main__')
body=bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
me=body.data
me.calc_loop_triangles()
coords=np.empty(len(me.vertices)*3,dtype=np.float64)
me.vertices.foreach_get('co',coords)
basis=np.empty(len(me.vertices)*3,dtype=np.float64)
me.shape_keys.key_blocks[0].data.foreach_get('co',basis)
polygons=[list(p.vertices) for p in me.polygons]
result={
 'model_file':source.name,'source_sha256_before':expected,
 'source_sha256_after':sha(source),'inspection_copy_sha256_after':sha(copy),
 'saved_by_bpy_data_version':list(bpy.data.version),'running_blender':bpy.app.version_string,
 'vertices':len(me.vertices),'polygons':len(me.polygons),'native_loop_triangles':len(me.loop_triangles),
 'vertex_groups':len(body.vertex_groups),'vertex_group_names':[g.name for g in body.vertex_groups],
 'shape_keys':len(me.shape_keys.key_blocks),'shape_key_names':[k.name for k in me.shape_keys.key_blocks],
 'rig_name':'HGPT_CANONICAL_V4_ORIGINAL',
 'rig_bones':len(bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL'].data.bones),
 'modifiers':[{'name':m.name,'type':m.type,'object':getattr(getattr(m,'object',None),'name',None),
               'use_deform_preserve_volume':getattr(m,'use_deform_preserve_volume',None)} for m in body.modifiers],
 'basis_hash_definition':'shape-key index0 coordinates in existing vertex order, float64 little-endian C bytes, local space; no quantization; topology separately hashed',
 'basis_coordinates_float64_le_sha256':hashlib.sha256(basis.astype('<f8').tobytes()).hexdigest(),
 'mesh_coordinates_equal_basis':bool(np.array_equal(coords,basis)),
 'polygons_ordered_json_sha256':hashlib.sha256(json.dumps(polygons,separators=(',',':')).encode()).hexdigest(),
 'archive_equivalence':'FAIL / NOT_ESTABLISHED','anatomical_approval':'NOT_GRANTED','saved':False,
}
assert result['source_sha256_after']==expected==result['inspection_copy_sha256_after'],'Inspection changed bytes'
assert result['vertex_groups']==77 and result['shape_keys']==79,'Inventory mismatch'
(out/'inspection.json').write_text(json.dumps(result,indent=2)+'\n')
# Remove only this new inspection copy after checking it; no source files are touched.
# Keep it read-only in the ephemeral job; reports only are uploaded.
print(json.dumps(result),flush=True)
