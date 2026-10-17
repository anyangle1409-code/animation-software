"""Read-only native BVH contact detection on the validated response geometry."""
import sys,json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
source,solution,dest=sys.argv[-3:]
z=np.load(source);delta=np.load(solution)['delta'];faces=z['faces'];fs=[set(f) for f in faces]
def pairs(p):
 tree=BVHTree.FromPolygons([Vector(v) for v in p],faces,all_triangles=True)
 return {(a,b) for a,b in tree.overlap(tree) if a<b and not(fs[a]&fs[b])}
contacts=[];samples=[]
for s,base in enumerate(z['base']):
 p=base+np.einsum('nij,nj->ni',z['mat'][s],np.einsum('kn,knj->nj',z['weight'][s],delta))
 before=pairs(base);after=pairs(p);extra=after-before if len(after)>len(before) else set()
 contacts.extend({'sample':s,'a':int(a),'b':int(b)} for a,b in sorted(extra))
 samples.append({'sample':s,'parent_pairs':len(before),'current_pairs':len(after)})
print('R39_NATIVE_CONTACTS',len(contacts),flush=True)
open(dest,'w').write(json.dumps({'contacts':contacts,'sample_count':82,'samples':samples},indent=2)+'\n')
