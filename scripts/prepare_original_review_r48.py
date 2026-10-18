"""Preserve every parent response array; add an explicit actual-R47 target."""
import sys
import numpy as np

def prepare(source,approved,destination,initial):
    with np.load(source) as z:d={k:z[k] for k in z.files}
    with np.load(approved) as z:delta=z['delta']
    target=d['base'][25]+np.einsum('nij,nj->ni',d['mat'][25],np.einsum('kn,knj->nj',d['weight'][25],delta))
    d.update(r48_allowed=d['r47_allowed'].copy(),r48_profile_target_points=target)
    np.savez_compressed(destination,**d)
    np.savez_compressed(initial,delta=np.zeros_like(delta))

if __name__=='__main__':prepare(*sys.argv[1:5])
