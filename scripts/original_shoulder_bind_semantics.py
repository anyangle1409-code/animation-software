"""Diagnostic bind semantics; no production retarget or scene mutation."""
import math

def validate_frame(matrix):
    """Copy a finite, proper rigid row-major world matrix; reject guessing."""
    if not isinstance(matrix,(list,tuple)) or len(matrix)!=4:
        raise ValueError('Expected four matrix rows')
    if any(not isinstance(row,(list,tuple)) or len(row)!=4 for row in matrix):
        raise ValueError('Expected four coordinates per row')
    if any(type(x) not in (float,int) or not math.isfinite(x) for row in matrix for x in row):
        raise ValueError('Expected finite numeric frame')
    m=tuple(tuple(float(x) for x in row) for row in matrix)
    if any(abs(m[3][j]-(1 if j==3 else 0))>1e-9 for j in range(4)):
        raise ValueError('Expected affine frame')
    if any(abs(sum(m[r][k]*m[c][k] for k in range(3))-(r==c))>1e-6 for r in range(3) for c in range(3)):
        raise ValueError('Scale/shear/singular frame not supported')
    det=(m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])
        -m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])
        +m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))
    if abs(det-1)>1e-6:raise ValueError('Reflection not supported')
    return m

def multiply(a,b):
    a,b=validate_frame(a),validate_frame(b)
    return validate_frame(tuple(tuple(sum(a[r][k]*b[k][c] for k in range(4)) for c in range(4)) for r in range(4)))

def inverse_rigid(matrix):
    m=validate_frame(matrix)
    r=[list(m[k][j] for k in range(3)) for j in range(3)]
    return tuple(tuple(r[j]+[-sum(r[j][k]*m[k][3] for k in range(3))]) for j in range(3))+((0,0,0,1),)

def bind_offset(source_rest,target_rest):
    """O=inv(S)*T preserves target rest; O translation is a retained gap."""
    return multiply(inverse_rigid(source_rest),target_rest)

def transfer_world(source_pose,offset):
    """P*O is a mathematical candidate; not anatomical retarget acceptance."""
    return multiply(source_pose,offset)

def separation_m(source_world,target_world):
    s,t=validate_frame(source_world),validate_frame(target_world)
    distance=math.dist([s[k][3] for k in range(3)],[t[k][3] for k in range(3)])
    if not math.isfinite(distance):raise ValueError('Non-finite frame separation')
    return distance
