"""Locate actual reversed triangles and their inherited influences."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Matrix
rig=bpy.data.objects['HGPT_TOE_SEGMENT_RUNTIME_TRIAL'];body=bpy.data.objects['HGPT_BODY_TOE_SEGMENT_TRIAL']
def reset():
    for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
    bpy.context.view_layer.update()
def pts():
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return [ev.matrix_world@v.co for v in ev.data.vertices]
reset();rest=pts();rig.pose.bones['trial_toe1_01_l'].matrix_basis=Matrix.Rotation(math.radians(15),4,'X')
bpy.context.view_layer.update();posed=pts();body.data.calc_loop_triangles();rows=[]
for t in body.data.loop_triangles:
    i,j,k=t.vertices;n=(rest[j]-rest[i]).cross(rest[k]-rest[i]);m=(posed[j]-posed[i]).cross(posed[k]-posed[i])
    if n.length>1e-12 and n.dot(m)<0:
        rows.append({'triangle':t.index,'vertices':list(t.vertices),
          'neutral_world_m':[list(rest[v]) for v in t.vertices],
          'weights':[{body.vertex_groups[g.group].name:g.weight for g in body.data.vertices[v].groups} for v in t.vertices]})
reset()
Path(sys.argv[sys.argv.index('--')+1]).write_text(json.dumps(rows,indent=2)+'\n')
print('REVERSED_TRIANGLE_LOCATIONS',len(rows),'forward_mm_range',
 min(-p[1]*1000 for r in rows for p in r['neutral_world_m']),max(-p[1]*1000 for r in rows for p in r['neutral_world_m']))
