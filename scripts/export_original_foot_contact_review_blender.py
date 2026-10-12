"""Package frozen foot weights candidate only; verify native and GLB rest skin.

Review-only Work asset export, not a viewer implementation or release gate.
"""
import bpy,sys,json,hashlib,struct,math
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
from mathutils.kdtree import KDTree
args=sys.argv[sys.argv.index('--')+1:];manifest=Path(args[0]);out=Path(args[1]);out.mkdir(parents=True,exist_ok=True)
rec=json.loads(manifest.read_text());source=Path(bpy.data.filepath)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source)==rec['candidate_sha256']
body=bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE'];rig=bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
assert len(body.data.vertices)==17946 and len(rig.data.bones)==67
# Blender's reference Basis has value1; only actual relative morphs are zero.
assert all(abs(k.value)<1e-7 for k in body.data.shape_keys.key_blocks if k!=body.data.shape_keys.reference_key)
assert max(abs(p.matrix_basis[r][c]-(r==c)) for p in rig.pose.bones for r in range(4) for c in range(4))<1e-6
def immutable():
 return json.dumps({'vertices':[list(v.co) for v in body.data.vertices],
  'weights':[[[g.group,g.weight] for g in v.groups] for v in body.data.vertices],
  'corrective_coordinates':{k.name:[list(v.co) for v in k.data] for k in body.data.shape_keys.key_blocks},
  'rigs':{name:{'world':[list(r) for r in bpy.data.objects[name].matrix_world],
   'rest':{b.name:[list(r) for r in b.matrix_local] for b in bpy.data.objects[name].data.bones}}
   for name in ('HGPT_ANATOMICAL_MASTER','HGPT_CANONICAL_V4_ORIGINAL')}},sort_keys=True)
before=immutable();influences=max(sum(g.weight>0 for g in v.groups) for v in body.data.vertices)
bpy.ops.object.select_all(action='DESELECT')
for obj in (body,rig):obj.hide_set(False);obj.hide_render=False;obj.select_set(True)
bpy.context.view_layer.objects.active=body
# Export-copy metadata must identify this frozen candidate on both mesh and rig.
# Retain prior export provenance under explicit historical names, never as current.
for obj in (body,rig):
 for key in list(obj.keys()):
  if key.startswith('hgpt_export_'):
   obj['hgpt_historical_'+key.removeprefix('hgpt_')]=obj[key];del obj[key]
 if 'hgpt_unbound_o2_target' in obj:
  obj['hgpt_historical_unbound_o2_target']=obj['hgpt_unbound_o2_target'];del obj['hgpt_unbound_o2_target']
 obj['hgpt_review_candidate']='FOOT_CONTACT_WEIGHTS_ONLY; FOOT_LENGTH_UNCHANGED; OWNER_ACCEPTANCE_PENDING'
 obj['hgpt_production_approved']=False
 obj['hgpt_export_source_candidate_sha256']=rec['candidate_sha256']
 obj['hgpt_export_original_model_sha256']=rec['source_sha256']
 obj['hgpt_export_candidate_revision']='FOOT_CONTACT_WEIGHTS_CANDIDATE_20261012'
 obj['hgpt_export_source_branch']='codex/original-foot-proportions-candidate-20261012'
 obj['hgpt_export_source_commit']='a542b8d8198131caf5d58ee239a2e7b781ef88c9'
 obj['hgpt_export_production_approved']=False
rig['hgpt_body_driver']=True
path=out/'HomeGymPT_Male_ORIGINAL_v1_FOOT_CONTACT_REVIEW_ONLY.glb'
bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,
 export_animations=False,export_extras=True,export_cameras=False,export_lights=False,export_all_influences=True)
assert immutable()==before and sha(source)==rec['candidate_sha256']
raw=path.read_bytes();magic,version,total=struct.unpack_from('<III',raw)
assert magic==0x46546C67 and version==2 and total==len(raw)
n,kind=struct.unpack_from('<II',raw,12);assert kind==0x4E4F534A
g=json.loads(raw[20:20+n]);bn,bkind=struct.unpack_from('<II',raw,20+n);assert bkind==0x004E4942
binary=raw[28+n:28+n+bn]
types={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16};components={5120:('b',1),5121:('B',1),5122:('h',2),5123:('H',2),5125:('I',4),5126:('f',4)}
def values(index):
 a=g['accessors'][index];assert 'sparse' not in a
 v=g['bufferViews'][a['bufferView']];assert v.get('buffer',0)==0
 fmt,size=components[a['componentType']];count=types[a['type']]
 offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',count*size)
 data=[struct.unpack_from('<'+fmt*count,binary,offset+i*stride) for i in range(a['count'])]
 if a.get('normalized'):data=[tuple(x/((1<<(size*8))-1) for x in row) for row in data]
 return data
assert len(g['meshes'])==1 and len(g['skins'])==1 and not g.get('animations')
mesh=g['meshes'][0];assert len(mesh['primitives'])==1
p=mesh['primitives'][0];attrs=p['attributes'];positions=values(attrs['POSITION']);normals=values(attrs['NORMAL'])
assert len(positions)==17946 and len(values(p['indices']))==35888*3
assert all(math.isfinite(x) for row in positions+normals for x in row)
normal_error=max(abs(sum(x*x for x in row)-1) for row in normals);assert normal_error<1e-4
skin=g['skins'][0];assert len(skin['joints'])==67
sets=[s for s in attrs if s.startswith('WEIGHTS_')]
weights=[values(attrs[s]) for s in sets]
sum_error=max(abs(sum(sum(data[i]) for data in weights)-1) for i in range(len(positions)))
assert sum_error<1e-5 and all(math.isfinite(x) and x>=0 for data in weights for row in data for x in row)
for name in attrs:
 if name.startswith('JOINTS_'):assert all(0<=x<67 for row in values(attrs[name]) for x in row)
