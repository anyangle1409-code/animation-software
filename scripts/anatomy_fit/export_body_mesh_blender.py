#!/usr/bin/env python3
"""Export the undeformed body mesh (world vertices, triangles) that build_anatomical_master_blender.py contains bones
against, so the source rebuild (skeleton_fit.build -> enforce_midline -> contain) can be re-run in pure Python (bpy;
read-only: the blend is opened, never saved).

  python3.13 export_body_mesh_blender.py --blend B.blend --out MESH.npz
"""
import argparse, hashlib, sys
from pathlib import Path

import bpy  # noqa: E402
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser(); ap.add_argument('--blend', required=True); ap.add_argument('--out', required=True)
    o = ap.parse_args(argv)
    before = hashlib.sha256(Path(o.blend).read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(Path(o.blend).resolve()))
    from build_anatomical_master_blender import BODY
    body = bpy.data.objects[BODY]; mw = body.matrix_world
    V = np.array([list(mw @ v.co) for v in body.data.vertices])
    T = []
    for poly in body.data.polygons:
        vs = list(poly.vertices)
        T += [[vs[0], vs[i], vs[i + 1]] for i in range(1, len(vs) - 1)]
    np.savez(o.out, V=V, T=np.array(T), blend_sha256=before)
    assert hashlib.sha256(Path(o.blend).read_bytes()).hexdigest() == before
    print('vertices', len(V), 'triangles', len(T), 'blend', before[:16])


if __name__ == '__main__':
    main()
