"""Measure O2 neutral mesh; --strict is for the completed neutral stage."""
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from original_o2_mesh_checks import inspect_mesh

body = bpy.data.objects.get('HGPT_ORIGINAL_V1_CLEAN_SCAFFOLD')
if body is None or body.type != 'MESH':
    raise RuntimeError('ORIGINAL v1 O2 body mesh is missing')
vertices = [tuple(body.matrix_world @ vertex.co) for vertex in body.data.vertices]
faces = [tuple(poly.vertices) for poly in body.data.polygons]
result = inspect_mesh(vertices, faces)
result['target_height_m'] = 1.82
result['height_within_2mm'] = abs(result['height_m'] - 1.82) <= .002
result['clean_room'] = bool(bpy.context.scene.get('hgpt_clean_room')) and not bool(bpy.context.scene.get('hgpt_legacy_geometry_imported'))
result['pass'] = result['clean_room'] and result['height_within_2mm'] and all(
    result[key] == 0 for key in ('unmatched_mirror_vertices', 'boundary_edges',
                                 'nonmanifold_edges', 'inconsistent_winding_edges',
                                 'loose_vertices', 'degenerate_faces', 'duplicate_faces'))
result['scope'] = 'Numerical mesh health only; anatomical silhouette and deformation need visual review.'
out = ROOT / 'reports/original_v1_o2_mesh_audit.json'
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
sys.exit(1 if '--strict' in sys.argv and not result['pass'] else 0)
