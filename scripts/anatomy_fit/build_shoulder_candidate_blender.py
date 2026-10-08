#!/usr/bin/env python3
"""Build the shoulder-proposal audit candidate .blend from a copy of a003 (bpy). a003 itself is opened read-only and never
saved; the result goes to a new, separately named path that must not exist.

The a003 anatomical master (armature, joint markers, landmark empties) is removed from the in-memory copy and rebuilt from
the candidate record with GPT's build_armature/build_markers (current fixed builder). The 29 measured scapula landmarks are
added as small reference empties in their own collection, parented to the scapula bones. Body mesh and runtime rig are a003's.

  python3.13 build_shoulder_candidate_blender.py --source-blend A003.blend --record CAND.json --out-blend NEW.blend
"""
import argparse, hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT / 'scripts')]

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-blend', required=True); ap.add_argument('--record', required=True); ap.add_argument('--out-blend', required=True)
    o = ap.parse_args(argv)
    src, out = Path(o.source_blend).resolve(), Path(o.out_blend).resolve()
    if out.exists():
        raise FileExistsError(out)
    before = sha(src)
    import build_anatomical_master_blender as bm
    rec = json.loads(Path(o.record).read_text())
    bpy.ops.wm.open_mainfile(filepath=str(src))
    coll = bpy.data.collections.get('HGPT_ANATOMICAL_REFERENCE')
    removed = 0
    if coll is not None:
        for name in [ob.name for ob in coll.objects]:
            bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True); removed += 1
        bpy.data.collections.remove(coll)
    if 'HGPT_ANATOMICAL_MASTER' in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects['HGPT_ANATOMICAL_MASTER'], do_unlink=True); removed += 1
    plan = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/blender_validation_plan.json').read_text())
    arm, newcoll = bm.build_armature(rec['bones'])
    bm.build_markers(arm, newcoll, rec['joint_markers'], rec['bones'], plan)
    lmc = bpy.data.collections.new('SHOULDER_PROPOSAL_SCAPULA_LANDMARKS')
    bpy.context.scene.collection.children.link(lmc)
    n_lm = 0
    for side, pts in rec['candidate']['scapula_landmarks_world_mm'].items():
        for i, p in enumerate(pts, 1):
            e = bpy.data.objects.new(f'SCAPLM_{side}_{i:02d}', None)
            lmc.objects.link(e)
            e.empty_display_type = 'SPHERE'; e.empty_display_size = 0.003
            e['hgpt_scapula_landmark_1based'] = i; e['hgpt_source'] = 'LEE_2024_SCAPULA_RAW_3D via canonical_shoulder_girdle_solution_182_v1.json'
            e.parent = arm; e.parent_type = 'BONE'; e.parent_bone = f'anat_scapula_{side}'
            bpy.context.view_layer.update()
            e.matrix_world = Matrix.Translation(Vector([c / 1000.0 for c in p]))
            n_lm += 1
    bpy.context.scene['hgpt_candidate_id'] = rec['candidate']['id']
    bpy.context.scene['hgpt_candidate_status'] = rec['candidate']['status']
    bpy.context.view_layer.update()
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    after = sha(src)
    if before != after:
        raise RuntimeError('source .blend changed')
    print(json.dumps({'out': str(out), 'sha256': sha(out), 'source_sha256_before': before, 'source_sha256_after': after,
                      'removed_objects': removed, 'bones': len(arm.data.bones), 'markers': len([x for x in newcoll.objects if x.name.startswith('HGPT_JOINT_')]),
                      'scapula_landmark_empties': n_lm, 'blender': bpy.app.version_string}))


if __name__ == '__main__':
    main()
