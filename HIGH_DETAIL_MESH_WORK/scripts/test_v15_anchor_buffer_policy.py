"""Focused contract test for the V15f Route A movement policy."""
from __future__ import annotations

from v15_anchor_buffer_policy import movement_cap_mm, report_is_safe


assert movement_cap_mm(0) == 0.0
assert movement_cap_mm(1) == 0.0
assert movement_cap_mm(2) == 0.25
assert movement_cap_mm(3) == 0.55
assert movement_cap_mm(4) == 0.0

safe = {
    "direct_contact_max_move_mm": 0.0,
    "direct_contact_weight_rows_changed": 0,
    "eligible_anchor_vertices": 10,
    "maximum_allowed_move_mm": 0.55,
    "topology_changes_allowed": False,
    "weights_changes_allowed": False,
}
assert report_is_safe(safe)

unsafe = dict(safe, direct_contact_max_move_mm=0.00001)
assert not report_is_safe(unsafe)
unsafe = dict(safe, direct_contact_weight_rows_changed=1)
assert not report_is_safe(unsafe)
unsafe = dict(safe, eligible_anchor_vertices=0)
assert not report_is_safe(unsafe)

print("V15_ANCHOR_BUFFER_POLICY_TEST_PASS")
