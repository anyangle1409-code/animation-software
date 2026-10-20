"""One bounded weight-only hypothesis; no optimisation or acceptance claim."""
import numpy as np

def validate(before,after,ids):
 before,after=np.asarray(before),np.asarray(after);ids=np.asarray(ids,int)
 if before.shape!=after.shape or before.ndim!=2 or not np.isfinite(after).all():raise ValueError('Invalid weight array')
 outside=np.ones(len(before),bool);outside[ids]=False
 if not np.array_equal(before[outside],after[outside]):raise ValueError('Weight change outside authorised patch')
 if after.min()<0 or not np.allclose(after.sum(1),before.sum(1),atol=2e-7,rtol=0):raise ValueError('Invalid weight mass')
 if abs(after-before).max()>.025+2e-7:raise ValueError('Weight proposal exceeds 2.5 percentage-point cap')
 return True

def propose(w,edges,ids):
 w=np.asarray(w,float);q=w.copy();ids=np.asarray(ids,int);edges=np.asarray(edges,int)
 if not np.isfinite(w).all() or w.min()<0:raise ValueError('Invalid input')
 for i in ids:
  neighbors=np.unique(edges[np.any(edges==i,axis=1)]);neighbors=neighbors[neighbors!=i]
  if len(neighbors):
   target=w[neighbors].mean(0)
   # Retain the original row mass, including float32 rounding.
   target*=w[i].sum()/target.sum()
   q[i]=w[i]+.25*(target-w[i])
 change=q-w;scale=min(1.,.025/max(float(abs(change).max()),1e-30));q=w+scale*change
 validate(w,q,ids)
 return q

def install_patch(res):
 import json,os
 from pathlib import Path
 body=res['body'];root=Path(__file__).resolve().parents[1]
 spec=json.loads((root/'docs/r53_proposed_weight_investigation_patch_20261019.json').read_text())
 ids=spec['proposed_edit_vertices'];assert len(ids)==26 and not set(ids)&set(spec['excluded_source_frozen_vertices'])
 source=np.load(os.environ['HGPT_R53_RESPONSE'])
 assert source['r47_allowed'].any(0)[ids].all() and not source['frozen_arm'].any(0)[ids].any()
 groups=[g.name for g in body.vertex_groups];w=np.zeros((len(body.data.vertices),len(groups)))
 for v in body.data.vertices:
  for g in v.groups:w[v.index,g.group]=g.weight
 assert all(res['runtime'].data.bones.get(g) is not None for g in groups)
 edges=np.array([tuple(e.vertices) for e in body.data.edges]);q=propose(w,edges,ids)
 for i in ids:
  for j in np.flatnonzero((w[i]!=q[i]) & ((w[i]>0)|(q[i]>0))):body.vertex_groups[int(j)].add([i],float(q[i,j]),'REPLACE')
 body.data.update()
 actual=np.zeros_like(w)
 for v in body.data.vertices:
  for g in v.groups:actual[v.index,g.group]=g.weight
 validate(w,actual,ids)
 return dict(ids=ids,maximum_weight_change=float(abs(actual-w).max()),outside_patch_exact=True,original_weight_identity_passed=bool(np.array_equal(w,actual)),before=w,after=actual,groups=groups)

def linear_points(res):
 """Independent linear blend replay, including actual corrective coordinates."""
 body,rig=res['body'],res['runtime'];blocks=body.data.shape_keys.key_blocks
 assert len(body.modifiers)==1 and body.modifiers[0].type=='ARMATURE'
 assert not body.modifiers[0].use_deform_preserve_volume and not body.modifiers[0].use_bone_envelopes
 coords=lambda k:np.array([tuple(v.co) for v in k.data])
 p=coords(blocks[0])
 for k in list(blocks)[1:]:
  if k.value and not k.mute:
   assert not k.vertex_group
   p+=(coords(k)-coords(k.relative_key))*k.value
 h=np.column_stack((p,np.ones(len(p))));result=np.zeros((len(p),4));mass=np.zeros(len(p))
 for group in body.vertex_groups:
  bone=rig.data.bones.get(group.name)
  if bone is None or not bone.use_deform:continue
  w=np.array([next((g.weight for g in v.groups if g.group==group.index),0.) for v in body.data.vertices])
  if not w.any():continue
  transform=np.array(rig.matrix_world@rig.pose.bones[group.name].matrix@bone.matrix_local.inverted()@rig.matrix_world.inverted()@body.matrix_world)
  result+=w[:,None]*(h@transform.T);mass+=w
 return normalize_linear_blend(result[:,:3],mass)

def normalize_linear_blend(points,mass):
 points,mass=np.asarray(points,float),np.asarray(mass,float)
 if points.shape!=(len(mass),3) or not np.isfinite(points).all() or not np.isfinite(mass).all() or np.any(mass<=0):raise ValueError('Invalid linear skinning influence')
 return points/mass[:,None]
