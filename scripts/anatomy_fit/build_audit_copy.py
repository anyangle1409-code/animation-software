#!/usr/bin/env python3
"""Create an isolated anatomical-audit .blend from a pinned candidate GLB export.

The source GLB is verified against its recorded SHA-256 before import and re-hashed after.
The audit copy is a NEW file; existing outputs are never overwritten. Production assets are
read only. Run: python3 build_audit_copy.py --glb PATH --sha256 HEX --out-blend NEW.blend --receipt NEW.json
"""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy


ROOT = Path(__file__).resolve().parents[2]


def rel(path):
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    for a in ['--glb', '--sha256', '--out-blend', '--receipt']:
        ap.add_argument(a, required=True)
    o = ap.parse_args(argv)
    glb, out, receipt = Path(o.glb).resolve(), Path(o.out_blend).resolve(), Path(o.receipt).resolve()
    if out.exists() or receipt.exists():
        raise FileExistsError('Audit outputs already exist; choose a new revision name')
    before = sha(glb)
    if before != o.sha256:
        raise ValueError(f'Source GLB hash {before} does not match pinned {o.sha256}')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(glb))
    scene = bpy.context.scene
    inventory = []
    for obj in sorted(scene.objects, key=lambda x: x.name):
        row = {'name': obj.name, 'type': obj.type, 'parent': obj.parent.name if obj.parent else None,
               'matrix_world_is_identity': all(abs(obj.matrix_world[r][c] - (1 if r == c else 0)) < 1e-9
                                               for r in range(4) for c in range(4))}
        if obj.type == 'MESH':
            row.update(vertices=len(obj.data.vertices), polygons=len(obj.data.polygons),
                       vertex_groups=len(obj.vertex_groups),
                       shape_keys=[k.name for k in obj.data.shape_keys.key_blocks] if obj.data.shape_keys else [],
                       modifiers=[m.type for m in obj.modifiers])
        if obj.type == 'ARMATURE':
            row.update(bones=len(obj.data.bones))
        inventory.append(row)
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    after = sha(glb)
    data = {'schema_version': 1, 'purpose': 'Isolated anatomical audit copy; never a production or candidate asset.',
            'source': {'path': rel(glb), 'sha256_before': before, 'sha256_after': after,
                       'unchanged': before == after, 'bytes': glb.stat().st_size},
            'audit_blend': {'path': rel(out), 'sha256': sha(out), 'bytes': out.stat().st_size},
            'blender_version': bpy.app.version_string, 'importer': 'io_scene_gltf2 (glTF Y-up metres -> Blender Z-up)',
            'scene_units': {'system': scene.unit_settings.system, 'scale_length': float(scene.unit_settings.scale_length)},
            'objects': inventory}
    receipt.parent.mkdir(parents=True, exist_ok=True)
    with receipt.open('x') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
    print(json.dumps(data['audit_blend']), 'source unchanged:', data['source']['unchanged'])


if __name__ == '__main__':
    main()
