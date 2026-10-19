"""Finite-iteration study helpers. No acceptance or save policy is relaxed."""
import numpy as np
def shrink_ball_dual(value,radius):
 return value*np.maximum(0.,1.-np.asarray(radius)[...,None]/np.maximum(np.linalg.norm(value,axis=-1,keepdims=True),1e-30))
def study_status(motion_mm,step_mm,outline_mm):
 return dict(status='UNSAVED_TEMPORAL_STUDY_NOT_ACCEPTED',approved=False,model_saved=False,shape_repair_complete=False,
  motion_and_step_goals_met=bool(motion_mm<=.5 and step_mm<=3.),actual_outline_guard_met=bool(outline_mm<=1.),
  motion_excess_mm=float(motion_mm),maximum_adjacent_mm=float(step_mm),approved_outline_error_mm=float(outline_mm),
  note='Finite iteration, source-knot projection and workflow success do not mean native surface safety or owner approval.')

def retention_key(row):
 if row['maximum_material_mm']>45.+1e-7 or row['approved_outline_error_mm']>1.+1e-8:return None
 ratios=(row['motion_excess_mm']/.5,row['maximum_adjacent_mm']/3.,row.get('early_outward_increment_mm',0.)/.05)
 feasible=all(v<=1. for v in ratios)
 return (0 if feasible else 1,max(ratios),row['motion_excess_mm'])
