"""Pure calculations shared by Blender shoulder-layer diagnostics."""
from __future__ import annotations

import math
from typing import Any

LAYER_KEYS={
    'abduction':('HGPT_SHOULDER_CORR_L','HGPT_SHOULDER_CORR_R'),
    'flexion':('HGPT_SHOULDER_FLEX_L','HGPT_SHOULDER_FLEX_R'),
    'scapular':('HGPT_SHOULDER_SCAP_L','HGPT_SHOULDER_SCAP_R'),
}
REQUIRED_KEYS=tuple(name for pair in LAYER_KEYS.values() for name in pair)


def activation_snapshot(scene: Any, body: Any, rig: Any) -> dict[str,Any]:
    shape_keys=getattr(getattr(body,'data',None),'shape_keys',None)
    blocks=getattr(shape_keys,'key_blocks',None)
    if blocks is None: raise ValueError('missing shoulder corrective configuration: no shape keys')
    missing=[name for name in REQUIRED_KEYS if name not in blocks]
    if missing: raise ValueError('missing shoulder corrective configuration: '+', '.join(missing))
    values={name:float(blocks[name].value) for name in REQUIRED_KEYS}
    if not all(math.isfinite(value) for value in values.values()):
        raise ValueError('non-finite shoulder corrective activation')
    grouped={layer:{'left':values[pair[0]],'right':values[pair[1]]} for layer,pair in LAYER_KEYS.items()}
    active=[layer for layer in LAYER_KEYS if max(abs(grouped[layer]['left']),abs(grouped[layer]['right']))>1e-9]
    return {
        'values':values,
        'layers':grouped,
        'active_layers':active,
        'symmetry_error':{layer:abs(grouped[layer]['left']-grouped[layer]['right']) for layer in LAYER_KEYS},
    }


def _distance(a, b):
    if len(a)!=3 or len(b)!=3: raise ValueError('vertex coordinates must be 3D')
    value=math.sqrt(sum((float(a[i])-float(b[i]))**2 for i in range(3)))
    if not math.isfinite(value): raise ValueError('non-finite vertex displacement')
    return value


def summarize_zone_displacement(states: dict[str,list], zones: dict[str,dict]) -> dict[str,Any]:
    if 'rest' not in states: raise ValueError('rest state missing')
    rest=states['rest']; count=len(rest)
    if not count: raise ValueError('rest state has no vertices')
    result={'vertex_count':count,'states':{}}
    for state_name,coords in states.items():
        if len(coords)!=count: raise ValueError('state vertex count differs: '+state_name)
        if state_name=='rest': continue
        state_row={'zones':{}}
        for zone_name,zone in zones.items():
            left=list(zone.get('left',[]));right=list(zone.get('right',[]));indices=left+right
            if not indices: raise ValueError('zone has no vertices: '+zone_name)
            if any(not isinstance(i,int) or i<0 or i>=count for i in indices):
                raise ValueError('zone vertex index out of range: '+zone_name+f' (mesh count {count}, min {min(indices)}, max {max(indices)})')
            distances={i:_distance(coords[i],rest[i]) for i in indices}
            symmetry=[]
            for li,ri in zip(left,right): symmetry.append(abs(distances[li]-distances[ri]))
            state_row['zones'][zone_name]={
                'vertex_count':len(indices),
                'mean_displacement':sum(distances.values())/len(distances),
                'max_displacement':max(distances.values()),
                'symmetry_error':max(symmetry) if symmetry else None,
            }
        result['states'][state_name]=state_row
    return result


def summarize_activation_arc(samples: list[dict[str,Any]]) -> dict[str,Any]:
    if not samples: raise ValueError('activation arc has no samples')
    angles=[float(row['angle_deg']) for row in samples]
    if any(not math.isfinite(x) for x in angles) or any(b<=a for a,b in zip(angles,angles[1:])):
        raise ValueError('activation arc angles must be finite and strictly increasing')
    layer_names=[]
    for row in samples:
        for name in row.get('values',{}):
            if name not in layer_names: layer_names.append(name)
    output={'sample_count':len(samples),'angles_deg':angles,'layers':{}}
    for layer in layer_names:
        values=[float(row.get('values',{}).get(layer,0.0)) for row in samples]
        if any(not math.isfinite(x) for x in values): raise ValueError('non-finite activation in '+layer)
        reversals=[]
        for i,(before,after) in enumerate(zip(values,values[1:])):
            if after < before-1e-9:
                reversals.append({'from_angle_deg':angles[i],'to_angle_deg':angles[i+1],'drop':round(before-after,10)})
        output['layers'][layer]={
            'values':values,
            'minimum':min(values),
            'maximum':max(values),
            'max_step':max((abs(b-a) for a,b in zip(values,values[1:])),default=0.0),
            'monotone_non_decreasing':not reversals,
            'reversals':reversals,
        }
    return output
