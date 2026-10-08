"""Counterexamples for printed conventions; no proposed rib geometry or solver."""
import json
import math
import sys
from pathlib import Path

import numpy as np

out = Path(sys.argv[1])
if out.exists():
    raise FileExistsError('Retain immutable equation review')
xpk, ypk = .3, .32
alpha = math.atan2(ypk, xpk)
# Eq 2.8/2.9 with Bp=0 is an independent unit-circle limit.
# Standard Python/MATLAB atan2(y, x) applied literally to Eq 2.11.
theta_cut = math.pi + alpha
dx, dy = -math.sin(theta_cut), math.cos(theta_cut)
literal_angle = math.atan2(-dx, -dy)
assert abs(literal_angle + alpha) < 1e-12
rotation = np.array([[math.cos(alpha), -math.sin(alpha)],
                     [math.sin(alpha), math.cos(alpha)]])
rotated_derivative = rotation @ np.array([dx, dy])
# The peak must be stationary in normalized Y; literal Eq 2.11 fails.
assert abs(rotated_derivative[1]) > .01
theta_stationary = math.pi / 2 - alpha
independent_derivative = rotation @ np.array([-math.sin(theta_stationary), math.cos(theta_stationary)])
assert abs(independent_derivative[1]) < 1e-12
# Printed second Eq 2.18: theta_cut > y(2*atan(sqrt(Bp^2+1)+Bp)+pi).
# At fixed alpha/Bp it is independent of phi_pia, though the text describes
# its purpose as avoiding a phi_pia upper-angle infeasibility.
second_rhs = math.sin(2 * math.atan(1) + math.pi)
constraints = [{'phi_pia_deg': phi, 'first_constraint': math.radians(phi) > alpha,
                'second_literal_constraint': theta_cut > second_rhs}
               for phi in [80, 120, 150]]
assert all(r['first_constraint'] and r['second_literal_constraint'] for r in constraints)
# Eq 2.16 uses row-vector translation; Eq 2.17 prints column-vector T*p.
tx, ty, scale = .4, .2, 1.7
translation = np.array([[1., 0, 0], [0, 1, 0], [-tx, -ty, 1]])
scaling = np.diag([scale, scale, 1])
row_rotation = np.array([[math.cos(alpha), math.sin(alpha), 0],
                         [-math.sin(alpha), math.cos(alpha), 0], [0, 0, 1]])
matrix = translation @ scaling @ row_rotation
source_origin = np.array([tx, ty, 1])
row_result, printed_column_result = source_origin @ matrix, matrix @ source_origin
np.testing.assert_allclose(row_result, [0, 0, 1], atol=1e-12)
assert not np.allclose(printed_column_result, [0, 0, 1])
report = {'status': 'CONFIRMED_LITERAL_NOTATION_COUNTEREXAMPLES_NOT_A_SOLVER',
          'unit_circle_case': {'Xpk': xpk, 'Ypk': ypk, 'Bp': 0, 'alpha_rad': alpha,
                              'literal_theta_cut_rad': theta_cut, 'literal_atan2_residual_rad': literal_angle + alpha,
                              'rotated_Y_derivative_at_literal_cut': float(rotated_derivative[1]),
                              'independent_stationary_Y_derivative': float(independent_derivative[1])},
          'printed_second_constraint': {'rhs': second_rhs, 'phi_cases': constraints,
                                       'warning': 'Not phi-dependent; not accepted as the described upper-angle feasibility guard.'},
          'matrix_convention': {'row_origin_result': row_result.tolist(),
                                'printed_column_origin_result': printed_column_result.tolist()},
          'source_typo_corrected_automatically': False, 'proximal_branch_accepted': False,
          'anatomical_coordinates_selected': False}
out.write_text(json.dumps(report, indent=2) + '\n')
