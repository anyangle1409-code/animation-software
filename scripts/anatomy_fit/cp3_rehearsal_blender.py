#!/usr/bin/env python3
"""CP3 rehearsal: build a skeleton-first master from target data alone, reload it in a fresh process, capture it
and compare with the input. Read-only towards the repository: the .blend goes to a caller-chosen scratch path and
is NOT an audit revision.

Reuses GPT's build_armature/build_markers from build_anatomical_master_blender.py unchanged, in an empty scene
(no character mesh, no runtime rig), which is how a skeleton-first CP3 build differs from the a00x mesh fits.

  python3.13 cp3_rehearsal_blender.py build   --record FIT.json --out-blend SCRATCH.blend
  python3.13 cp3_rehearsal_blender.py capture --blend SCRATCH.blend --out CAPTURE.json
"""
import argparse, hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT / 'scripts')]

import bpy  # noqa: E402


def build(o):
    import build_anatomical_master_blender as bm
    rec = json.loads(Path(o.record).read_text())
    out = Path(o.out_blend).resolve()
    if out.exists():
        raise FileExistsError(out)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    plan = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/blender_validation_plan.json').read_text())
    arm, coll = bm.build_armature(rec['bones'])
    bm.build_markers(arm, coll, rec['joint_markers'], rec['bones'], plan)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print(json.dumps({'built': str(out), 'bones': len(arm.data.bones), 'markers': len(coll.objects) - 1,
                      'sha256': hashlib.sha256(out.read_bytes()).hexdigest()}))


def capture(o):
    bpy.ops.wm.open_mainfile(filepath=str(Path(o.blend).resolve()))
    arm = bpy.data.objects['HGPT_ANATOMICAL_MASTER']
    bpy.context.view_layer.update()
    mw = arm.matrix_world
    bones = {}
    for b in arm.data.bones:
        bid = b['hgpt_anatomical_id']
        z = (mw.to_3x3() @ b.matrix_local.to_3x3()).col[2]
        bones[bid] = {'head_m': list(mw @ b.head_local), 'tail_m': list(mw @ b.tail_local),
                      'parent': b.parent['hgpt_anatomical_id'] if b.parent else None,
                      'parent_relation': json.loads(b['hgpt_parent_relation']),
                      'bone_z_axis': list(z.normalized()), 'role': b['hgpt_role'], 'placement': b['hgpt_placement']}
    markers = {}
    for ob in bpy.data.objects:
        if ob.name.startswith('HGPT_JOINT_'):
            M = ob.matrix_world
            markers[ob['hgpt_joint_id']] = {'centre_m': list(M.translation),
                                            'frame_axes_columns_XYZ': [list(M.to_3x3()[r]) for r in range(3)],
                                            'frame_bone': ob['hgpt_carrier_bone'], 'parent_bone': ob.parent_bone[len('anat_'):]}
    Path(o.out).write_text(json.dumps({'blend': str(o.blend), 'blender_version': bpy.app.version_string,
                                       'bones': bones, 'joint_markers': markers}, indent=1) + '\n')
    print(json.dumps({'captured_bones': len(bones), 'captured_markers': len(markers)}))


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    b = sub.add_parser('build'); b.add_argument('--record', required=True); b.add_argument('--out-blend', required=True)
    c = sub.add_parser('capture'); c.add_argument('--blend', required=True); c.add_argument('--out', required=True)
    o = ap.parse_args(argv)
    {'build': build, 'capture': capture}[o.cmd](o)


if __name__ == '__main__':
    main()
