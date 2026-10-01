"""Read-only raw body (default) or garment snapshot from a verified candidate.

blender --background --factory-startup <candidate.blend> --python-exit-code 1
 --python scripts/snapshot_original_v1_model_blender.py -- <new snapshot.json> [--garment]
Never saves, evaluates modifiers, renormalizes or transfers weights.
"""
import argparse
import json
import sys
from pathlib import Path
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from original_v1_garment_evidence import capture

ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path);ap.add_argument('--garment',action='store_true')
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
out=args.output
if out.exists():raise SystemExit('STOP — snapshot output already exists')
try:result=capture(bpy,'garment' if args.garment else 'body')
except (OSError,ValueError,KeyError,TypeError) as exc:raise SystemExit('STOP — '+str(exc))
if out.resolve()==Path(bpy.data.filepath).resolve() or out.resolve()==Path(bpy.data.filepath).with_suffix('.json').resolve():raise SystemExit('STOP — output aliases candidate source')
out.parent.mkdir(parents=True,exist_ok=True)
with out.open('x',encoding='utf-8') as handle:handle.write(json.dumps(result,indent=2)+'\n')
print('MODEL SNAPSHOT',result['mesh_object'],result['candidate_sha256'],out)
