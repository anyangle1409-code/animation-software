import sys, numpy as np
SP="/tmp/claude-0/-home-user-animation-software/b0b01a8a-22fb-52cd-85ad-39c74496ecb2/scratchpad"
co=np.load(SP+"/r76/rest_co.npy"); F=np.load(SP+"/r76/faces.npy"); nv=len(co)
nb=[[] for _ in range(nv)]
for a,b,c in F: nb[a]+=[b,c]; nb[b]+=[a,c]; nb[c]+=[a,b]
nb=[np.unique(n) for n in nb]; rows=np.repeat(np.arange(nv),[len(n) for n in nb]); cols=np.concatenate(nb); deg=np.array([len(n) for n in nb],float)
def lap(X):
    acc=np.zeros_like(X); np.add.at(acc,rows,X[cols]); return acc/deg[:,None]-X
reg=(np.abs(co[:,0])>0.17)&(np.abs(co[:,0])<0.31)&(co[:,2]>1.28)&(co[:,2]<1.56)
r0=np.linalg.norm(lap(co),axis=1)
for p in sys.argv[1:]:
    P=co+np.load(p)["offsets"]; r=np.linalg.norm(lap(P),axis=1); d=r-r0
    print(p.split('/')[-2], "deltoid-region extra roughness: p95 %.2f mm  max %.2f mm  verts>0.5mm %d"%(np.percentile(d[reg],95)*1000,d[reg].max()*1000,(d[reg]>0.0005).sum()))
