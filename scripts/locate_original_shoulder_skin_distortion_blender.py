"""Bounded native triangle distortion localization; no source save or render."""
import bpy,json,sys,hashlib
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import original_shoulder_joint_authority as authority
import build_functional_absolute_reach_blender as reach
path=Path(bpy.data.filepath)
EXPECTED='a48ee389a064927f740b5ea294b7afed3ef1616cbe8ac6c121867b86581680c2'
assert hashlib.sha256(path.read_bytes()).hexdigest()==EXPECTED
record=json.loads((ROOT/authority.RECORD).read_text())
body=bpy.data.objects['HGPT_BODY_SHOULDER_REFIT_TRIAL'];rig=bpy.data.objects['HGPT_SHOULDER_JOINT_REFIT_TRIAL']
guide=next(o for o in bpy.data.objects if o.type=='ARMATURE' and len(o.data.bones)==6 and 'scapula_left' in o.data.bones)
mapping={part+'_'+side:runtime+'_'+suffix for side,suffix in [('left','r'),('right','l')] for part,runtime in [('clavicle','clavicle'),('scapula','scapula'),('humerus','upperarm')]}
def positions():
    bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return [ev.matrix_world@v.co for v in ev.data.vertices]
for arm in (guide,rig):
    for bone in arm.pose.bones:bone.matrix_basis=Matrix.Identity(4)
neutral=positions();rest={name:rig.matrix_world@rig.data.bones[name].matrix_local for name in mapping.values()}
guide_rest={name:guide.matrix_world@guide.data.bones[name].matrix_local for name in mapping}
reach.pose_absolute(guide,record,160)
for name,target in mapping.items():
    rig.pose.bones[target].matrix=rig.matrix_world.inverted()@(guide.matrix_world@guide.pose.bones[name].matrix)@guide_rest[name].inverted()@rest[target]
    bpy.context.view_layer.update()
posed=positions();body.data.calc_loop_triangles();rows=[]
for triangle in body.data.loop_triangles:
    a,b,c=triangle.vertices
    area=(neutral[b]-neutral[a]).cross(neutral[c]-neutral[a]).length
    if area<=1e-12:continue
    centre=(neutral[a]+neutral[b]+neutral[c])/3
    if centre.z<1.25 or abs(centre.x)>.42:continue
    ratio=(posed[b]-posed[a]).cross(posed[c]-posed[a]).length/area
    rows.append({'triangle_vertices':[a,b,c],'area_ratio':ratio,'rest_centre_m':list(centre),
        'vertices':[{'index':i,'rest_m':list(neutral[i]),'posed_m':list(posed[i]),
            'weights':{body.vertex_groups[g.group].name:g.weight for g in body.data.vertices[i].groups if g.weight>0}} for i in (a,b,c)]})
for arm in (guide,rig):
    for bone in arm.pose.bones:bone.matrix_basis=Matrix.Identity(4)
assert max((a-b).length for a,b in zip(positions(),neutral))<2e-6
assert hashlib.sha256(path.read_bytes()).hexdigest()==EXPECTED
result={'input_candidate_sha256':EXPECTED,'probe':'160deg authored reach; upper body rest z>=1.25m and |x|<=.42m',
    'region_triangles':len(rows),'worst_compressed':sorted(rows,key=lambda r:r['area_ratio'])[:12],
    'worst_stretched':sorted(rows,key=lambda r:r['area_ratio'],reverse=True)[:12],
    'area_ratio_below_0_1_count':sum(r['area_ratio']<.1 for r in rows),
    'area_ratio_above_2_count':sum(r['area_ratio']>2 for r in rows),
    'source_file_unchanged':True,'scene_saved':False,'deformation_accepted':False,
    'limitation':'Geometric area distortion localization, not self-intersection/inversion or clinical verification. Hand/upper-arm areas inside bounds may also be included.'}
out=Path(sys.argv[sys.argv.index('--')+1]);out.write_text(json.dumps(result,indent=2)+'\n')
print('SHOULDER_DISTORTION_REGION',len(rows),'compressed',result['area_ratio_below_0_1_count'],'stretched',result['area_ratio_above_2_count'])
for r in result['worst_compressed'][:3]:print(r['triangle_vertices'],r['area_ratio'],r['rest_centre_m'],r['vertices'][0]['weights'])