nodes=g['nodes'];parents={c:i for i,node in enumerate(nodes) for c in node.get('children',[])}
for name in (body.name,rig.name):
 matched=[n for n in nodes if n.get('name')==name];assert len(matched)==1
 extras=matched[0]['extras'];assert extras['hgpt_export_source_candidate_sha256']==rec['candidate_sha256']
 assert extras['hgpt_export_original_model_sha256']==rec['source_sha256']
 assert extras['hgpt_export_production_approved'] is False
def matrix(row):return Matrix([[row[c*4+r] for c in range(4)] for r in range(4)])
def local(node):
 if 'matrix' in node:return matrix(node['matrix'])
 q=node.get('rotation',[0,0,0,1]);rotation=Quaternion((q[3],q[0],q[1],q[2])).to_matrix().to_4x4()
 return Matrix.Translation(Vector(node.get('translation',[0,0,0])))@rotation@Matrix.Diagonal(Vector([*node.get('scale',[1,1,1]),1]))
worlds={}
def world(i):
 if i not in worlds:worlds[i]=(world(parents[i]) if i in parents else Matrix.Identity(4))@local(nodes[i])
 return worlds[i]
mesh_ids=[i for i,node in enumerate(nodes) if 'mesh' in node];assert len(mesh_ids)==1
meshworld=world(mesh_ids[0]);inverse=meshworld.inverted();ibms=values(skin['inverseBindMatrices'])
world_points=[meshworld@Vector(v) for v in positions]
# Verify the complete exported permutation and each named influence against native.
tree=KDTree(len(body.data.vertices))
for v in body.data.vertices:tree.insert(body.matrix_world@v.co,v.index)
tree.balance();matched_indices=set();position_error=weight_pair_error=0.0
joint_arrays={s:values(attrs['JOINTS_'+s.removeprefix('WEIGHTS_')]) for s in sets}
for i,point in enumerate(world_points):
 native_world=Vector((point.x,-point.z,point.y)) # glTF Y-up -> Blender Z-up
 _,index,distance=tree.find(native_world);assert distance<2e-6
 assert index not in matched_indices,'Exported/native vertex permutation is not bijective'
 matched_indices.add(index);position_error=max(position_error,distance)
 native={body.vertex_groups[group.group].name:group.weight for group in body.data.vertices[index].groups if group.weight>0}
 exported={}
 for set_name,data in zip(sets,weights):
  for joint,w in zip(joint_arrays[set_name][i],data[i]):
   if w>0:
    name=nodes[skin['joints'][joint]]['name'];exported[name]=exported.get(name,0)+w
 weight_pair_error=max(weight_pair_error,max(abs(native.get(name,0)-exported.get(name,0)) for name in native.keys()|exported.keys()))
assert len(matched_indices)==17946 and weight_pair_error<2e-6
height=max(v.y for v in world_points)-min(v.y for v in world_points)
assert abs(height-1.82)<1e-6
footprints={}
for side,sign in [('left',1),('right',-1)]:
 points=[v for v in world_points if v.y<.16 and v.x*sign>0]
 length=max(v.z for v in points)-min(v.z for v in points)
 minimum_y=min(v.y for v in points)
 assert abs(length-rec['foot_length_still_m'])<1e-6 and abs(minimum_y)<1e-6
 footprints[side]={'length_m':length,'minimum_ground_height_m':minimum_y}
error=0
for joint,ibm in zip(skin['joints'],ibms):
 result=inverse@world(joint)@matrix(ibm)
 error=max(error,max(abs(result[r][c]-(r==c)) for r in range(4) for c in range(4)))
assert error<1e-5,error
assert len(p.get('targets',[]))==6 and all(abs(x)<1e-7 for x in mesh.get('weights',[]))
report={'source_branch':'codex/original-foot-proportions-candidate-20261012','source_commit':'a542b8d8198131caf5d58ee239a2e7b781ef88c9',
 'original_model_sha256':rec['source_sha256'],'candidate_model':source.name,'candidate_sha256':rec['candidate_sha256'],
 'glb':path.name,'glb_sha256':sha(path),'glb_bytes':len(raw),'vertices':17946,'triangles':35888,'skin_joints':67,
 'corrective_targets':6,'exported_animations':0,'source_max_positive_influences':influences,'exported_weight_sets':len(sets),
 'export_all_influences':True,'maximum_weight_sum_error':sum_error,'maximum_normal_squared_length_error':normal_error,
 'current_candidate_provenance_on_body_and_rig':True,'prior_export_metadata_explicitly_historical':True,
 'all_exported_vertices_and_named_joint_weights_match_native':True,
 'maximum_exported_native_position_difference_m':position_error,'maximum_exported_native_named_weight_difference':weight_pair_error,
 'maximum_rest_skin_inverse_bind_error':error,'native_geometry_weights_rig_matrices_unchanged':True,
 'exported_body_height_m':height,'exported_neutral_footprints':footprints,'glb_world_up_axis':'Y',
 'foot_length_m':rec['foot_length_still_m'],'changed_weights_vertices':724,'28cm_geometry_correction':False,
 'owner_acceptance_required':True,'production_approved':False,'anatomical_approval':False,
 'limits':['Separate review-only weights candidate; original production GLB not replaced',
 'No exercise animations, loaded stance, individual toe or physiological validation',
 'Six inherited corrective morphs remain zero; no new muscle deformation',
 '206 reference controls not exported or body-driving; static thorax layer excluded',
 'Numerical GLB checks are Work packaging evidence, not Chat viewer/GPU acceptance']}
(out/'foot_contact_glb_export_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print('FOOT_REVIEW_GLB_PASS',report)
