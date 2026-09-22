import bpy,numpy as np,json,struct,copy,math,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
S=next((R/'reference').iterdir())/'HOME_GYM_PT_GPT_MESH_HANDOFF/characters/HomeGymPT_Male_CORNER_FINAL_SHORTS.glb'
b=S.read_bytes();jl=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+jl]);binary=b[28+jl:];out=copy.deepcopy(j);chunks=bytearray(binary)
types={5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1',5122:'<i2',5120:'i1'};sizes={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def read(ai):
 a=j['accessors'][ai];v=j['bufferViews'][a['bufferView']];dt=np.dtype(types[a['componentType']]);n=sizes[a['type']];return np.ndarray((a['count'],n),dt,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',dt.itemsize*n),dt.itemsize)).copy()
def append(arr,typ,ctype=5126,target=34962):
 global chunks
 arr=np.array(arr,dtype=types[ctype]);chunks.extend(b'\0'*((-len(chunks))%4));offset=len(chunks);chunks.extend(arr.tobytes());vi=len(out['bufferViews']);out['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':arr.nbytes,'target':target});a={'bufferView':vi,'componentType':ctype,'count':len(arr),'type':typ};
 if typ=='VEC3':a.update(min=arr.min(axis=0).tolist(),max=arr.max(axis=0).tolist())
 ai=len(out['accessors']);out['accessors'].append(a);return ai
pr=out['meshes'][0]['primitives'][0];orig=j['meshes'][0]['primitives'][0];attrs={k:read(ai) for k,ai in orig['attributes'].items()};pos=attrs['POSITION'].astype(float);normal=attrs['NORMAL'].astype(float);tri=read(orig['indices']).reshape(-1,3);N=len(pos)
ref=json.loads((R/'reports/sculpt_reference.json').read_text());posed=np.array(ref['points']);inverse=np.array(ref['transforms']).reshape(-1,4,4).transpose(0,2,1);shares=ref['ownership'];delta=np.zeros_like(pos)
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
gain=float(args[0]) if args else 1.0
version=args[1] if len(args)>1 else 'v4b'
loss_limit=.05
for side in ['L','R']:
 sh=np.array(ref['shoulders'][side]);arm=np.array([w[side] for w in shares]);rel=posed-sh
 height=smooth((rel[:,1]+.090)/.085)*(1-smooth((rel[:,1]-.045)/.045))
 lateral=np.exp(-((rel[:,0])/.095)**4)
 depth=np.exp(-((rel[:,2]-.006)/.100)**4)
 ownership=smooth((arm-.05)/.65)
 # The frozen axilla is sharply folded already. V3 extended its cap sculpt
 # across the medial/anterior underarm and worsened compression overhead.
 # Fade the sculpt before that border; leave the outer/superior cap intact.
 medial=rel[:,0]*(1 if side=='L' else -1)
 axilla_guard=1-smooth((medial-.005)/.050)
 front_guard=1-smooth(rel[:,2]/.065)*(1-smooth((rel[:,1]+.075)/.090))
 axilla_guard*=front_guard
 mask=height*lateral*depth*ownership*axilla_guard
 world=np.zeros_like(pos);world[:,1]=.027*mask*gain;world[:,2]=-.012*mask*gain
 delta+=np.einsum('nij,nj->ni',inverse[:,:3,:3],world)
boneTransforms=np.array(ref['boneTransforms']).reshape(-1,4,4).transpose(0,2,1)
posedSculpt=posed+np.einsum('nij,nj->ni',np.linalg.inv(inverse[:,:3,:3]),delta)
# Smooth the anatomical surface across skin-ownership boundaries. Those
# boundaries are not anatomical creases and must not emboss the deltoid.
adj=[set() for _ in range(N)]
for a,b,c in tri:adj[a].update([int(b),int(c)]);adj[b].update([int(a),int(c)]);adj[c].update([int(a),int(b)])
weld={}
for i,p in enumerate(pos):weld.setdefault(tuple(np.round(p,6)),[]).append(i)
for ids in weld.values():
 neighbours=set().union(*(adj[i] for i in ids))
 for i in ids:adj[i]=neighbours
region=np.zeros(N)
for side in ['L','R']:
 rel=posed-np.array(ref['shoulders'][side]);medial=rel[:,0]*(1 if side=='L' else -1)
 axilla_guard=1-smooth((medial-.005)/.050)
 front_guard=1-smooth(rel[:,2]/.065)*(1-smooth((rel[:,1]+.075)/.090))
 axilla_guard*=front_guard
 region=np.maximum(region,np.exp(-((rel[:,0]/.095)**4+(rel[:,1]/.115)**4+(rel[:,2]/.12)**4))*axilla_guard)
region[region<.02]=0
for _ in range(5):
 previous=posedSculpt.copy()
 for i,neighbours in enumerate(adj):
  if region[i] and neighbours:posedSculpt[i]+=.42*region[i]*(previous[list(neighbours)].mean(axis=0)-previous[i])
delta=np.einsum('nij,nj->ni',inverse[:,:3,:3],posedSculpt-posed);pos+=delta;attrs['POSITION']=pos
posedNormals=np.zeros_like(pos);pf=np.cross(posedSculpt[tri[:,1]]-posedSculpt[tri[:,0]],posedSculpt[tri[:,2]]-posedSculpt[tri[:,0]])
for k in range(3):np.add.at(posedNormals,tri[:,k],pf)
posedNormals/=np.maximum(np.linalg.norm(posedNormals,axis=1)[:,None],1e-12)
# Recompute a consistent normal field only where the sculpt changed the surface.
acc=np.zeros_like(pos)
faces=np.cross(pos[tri[:,1]]-pos[tri[:,0]],pos[tri[:,2]]-pos[tri[:,0]])
for k in range(3):np.add.at(acc,tri[:,k],faces)
groups={}
for i,p in enumerate(pos):groups.setdefault(tuple(np.round(p,6)),[]).append(i)
affected=np.linalg.norm(delta,axis=1)>1e-9
for ids in groups.values():
 if np.any(affected[ids]):
  v=acc[ids].sum(axis=0);v/=max(np.linalg.norm(v),1e-12);normal[ids]=v
attrs['NORMAL']=normal
# Keep original hand vertices and every edge touching the hand region unchanged.
hand=np.array([w['hand']>.001 for w in shares]);ji=attrs['JOINTS_0'];we=attrs['WEIGHTS_0'];names=[j['nodes'][i]['name'].lower() for i in j['skins'][0]['joints']]
feet=np.array([any(('foot' in names[int(b)] or 'toe' in names[int(b)]) and w>.001 for b,w in zip(bs,ws)) for bs,ws in zip(ji,we)])
protected=hand|feet;arrays={k:list(a) for k,a in attrs.items() if not k.startswith(('JOINTS_','WEIGHTS_'))};joints=list(ji);weights=list(we);mid={};lost=[]
def midpoint(a,b):
 key=tuple(sorted((int(a),int(b))))
 if protected[a] or protected[b]:return None
 if key in mid:return mid[key]
 totals={}
 for v in [a,b]:
  for bone,w in zip(ji[v],we[v]):totals[int(bone)]=totals.get(int(bone),0)+float(w)*.5/float(we[v].sum())
 ranked=sorted(totals.items(),key=lambda x:-x[1]);chosen=ranked[:4];total=sum(x[1] for x in chosen);loss=max(0,sum(totals.values())-total)
 if loss_limit is not None and loss>loss_limit:return None
 idx=len(arrays['POSITION']);mid[key]=idx
 for name,rows in arrays.items():rows.append((attrs[name][a].astype(float)+attrs[name][b].astype(float))*.5)
 na=normal[a];nb=normal[b];edge=pos[b]-pos[a];curve=-.125*(np.dot(edge,na)*na-np.dot(edge,nb)*nb)
 # Conservative curved subdivision; never bridge a deliberate hard edge.
 if np.dot(na,nb)>.65:arrays['POSITION'][-1]+=curve*.5
 n=arrays['NORMAL'][-1];arrays['NORMAL'][-1]=n/max(np.linalg.norm(n),1e-12)
 lost.append(loss);chosen+= [(0,0)]*(4-len(chosen));joints.append([x[0] for x in chosen]);weights.append([x[1]/total for x in chosen])
 # New vertices must interpolate the actual posed surface, not multiply an
 # interpolated rest position by an independently interpolated skin transform.
 # The latter produces a quadratic cross-term and visible ridges at bone blends.
 na=posedNormals[a];nb=posedNormals[b];edge=posedSculpt[b]-posedSculpt[a];target=(posedSculpt[a]+posedSculpt[b])*.5
 if np.dot(na,nb)>.65:target-=.0625*(np.dot(edge,na)*na-np.dot(edge,nb)*nb)
 blend=sum(boneTransforms[bone]*w for bone,w in zip(joints[-1],weights[-1]));arrays['POSITION'][-1]=(np.linalg.inv(blend)@np.r_[target,1])[:3]
 return idx
newtri=[]
for a,b,c in tri:
 ab,bc,ca=midpoint(a,b),midpoint(b,c),midpoint(c,a)
 if ab is not None and bc is not None and ca is not None:newtri.extend([(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)])
 elif ab is not None and bc is not None:newtri.extend([(b,bc,ab),(a,ab,c),(ab,bc,c)])
 elif bc is not None and ca is not None:newtri.extend([(c,ca,bc),(b,bc,a),(bc,ca,a)])
 elif ca is not None and ab is not None:newtri.extend([(a,ab,ca),(c,ca,b),(ca,ab,b)])
 elif ab is not None:newtri.extend([(a,ab,c),(ab,b,c)])
 elif bc is not None:newtri.extend([(b,bc,a),(bc,c,a)])
 elif ca is not None:newtri.extend([(c,ca,b),(ca,a,b)])
 else:newtri.append((a,b,c))
assert not orig.get('targets'),'Source morph interpolation must be implemented before topology change'
for name,rows in arrays.items():
 a=j['accessors'][orig['attributes'][name]];pr['attributes'][name]=append(rows,a['type'],a['componentType']);
 if a.get('normalized'):out['accessors'][-1]['normalized']=True
pr['attributes']['JOINTS_0']=append(joints,'VEC4',5123);pr['attributes']['WEIGHTS_0']=append(weights,'VEC4');pr['indices']=append(np.array(newtri).reshape(-1,1),'SCALAR',5125,34963)
for name,values in attrs.items():
 if name.startswith(('JOINTS_','WEIGHTS_')) and not name.endswith('_0'):
  a=j['accessors'][orig['attributes'][name]];rows=np.concatenate([values,np.zeros((len(joints)-N,4))]);pr['attributes'][name]=append(rows,'VEC4',a['componentType'])
out['buffers'][0]['byteLength']=len(chunks);jb=json.dumps(out,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4);chunks.extend(b'\0'*((-len(chunks))%4));glb=struct.pack('<III',0x46546c67,2,28+len(jb)+len(chunks))+struct.pack('<II',len(jb),0x4e4f534a)+jb+struct.pack('<II',len(chunks),0x004e4942)+chunks
dest=R/f'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.glb';dest.write_bytes(glb)
report={'body_triangles':len(newtri),'source_body_triangles':len(tri),'vertices':len(joints),'original_vertices':N,'original_hand_vertices_untouched':int(hand.sum()),'sculpt_vertices':int(affected.sum()),'max_sculpt_mm':float(np.linalg.norm(delta,axis=1).max()*1000),'new_vertex_weight_loss_max':max(lost),'new_vertex_weight_loss_mean':sum(lost)/len(lost),'gain':gain,'influence_loss_limit':loss_limit,'source_rig_and_metadata_equal':all(j.get(k)==out.get(k) for k in ['nodes','skins','scenes','animations'])}
(R/f'reports/build_{version}.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(dest));
for ob in bpy.context.scene.objects:
 if ob.type=='ARMATURE':ob.show_in_front=True
 if ob.type=='MESH':ob['candidate_only']=True
bpy.ops.wm.save_as_mainfile(filepath=str(R/f'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(R/f'checkpoints/CANDIDATE_{version}_03_surface_gain_{gain:.2f}.blend'),copy=True)
