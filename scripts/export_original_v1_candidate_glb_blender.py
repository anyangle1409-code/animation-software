"""Export verified ORIGINAL candidates to a NEW directory; never save the Blend.

Use RUN_ORIGINAL_V1_CANDIDATE_EXPORT.bat <rN> <fresh repository output directory>.
Direct Blender use requires --out-dir, --candidate-manifest and --revision.
Historical no-argument/shared-filename export is deliberately refused.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
import addon_utils
import bpy

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from original_v1_export_evidence import BODY,SHORTS,SCRIPT,SETTINGS,plan,record
from original_v1_production_control import build,digest


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out-dir',required=True,type=Path);ap.add_argument('--candidate-manifest',required=True,type=Path)
    ap.add_argument('--revision',required=True)
    args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    state,_=build(ROOT)
    if args.revision!=state['current_candidate'] or state['candidate_state']=='rejected':raise ValueError('latest complete non-rejected candidate required')
    if not bpy.context.scene.get('hgpt_not_production'):raise ValueError('candidate-only scene required')
    source=Path(bpy.data.filepath);p=plan(ROOT,source,args.candidate_manifest,args.out_dir,args.revision)
    if p['candidate_sha256']!=state['last_known_candidate_sha256']:raise ValueError('source differs from current candidate evidence')
    rig=bpy.data.objects.get('HGPT_CANONICAL_V4_ORIGINAL');body=bpy.data.objects.get(BODY);shorts=bpy.data.objects.get(SHORTS)
    if rig is None or rig.type!='ARMATURE' or len(rig.data.bones)!=63:raise ValueError('canonical 63-bone rig required')
    if body is None or shorts is None or any(o.type!='MESH' or o.find_armature()!=rig for o in (body,shorts)):
        raise ValueError('owned bound body and shorts required; never label a bare export dressed')
    if any(o.get('hgpt_production_ready') for o in (body,shorts)):raise ValueError('candidate export cannot carry a production-ready label')
    git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    script_sha=digest(ROOT/SCRIPT)
    objects=list(bpy.data.objects);saved=[(o,o.select_get(),o.hide_get(),o.hide_viewport,o.hide_render) for o in objects]
    mask=body.modifiers.get('HGPT_DRESSED_MASK');mask_state=(mask.show_viewport,mask.show_render) if mask else None
    pose=rig.data.pose_position
    keys={'hgpt_export_source_candidate_sha256':p['candidate_sha256'],
          'hgpt_export_candidate_revision':args.revision,'hgpt_export_production_approved':False}
    properties=[(o,k,k in o,o.get(k)) for o in (rig,body,shorts) for k in keys]
    try:
        addon_utils.enable('io_scene_gltf2',default_set=False)
        out=ROOT/p['output_directory'];out.mkdir(parents=True,exist_ok=False)
        rig.data.pose_position='REST'
        for o in (rig,body,shorts):
            for key,value in keys.items():o[key]=value
        for variant,name in p['files'].items():
            dressed=variant=='dressed'
            for o in objects:o.select_set(False)
            for o in (rig,body):o.hide_set(False);o.hide_viewport=False;o.hide_render=False;o.select_set(True)
            shorts.hide_set(not dressed);shorts.hide_viewport=not dressed;shorts.hide_render=not dressed;shorts.select_set(dressed)
            if mask:mask.show_viewport=mask.show_render=dressed
            bpy.context.view_layer.update()
            if (out/name).exists():raise ValueError('export output already exists; preserve it: '+name)
            status=bpy.ops.export_scene.gltf(filepath=str(out/name),**SETTINGS)
            if 'FINISHED' not in status:raise ValueError('Blender export did not finish: '+variant)
        data=record(ROOT,p,bpy.app.version_string,git_commit,script_sha,SETTINGS)
        data['capture_arguments']=sys.argv[sys.argv.index('--')+1:]
        data['rest_scope']='armature REST; authored non-armature modifiers follow recorded export_apply setting'
        with (out/'CANDIDATE_GLB_EXPORT.json').open('x',encoding='utf-8') as handle:handle.write(json.dumps(data,indent=2)+'\n')
        print('CANDIDATE EXPORT CAPTURED',out,'production_approved: false')
    finally:
        rig.data.pose_position=pose
        if mask:mask.show_viewport,mask.show_render=mask_state
        for o,key,existed,value in properties:
            if existed:o[key]=value
            elif key in o:del o[key]
        for o,selected,hidden,viewport,render in saved:
            o.hide_viewport=viewport;o.hide_render=render;o.hide_set(hidden);o.select_set(selected)
        bpy.context.view_layer.update()


if __name__=='__main__':main()
