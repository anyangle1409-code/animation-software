"""Fresh Blender/mathutils verification only; no anatomical asset is saved."""
import json, sys, importlib.util
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix, Vector
ROOT = Path(__file__).resolve().parents[5]
spec = importlib.util.spec_from_file_location('thorax', ROOT / 'scripts/anatomy_fit/thorax_source_frame.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
record = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/canonical_sc_primary_model_reference_v1.json').read_text())
source = {k.upper(): v['location_m'] for k, v in record['source_markers'].items() if k in ['ij', 'c7', 'px', 't8']}
Q = np.array([[0., 0., -1.], [-1., 0., 0.], [0., 1., 0.]])
shift = np.array([.1, -.2, 1.3])
target = {k: Q @ np.array(v) + shift for k, v in source.items()}
source_origin, source_frame = m.thorax_frame(source)
target_origin, target_frame = m.thorax_frame(target)
parent = bpy.data.objects.new('SYNTHETIC_TARGET_FRAME_NOT_CANONICAL', None)
bpy.context.scene.collection.objects.link(parent)
parent.rotation_mode = 'QUATERNION'
parent.rotation_quaternion = Matrix(target_frame.tolist()).to_quaternion()
parent.location = Vector(target_origin.tolist())
rows = []
for side, sign in [('right', 1.), ('left', -1.)]:
    point = np.array(record['SC']['location_in_parent_m']); point[2] *= sign
    marker = bpy.data.objects.new('SOURCE_SC_CONTEXT_' + side, None)
    bpy.context.scene.collection.objects.link(marker)
    marker.parent = parent
    marker.location = Vector((source_frame.T @ (point - source_origin)).tolist())
    bpy.context.view_layer.update()
    expected = Q @ point + shift
    actual = np.array(marker.matrix_world.translation[:])
    error = float(np.max(np.abs(actual - expected)))
    assert error < 1e-7, (side, error)
    mapped = m.map_between_thorax_frames(source, target, point)
    assert np.max(np.abs(mapped - expected)) < 1e-12
    rows.append({'side': side, 'actual_m': actual.tolist(), 'expected_m': expected.tolist(),
                 'max_error_m': error})
assert rows[0]['actual_m'][0] < shift[0] < rows[1]['actual_m'][0]
report = {'status': 'CONFIRMED_BLENDER_FRAME_TRANSFER_ONLY', 'bpy_version': bpy.app.version_string,
          'fixtures_synthetic_target_pose': True, 'source_SC_context': True, 'bilateral_signs_match': True,
          'checks': rows, 'blend_saved': False, 'canonical_coordinates_selected': False,
          'scope': 'Quaternion parent transform and metre-valued bilateral point transfer; no anatomical contact or movement acceptance.'}
out = Path(sys.argv[1])
if out.exists(): raise FileExistsError('Retained run output must not be overwritten')
out.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
