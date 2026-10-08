"""Inspect source STL geometry only. No canonical coordinates or mesh promotion."""
import json, sys, struct, re, hashlib
from pathlib import Path
import bpy
import numpy as np
folder = Path(sys.argv[1]); out = Path(sys.argv[2])
if out.exists(): raise FileExistsError('Keep retained audit output immutable')
rows = []
for name in ['M02_L_Calc.stl', 'M02_L_Talus.stl', 'M02_L_1Met.stl', 'M02_L_Midfoot.stl']:
    path = folder / name; raw = path.read_bytes()
    # Byte-count detection avoids the invalid 'solid' => ASCII shortcut.
    n = struct.unpack('<I', raw[80:84])[0] if len(raw) >= 84 else -1
    binary = len(raw) == 84 + 50*n
    if binary:
        triangles = np.array([struct.unpack('<9f', raw[84+50*i+12:84+50*i+48])
                              for i in range(n)]).reshape(-1, 3)
    else:
        text = raw.decode('ascii')
        triangles = np.array([[float(x) for x in line.split()[1:]]
                              for line in text.splitlines() if line.strip().startswith('vertex')])
        assert len(triangles) % 3 == 0; n = len(triangles)//3
    assert np.isfinite(triangles).all()
    bpy.ops.wm.stl_import(filepath=str(path), global_scale=1, use_scene_unit=False,
                         forward_axis='Y', up_axis='Z', use_mesh_validate=False)
    obj = bpy.context.object; mesh = obj.data
    verts = np.array([v.co[:] for v in mesh.vertices])
    expected_vertices = np.unique(triangles.astype(np.float32), axis=0)
    actual_vertices = np.unique(verts.astype(np.float32), axis=0)
    np.testing.assert_array_equal(expected_vertices, actual_vertices)
    assert len(mesh.polygons) == n, 'STL import dropped or added triangles'
    raw_faces = sorted(tuple(sorted(tuple(float(c) for c in point) for point in tri))
                       for tri in triangles.astype(np.float32).reshape(-1, 3, 3))
    imported_faces = sorted(tuple(sorted(tuple(mesh.vertices[i].co) for i in face.vertices))
                            for face in mesh.polygons)
    assert raw_faces == imported_faces, 'STL import changed triangle geometry'
    expected_min, expected_max = triangles.min(axis=0), triangles.max(axis=0)
    tolerance = max(1, float(np.abs(triangles).max())) * 1e-6
    assert np.max(np.abs(verts.min(axis=0)-expected_min)) < tolerance
    assert np.max(np.abs(verts.max(axis=0)-expected_max)) < tolerance
    links = [[] for v in mesh.vertices]
    for edge in mesh.edges:
        a,b = edge.vertices; links[a].append(b); links[b].append(a)
    seen = set(); components = []
    for start in range(len(links)):
        if start in seen: continue
        todo=[start]; seen.add(start); ids=[]
        while todo:
            i=todo.pop(); ids.append(i)
            for j in links[i]:
                if j not in seen: seen.add(j); todo.append(j)
        data=verts[ids]
        components.append({'vertices':len(ids), 'bbox_min':data.min(axis=0).tolist(),
                           'bbox_max':data.max(axis=0).tolist(),
                           'vertex_mean_not_volume_centroid':data.mean(axis=0).tolist()})
    components.sort(key=lambda x:-x['vertices'])
    rows.append({'file':name, 'sha256':hashlib.sha256(raw).hexdigest(),
                 'format':'binary_STL' if binary else 'ASCII_STL', 'raw_triangles':n,
                 'imported_vertices':len(verts), 'imported_faces':len(mesh.polygons),
                 'bbox_min':expected_min.tolist(), 'bbox_max':expected_max.tolist(),
                 'components':components, 'raw_bbox_preserved_by_import':True, 'all_vertex_positions_preserved_float32':True,
                 'all_triangle_geometry_preserved_ignoring_winding':True})
report={'status':'CONFIRMED_SOURCE_STL_IMPORT_ONLY', 'bpy_version':bpy.app.version_string,
        'coordinate_units':'UNVERIFIED_STL_UNIT_METADATA', 'source_segments':rows,
        'source_common_contact_frame':'UNVERIFIED', 'canonical_targets_selected':False,
        'blend_saved':False, 'production_modified':False,
        'limits':['Connected components are not named anatomical bones without an independent identification.',
                  'Vertex mean is not bone-volume centroid or articular contact centre.',
                  'No generic PCA axis or nearest surface point is promoted into a joint axis/contact.',
                  'This grouped midfoot represents nine bones; it must not become one bone in the 206 inventory.']}
out.write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report))
