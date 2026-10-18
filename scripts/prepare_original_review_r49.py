"""Copy exact failed-R48 response data; name the unchanged R49 target/scope."""
import sys
import numpy as np

def prepare(source,destination,initial):
    with np.load(source) as z:d={k:z[k] for k in z.files}
    d.update(r49_allowed=d['r48_allowed'].copy(),r49_profile_target_points=d['r48_profile_target_points'].copy())
    np.savez_compressed(destination,**d)
    np.savez_compressed(initial,delta=np.zeros_like(d['delta']))

if __name__=='__main__':prepare(*sys.argv[1:4])
