"""READ ONLY native inventory. Run with --factory-startup --disable-autoexec.

blender --background --factory-startup --disable-autoexec --python-exit-code 1 \
  --python experiments/anatomical_muscles/inspect_blender.py -- COPY.blend SHA256 NEW_REPORT.json
No save operation, handlers, mesh edits, pose changes or generated attachment guesses.
Native execution has NOT been performed in the authoring environment.
"""
import hashlib
import json
from pathlib import Path
import sys
import bpy


def main():
    source,expected,output=sys.argv[sys.argv.index('--')+1:]
    source=Path(source); output=Path(output)
    if output.exists() or output.is_symlink() or output.resolve()==source.resolve():
        raise ValueError('Report output must be a new, separate file')
    before=hashlib.sha256(source.read_bytes()).hexdigest()
    if before!=expected: raise ValueError('Copy hash mismatch')
    bpy.ops.wm.open_mainfile(filepath=str(source.resolve()),use_scripts=False)
    rigs=[]; meshes=[]
    for obj in bpy.data.objects:
        if obj.type=='ARMATURE':
            rigs.append({'name':obj.name,'matrix_world':[list(row) for row in obj.matrix_world],
                         'bones':[{'id':b.name,'parent':b.parent.name if b.parent else None,
                                   'head':list(b.head_local),'tail':list(b.tail_local),
                                   'matrix_local':[list(row) for row in b.matrix_local]}
                                  for b in obj.data.bones]})
        elif obj.type=='MESH':
            meshes.append({'name':obj.name,'vertices':len(obj.data.vertices),'faces':len(obj.data.polygons),
                           'modifiers':[{'name':m.name,'type':m.type} for m in obj.modifiers],
                           'vertex_groups':[g.name for g in obj.vertex_groups],
                           'shape_keys':[k.name for k in obj.data.shape_keys.key_blocks] if obj.data.shape_keys else []})
    after=hashlib.sha256(source.read_bytes()).hexdigest()
    if before!=after: raise RuntimeError('Source changed')
    report={'status':'native_inventory_only','blender_version':bpy.app.version_string,
            'source_sha256':before,'source_unchanged':True,'rigs':rigs,'meshes':meshes,
            'attachment_validation':'NOT_RUN','deformation_validation':'NOT_RUN'}
    with output.open('x') as f: json.dump(report,f,indent=2)

if __name__=='__main__': main()
