from pathlib import Path
import numpy as np,json,sys
if len(sys.argv)!=4:raise SystemExit('usage: audit SOURCE.npz SOLUTION.npz OUTPUT.json')
source,solution,output=map(Path,sys.argv[1:])
with np.load(source) as z:d={k:z[k] for k in z.files}
delta=np.load(solution)['delta'];rest=d['rest'];faces=d['faces']
now=d['base'][:41]+np.einsum('snij,snj->sni',d['mat'][:41],np.einsum('skn,knj->snj',d['weight'][:41],delta))
marked=now[25];a=faces[:,[0,1,2]].ravel();b=faces[:,[1,2,0]].ravel();za=marked[a,2];zb=marked[b,2];supports=[]
for side in (-1,1):
 for view,n in [('back',np.array([side,0.,0.])),('three_quarter',np.array([side,-1.,0.])/np.sqrt(2.))]:
  for height in np.arange(1.18,1.62,.005):
   use=((za<=height)&(zb>height))|((zb<=height)&(za>height));aa,bb,az,bz=a[use],b[use],za[use],zb[use];t=(height-az)/(bz-az);q=(1-t[:,None])*marked[aa]+t[:,None]*marked[bb];valid=q[:,0]*side>.08;aa,bb,q=aa[valid],bb[valid],q[valid];j=(q@n).argmax();supports.extend((int(aa[j]),int(bb[j])))
supports=np.unique(supports)
mask=(abs(rest[:,0])>.08)&(abs(rest[:,0])<.25)&(rest[:,2]>1.27)&(rest[:,2]<1.49)&(rest[:,1]>.025);ids=np.flatnonzero(mask)
excess=(np.linalg.norm(np.diff(now[:,ids],n=2,axis=0),axis=2)-np.linalg.norm(np.diff(d['base'][:41,ids].astype(float),n=2,axis=0),axis=2))*1000
maximum=excess.max(0);intersect=np.isin(ids,supports)
out={'diagnostic_only':True,'scope':'Current R51 active outline-support edges at original marked-pose stations; nonlinear support can change after editing.','motion_mask_count':len(ids),'outline_support_vertex_count':len(supports),'overlap_count':int(intersect.sum()),'worst_vertex_is_current_outline_support':bool(21317 in supports),'violating_motion_vertices':int((maximum>.5).sum()),'violating_motion_outline_support_vertices':int(((maximum>.5)&intersect).sum()),'worst_outline_support_motion_excess_mm':None if not intersect.any() else float(maximum[intersect].max()),'top_motion_vertices':[{'vertex':int(ids[j]),'excess_mm':float(maximum[j]),'current_outline_support':bool(intersect[j])} for j in np.argsort(maximum)[-12:][::-1]]}
print(json.dumps(out,indent=2));output.write_text(json.dumps(out,indent=2)+'\n')
