"""R40 post-guard protection and explicit front-metric reporting."""
import re,math
import numpy as np

def sentinels_preserved(before,after):
    return (bool(before) and before.keys()==after.keys() and
            all(np.isfinite(before[k]).all() and np.isfinite(after[k]).all() and
                np.array_equal(before[k],after[k]) for k in before))

def front_comparison(parent_log,current_log):
    def parse(log):
        def value(pattern):
            matches=re.findall(pattern,log,re.M)
            if len(matches)!=1:raise ValueError('Missing or ambiguous front metric')
            number=float(matches[0])
            if not math.isfinite(number):raise ValueError('Nonfinite front metric')
            return number
        return {'edge_130':value(r'^[.FEes]*FRONT_EDGE_130\s+(\S+)\s*$'),
                'sentinel_120':value(r'^[.FEes]*FRONT_TARGET_FIT\s+120(?:\.0)?\s+(\S+)\s*$'),
                'sentinel_145':value(r'^[.FEes]*FRONT_TARGET_FIT\s+145(?:\.0)?\s+(\S+)\s*$')}
    a,b=parse(parent_log),parse(current_log)
    delta={k:b[k]-a[k] for k in a}
    return {'parent':a,'current':b,'changes':delta,'edge_change_degrees':delta['edge_130'],
            'worsened':[k for k in a if delta[k]>1e-6]}
