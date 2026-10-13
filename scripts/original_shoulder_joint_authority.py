"""Read-only provisional SC/AC/GH contract; never authorizes source changes."""
import math
from original_shoulder_bind_semantics import validate_frame
RECORD='ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json'
def extract(record):
    joints={}
    for side in ('left','right'):
        for joint,marker_name,bone,endpoint,control in (
            ('SC','sternoclavicular','clavicle','head_m','clavicle'),
            ('AC','acromioclavicular','clavicle','tail_m','scapula'),
            ('GH','glenohumeral','humerus','head_m','humerus')):
            marker=record['joint_markers'][marker_name+'_'+side]
            if marker['fit_status']!='FITTED_UNVERIFIED_OPERATION':
                raise ValueError('Unexpected source fit status; approval requires separate evidence')
            centre=marker['centre_m']
            if math.dist(centre,record['bones'][bone+'_'+side][endpoint])>1e-8:
                raise ValueError(joint+' anchor mismatch')
            columns=marker['frame_axes_columns_XYZ']
            frame=validate_frame([[columns[c][r] for c in range(3)]+[centre[r]] for r in range(3)]+[[0,0,0,1]])
            joints[joint+'_'+side]={'source_marker':marker_name+'_'+side,
                'world_frame_row_major':frame,'fit_status':marker['fit_status'],
                'method':marker['method'],'frame_bone':marker['frame_bone'],
                'authored_control':control+'_'+side,
                'anchor_semantics':bone+'_'+side+'.'+endpoint,
                'control_orientation_is_joint_frame':False}
    return {'joints':joints,'anatomical_approval':False,'production_approved':False,
        'retarget_installed':False,'axes_authority':'source fitted marker axes; unverified operation',
        'world_conventions':record['conventions']}
