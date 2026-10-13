"""Reopen both actual native files and verify the bounded plantar trial."""
import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
source,candidate,out=map(Path,sys.argv[sys.argv.index('--')+1:])
def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body=bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
    rig=bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
    a=bpy.data.objects['HGPT_ANATOMICAL_MASTER']
    return {'coords':[tuple(v.co) for v in body.data.vertices],
      'topology':[tuple(p.vertices) for p in body.data.polygons],
      'vertex_group_names':[g.name for g in body.vertex_groups],
      'body_world':[list(x) for x in body.matrix_world],
      'body_parent':None if body.parent is None else body.parent.name,
      'modifiers':[(m.name,m.type,m.show_viewport,m.show_render,
         None if m.type!='ARMATURE' or m.object is None else m.object.name,
         None if m.type!='ARMATURE' else m.use_deform_preserve_volume) for m in body.modifiers],
      'weights':[[(g.group,g.weight) for g in v.groups] for v in body.data.vertices],
      'keys':{k.name:[tuple(v.co) for v in k.data] for k in body.data.shape_keys.key_blocks},
      'rigs':{r.name:{'world':[list(x) for x in r.matrix_world],
       'rest':{b.name:[list(x) for x in b.matrix_local] for b in r.data.bones},
       'stations':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local),
          'length':b.length,'parent':None if b.parent is None else b.parent.name}
          for b in r.data.bones}} for r in (rig,a)}}
before=snapshot(source);after=snapshot(candidate)
assert before['weights']==after['weights']
assert before['rigs']==after['rigs']
for field in ('topology','vertex_group_names','body_world','body_parent','modifiers'):
    assert before[field]==after[field],field
assert len(after['coords'])==17946
changed=[i for i,(p,q) in enumerate(zip(before['coords'],after['coords'])) if p!=q]
assert len(changed)==902,len(changed)
assert all(p[0:2]==q[0:2] for p,q in zip(before['coords'],after['coords']))
assert all(q[2]<=p[2]+1e-8 for p,q in zip(before['coords'],after['coords']))
for name in before['keys']:
    for i,(p,q) in enumerate(zip(before['keys'][name],after['keys'][name])):
        for k in range(3):
            expected=after['coords'][i][k]-before['coords'][i][k]
            assert abs(q[k]-p[k]-expected)<2e-7,(name,i,k)
body=bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE'];rig=bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
body.data.calc_loop_triangles()
flipped=[];area_ratios=[]
for t in body.data.loop_triangles:
    ids=t.vertices
    p=[Vector(before['coords'][i]) for i in ids]
    q=[Vector(after['coords'][i]) for i in ids]
    n=(p[1]-p[0]).cross(p[2]-p[0]);m=(q[1]-q[0]).cross(q[2]-q[0])
    if n.length>1e-12:
        area_ratios.append(m.length/n.length)
        if n.dot(m)<0:flipped.append(t.index)
for k in body.data.shape_keys.key_blocks:
    if k.name!='Basis':k.value=0
def reset():
    for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
    bpy.context.view_layer.update()
def points():
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return [ev.matrix_world@v.co for v in ev.data.vertices]
reset();rest=points()
assert max(abs(p[k]-q[k]) for p,q in zip(rest,after['coords']) for k in range(3))<2e-6
# Mirror pairs from the immutable original, not candidate-dependent grouping.
lookup={(round(-p[0],6),round(p[1],6),round(p[2],6)):i for i,p in enumerate(before['coords'])}
symmetry=max(abs(after['coords'][i][2]-after['coords'][lookup[(round(p[0],6),round(p[1],6),round(p[2],6))]][2])
             for i,p in enumerate(before['coords']) if (round(p[0],6),round(p[1],6),round(p[2],6)) in lookup)
assert symmetry<2e-6,symmetry
motion=[]
for suffix in ('l','r'):
    ids=[i for i,p in enumerate(rest) if p.z<.16 and p.x*(1 if suffix=='r' else -1)>0]
    for control,angles in [('toe',[-15,0,15]),('foot',[-10,0,10])]:
        for angle in angles:
            reset();p=rig.pose.bones[control+'_'+suffix];pivot=p.head.copy()
            p.matrix=Matrix.Translation(pivot)@Matrix.Rotation(math.radians(angle),4,'X')@Matrix.Translation(-pivot)@p.matrix
            bpy.context.view_layer.update();posed=points()
            assert all(math.isfinite(v) for point in posed for v in point)
            motion.append({'suffix':suffix,'control':control,'angle_deg':angle,
              'minimum_foot_z_mm':1000*min(posed[i].z for i in ids),
              'context':'unloaded/free control; no planted contact solver'})
reset();returned=points();residual=max((p-q).length for p,q in zip(rest,returned))
assert residual<2e-6
a=bpy.data.objects['HGPT_ANATOMICAL_MASTER']
digit_contacts=[]
ends=sorted([a.matrix_world@b.tail_local for b in a.data.bones if b.name.endswith('_left')
     and 'distal_phalanx' in b.name and any(s in b.name for s in ('hallux_','toe2_','toe3_','toe4_','toe5_'))],key=lambda p:p.x)
for side,sign in [('left',1),('right',-1)]:
    for digit,tip in enumerate(ends,1):
        ids=[i for i,p in enumerate(rest) if p.x*sign>0 and p.z<.045 and -p.y>-tip.y-.015
             and min(range(5),key=lambda j:abs(abs(p.x)-ends[j].x))==digit-1]
        digit_contacts.append({'side':side,'digit':digit,'sample_vertices':len(ids),
          'minimum_z_mm':1000*min(rest[i].z for i in ids)})
report={'native_reopen_pass':True,'changed_vertices':len(changed),'weights_and_both_rig_rest_world_unchanged':True,
 'topology_group_names_body_transform_modifiers_bone_stations_unchanged':True,
 'contact_interpretation':'Each digit sample contains a vertex within0.001mm of floor; not complete contact patch/pressure/load proof.',
 'triangle_orientation_reversals_vs_source':flipped,
 'triangle_area_ratio_min_max':[min(area_ratios),max(area_ratios)],
 'all_corrective_relative_deltas_preserved_tolerance_m':2e-7,'bilateral_z_residual_m':symmetry,
 'return_to_identity_residual_m':residual,'digit_contact_samples':digit_contacts,'unloaded_motion':motion,
 'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
 'owner_accepted':False,'shape_accepted':False,'physiological_or_loaded_contact_accepted':False}
out.write_text(json.dumps(report,indent=2)+'\n')
print('NATIVE_REOPEN_PASS',json.dumps(report))
