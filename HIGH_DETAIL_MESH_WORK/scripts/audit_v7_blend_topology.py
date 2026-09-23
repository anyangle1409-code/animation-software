"""Read-only audit of the saved V7 editable knee mesh."""
from pathlib import Path
import json
import bpy,bmesh
from mathutils import Vector

root=Path(__file__).resolve().parents[1]
path=root/'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v7_knee_retopology.blend'
bpy.ops.wm.open_mainfile(filepath=str(path))
body=max((o for o in bpy.data.objects if o.type=='MESH'),key=lambda o:len(o.data.vertices))
bm=bmesh.new();bm.from_mesh(body.data)
centres={'L':Vector((.06,.04,.53)),'R':Vector((-.06,.04,.53))}
edges={side:sum(1 for e in bm.edges if e.is_boundary and (((e.verts[0].co+e.verts[1].co)*.5)-centre).length<.18)
       for side,centre in centres.items()}
result={'body_vertices':len(body.data.vertices),'body_triangles':len(body.data.polygons),
        'local_boundary_edges_in_blend':edges,'uv_loop_counts':{u.name:len(u.data) for u in body.data.uv_layers},
        'armature_objects':sum(o.type=='ARMATURE' for o in bpy.data.objects)}
assert result['body_vertices']==33059
assert result['body_triangles']==62961
assert all(v<74 for v in edges.values())
bm.free()
(root/'reports/blend_topology_audit_v7_knee_retopology.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
