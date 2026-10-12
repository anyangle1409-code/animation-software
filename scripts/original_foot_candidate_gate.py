"""Fail-closed eligibility for a mesh-only foot proportion proposal."""
import math

def assess(heel_backward_m,reference_forward_stations_m,target_length_m,semantics_resolved):
    if any(type(x) not in (float,int) or not math.isfinite(x) for x in (heel_backward_m,target_length_m)):
        raise ValueError('Finite numeric heel/target required')
    if heel_backward_m<0 or target_length_m<=heel_backward_m or type(semantics_resolved) is not bool:
        raise ValueError('Invalid footprint extent or semantic status')
    if not isinstance(reference_forward_stations_m,(list,tuple)) or not reference_forward_stations_m:
        raise ValueError('Nonempty source station inventory required')
    if any(type(x) not in (float,int) or not math.isfinite(x) for x in reference_forward_stations_m):
        raise ValueError('Finite source stations required')
    required_forward=max(reference_forward_stations_m)
    target_forward=target_length_m-heel_backward_m
    minimum_length=heel_backward_m+required_forward
    if not math.isfinite(minimum_length):raise ValueError('Footprint overflow')
    protrusion=max(0.0,required_forward-target_forward)
    blockers=[]
    if protrusion>1e-7:blockers.append('UNCHANGED_REFERENCE_POINTS_OUTSIDE_TARGET_SKIN_ENVELOPE')
    if not semantics_resolved:blockers.append('UNRESOLVED_REFERENCE_STATION_SEMANTICS')
    return {'mesh_only_candidate_allowed':not blockers,'blockers':blockers,
      'target_length_m':target_length_m,'target_forward_station_m':target_forward,
      'minimum_reference_envelope_length_m':minimum_length,'reference_protrusion_m':protrusion,
      'skeleton_changes_required':False,'production_approved':False}
