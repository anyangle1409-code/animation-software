"""Synthetic source-to-world frame save/reload fixture; NOT anatomical targets."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import bpy
from mathutils import Matrix, Vector
import numpy as np
from thorax_source_frame import thorax_frame, map_source_point

ap = argparse.ArgumentParser()
ap.add_argument('--out-blend', required=True); ap.add_argument('--out-report', required=True)
o = ap.parse_args()
if Path(o.out_blend).exists() or Path(o.out_report).exists():
    raise FileExistsError('Use new fixture output paths')
Q = np.array([[1, 0, 0], [0, 0.8, -0.6], [0, 0.6, 0.8]])
shift = np.array([0.1, 0.2, -0.3])
pts = {k: Q @ np.array(v) + shift for k, v in {
    'IJ': [0, -0.1, 1.5], 'C7': [0, 0.1, 1.5],
    'PX': [0, -0.1, 1.2], 'T8': [0, 0.1, 1.2]}.items()}
origin, R = thorax_frame(pts)
source_points = [[0.02, -0.03, 0.04], [-0.02, 0.03, -0.04]]
expected = [map_source_point(origin, R, p) for p in source_points]
bpy.ops.wm.read_factory_settings(use_empty=True)
frame = bpy.data.objects.new('SYNTHETIC_THORAX_FRAME', None)
bpy.context.scene.collection.objects.link(frame)
M = Matrix(R.tolist()).to_4x4(); M.translation = Vector(origin)
frame.rotation_mode = 'QUATERNION'; frame.matrix_world = M
for i, p in enumerate(expected):
    obj = bpy.data.objects.new(f'SYNTHETIC_POINT_{i}', None)
    bpy.context.scene.collection.objects.link(obj); obj.location = Vector(p)
bpy.ops.wm.save_as_mainfile(filepath=str(Path(o.out_blend).resolve()))
bpy.ops.wm.open_mainfile(filepath=str(Path(o.out_blend).resolve()))
bpy.context.view_layer.update()
F = np.array(bpy.data.objects['SYNTHETIC_THORAX_FRAME'].matrix_world)
points = [np.array(bpy.data.objects[f'SYNTHETIC_POINT_{i}'].matrix_world.translation) for i in range(2)]
position_error = max(float(np.linalg.norm(p-e)) for p, e in zip(points, expected))
frame_error = float(np.abs(F[:3, :3] - R).max())
report = {'scope': 'synthetic source-coordinate transform fixture only',
          'blender_version': bpy.app.version_string, 'maximum_position_error_m': position_error,
          'maximum_frame_component_error': frame_error,
          'determinant_after_reload': float(np.linalg.det(F[:3, :3])),
          'fixture_pass': bool(position_error < 1e-6 and frame_error < 1e-6 and np.linalg.det(F[:3, :3]) > 0),
          'blend_sha256': hashlib.sha256(Path(o.out_blend).read_bytes()).hexdigest(),
          'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'canonical_target_selected': False}
Path(o.out_report).write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
