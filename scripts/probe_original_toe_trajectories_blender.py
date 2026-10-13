"""Fresh196frame unloaded trajectory diagnostics for the28new controls."""
import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
out=Path(sys.argv[sys.argv.index('--')+1]).resolve()
rig=bpy.data.objects['HGPT_TOE_SEGMENT_RUNTIME_TRIAL']
body=bpy.data.objects['HGPT_BODY_TOE_SEGMENT_TRIAL']
def reset():
    for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
    bpy.context.view_layer.update()
def points():
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return [ev.matrix_world@v.co for v in ev.data.vertices]
reset();rest=points();body.data.calc_loop_triangles()
triangles=[tuple(t.vertices) for t in body.data.loop_triangles]
controls=sorted(b.name for b in rig.data.bones if b.name.startswith('trial_toe'))
records=[]
for name in controls:
    own={g.index for g in body.vertex_groups if g.name.startswith(name[:10]) and g.name.endswith(name[-2:])}
    ids=[v.index for v in body.data.vertices if any(g.group in own and g.weight>.1 for g in v.groups)]
    local_tri=[t for t in triangles if any(i in ids for i in t)]
    reference=[]
    for t in local_tri:
        p=[rest[i] for i in t];reference.append((p[1]-p[0]).cross(p[2]-p[0]))
    previous=None
    for frame,angle in enumerate((0,5,10,15,10,5,0)):
        reset();rig.pose.bones[name].matrix_basis=Matrix.Rotation(math.radians(angle),4,'X')
        bpy.context.view_layer.update();posed=points()
        assert all(math.isfinite(v) for p in posed for v in p)
        inversions=0;ratios=[]
        for t,n in zip(local_tri,reference):
            p=[posed[i] for i in t];m=(p[1]-p[0]).cross(p[2]-p[0])
            if n.length>1e-12:
                ratios.append(m.length/n.length)
                if n.dot(m)<0:inversions+=1
        records.append({'control':name,'frame':frame,'local_x_angle_deg':angle,
          'max_displacement_mm':1000*max((posed[i]-rest[i]).length for i in ids),
          'previous_step_max_mm':None if previous is None else 1000*max((posed[i]-previous[i]).length for i in ids),
          'minimum_sample_z_mm':1000*min(posed[i].z for i in ids),
          'triangle_orientation_reversal_count':inversions,
          'triangle_area_ratio_min_max':[min(ratios),max(ratios)]})
        previous=posed
    assert max((p-q).length for p,q in zip(posed,rest))<2e-6
reset()
report={'candidate_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
 'control_count':len(controls),'samples':len(records),'all_finite':True,
 'trajectory_deg':[0,5,10,15,10,5,0],'context':'unloaded per-control implementation probe; not gait/physiology',
 'sample_selection':'vertices with individual digit-group influence above0.1 and adjacent triangles; not exhaustive whole-foot extrema',
 'maximum_triangle_reversals':max(r['triangle_orientation_reversal_count'] for r in records),
 'maximum_adjacent_step_mm':max(r['previous_step_max_mm'] or 0 for r in records),
 'minimum_any_sample_z_mm':min(r['minimum_sample_z_mm'] for r in records),
 'motion_deformation_accepted':False,'physiological_coupling_accepted':False,'records':records}
out.write_text(json.dumps(report,indent=2)+'\n')
print('TOE_TRAJECTORIES',json.dumps({k:v for k,v in report.items() if k!='records'}))
