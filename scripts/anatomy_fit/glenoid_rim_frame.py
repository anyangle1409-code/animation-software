"""Measured rim orientation only; no humeral-head centre or standing pose."""
import importlib.util,json,math
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('scapula',Path(__file__).with_name('scapula_landmark_model.py'))
scapula=importlib.util.module_from_spec(spec);spec.loader.exec_module(scapula)
def derive(points):
 p=np.asarray(points,dtype=float)
 if p.shape!=(29,3) or not np.isfinite(p).all():raise ValueError('29 finite local XYZ landmarks required')
 rim=p[[14,15,16,17]];centre=rim.mean(axis=0)
 _,sv,V=np.linalg.svd(rim-centre,full_matrices=False)
 if sv[1]<1e-8:raise ValueError('glenoid rim plane is degenerate')
 if sv[1]-sv[2]<1e-8*sv[0]:raise ValueError('glenoid rim has no uniquely resolved plane normal')
 ap=p[16]-p[15];si=p[17]-p[14];cross=np.cross(ap,si)
 if np.linalg.norm(cross)<1e-8:raise ValueError('rim directions collapse')
 n=V[-1]
 if np.dot(n,cross)<0:n=-n
 if n[2]<=0:raise ValueError('rim chirality must face lateral in right local frame')
 y=si-n*np.dot(si,n)
 if np.linalg.norm(y)<1e-8:raise ValueError('superior tangent collapses')
 y=y/np.linalg.norm(y);x=np.cross(y,n)
 if np.dot(x,ap)<=0:raise ValueError('anterior tangent sign mismatch')
 R=np.column_stack((x,y,n))
 return {'rim_centroid_local_mm':centre.tolist(),'axes_local':R.tolist(),'axis_columns':['anterior_tangent','superior_tangent','lateral_facing_rim_normal'],'rim_plane_rms_mm':float(np.sqrt(np.mean(((rim-centre)@n)**2))),'landmark_19_signed_offset_mm':float(np.dot(p[18]-centre,n)),'normal_anterior_projection_deg':math.degrees(math.atan2(n[0],n[2])),'normal_superior_projection_deg':math.degrees(math.atan2(n[1],n[2])),'GH_centre_local_mm':None}
def bilateral(frame):
 R=np.array([[0,0,-1],[-1,0,0],[0,1,0]],dtype=float)
 M=np.diag([-1,1,1]);local=np.asarray(frame['axes_local']);centre=np.asarray(frame['rim_centroid_local_mm'])
 right=R@local;left=M@right@np.diag([-1,1,1])
 return {'right':{'axes_HGPT':right.tolist(),'rim_centroid_relative_mm':(R@centre).tolist(),'axis_columns':['anterior_tangent','superior_tangent','outward_normal']},'left':{'axes_HGPT':left.tolist(),'rim_centroid_relative_mm':(M@R@centre).tolist(),'axis_columns':['posterior_tangent','superior_tangent','outward_normal']},'pose':'Relative basis fixture only; no standing thorax rotation or translation.','left_policy':'Reflect geometry then reverse first tangent to retain determinant +1; anatomical anterior vector is negative first axis on left.'}
def build():
 b=ROOT/'ORIGINAL_V1_WORK/anatomy';shape=json.loads((b/'canonical_scapula_measured_landmark_model_v1.json').read_text())
 points=np.asarray(shape['groups']['asymptomatic_no_FTT_males']['stature_conditioned_local_landmarks']['predicted']).reshape(29,3)
 predicted=derive(points)
 subjects=[s for s in scapula.load_subjects() if s['sex']=='Male' and s['symptoms']=='Asym' and s['FTT']=='no']
 results=[derive(scapula.anatomical_local(s['points_mm'])[0]) for s in subjects]
 summary={}
 for key in ['normal_anterior_projection_deg','normal_superior_projection_deg','rim_plane_rms_mm']:
  values=np.array([r[key] for r in results]);summary[key]={'mean':float(values.mean()),'SD':float(values.std(ddof=1)),'range':[float(values.min()),float(values.max())]}
 return {'schema_version':1,'status':'PROVISIONAL_MEASURED_RIM_ORIENTATION_ONLY','freeze_ready':False,'source':'LEE_2024_SCAPULA_RAW_3D','source_shape_file':'canonical_scapula_measured_landmark_model_v1.json','source_workbook_sha256':__import__('hashlib').sha256(scapula.DEFAULT_SOURCE.read_bytes()).hexdigest(),'definition':'Least-squares plane through LM15 inferior, LM16 posterior, LM17 anterior, LM18 superior rim; centroid is arithmetic rim landmark centroid, not joint or GH centre.','local_axes':['anterior','superior','lateral_right_scapula'],'subject_count':len(subjects),'subject_summary':summary,'stature_conditioned_shape_rim_frame':predicted,'bilateral_relative_frames':bilateral(predicted),'absolute_SC_AC_GH_centres_m':{'SC':None,'AC':None,'GH':None},'limitations':['Rim landmarks are nonplanar; residual is reported, not forced to zero.','Projection angles use the measured scapular landmark basis, not clinical Friedman/version/inclination definitions.','Frame of stature-conditioned mean landmarks differs from mean subject orientation; both are retained.','No articular cartilage, sphere fit, complete bone envelope or independent numerical freeze.','Neutral thorax pose and global centres remain unresolved.']}
if __name__=='__main__':
 r=build();(ROOT/'ORIGINAL_V1_WORK/anatomy/canonical_glenoid_rim_frame_v1.json').write_text(json.dumps(r,indent=2,allow_nan=False)+'\n');print(json.dumps({'subjects':r['subject_count'],'predicted_frame':r['stature_conditioned_shape_rim_frame']}))
