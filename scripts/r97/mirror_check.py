import numpy as np
from scipy.spatial import cKDTree
d=np.load('rest.npz'); co=d['co']
m=co*np.array([-1,1,1]); dist,idx=cKDTree(co).query(m)
print('mirror max err', dist.max(), 'p99', np.percentile(dist,99), 'self-mapped', np.sum(idx==np.arange(len(co))), 'bijective', len(set(idx))==len(co))
np.save('mirror_idx.npy', idx)
