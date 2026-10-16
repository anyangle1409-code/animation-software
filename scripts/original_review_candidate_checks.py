"""Numerical acceptance for review candidates; never implies visual acceptance."""
import math
import re

def acceptance(invariants, front_exit, front_log, press_rows, regressions, guard_report):
    front_ok = front_exit == 0 and bool(re.search(r"^OK$", front_log, re.M))
    volume = float(press_rows[-1]["volume_pct"]) if press_rows else float("nan")
    # Preserve the original R33 test's strict lockout bound.
    volume_ok = math.isfinite(volume) and abs(volume) < 2.5
    motion_ok = all(row["ht"] <= 95.0 or (row["pairs"] == 0 and row["collapse"] == 0) for row in press_rows)
    guard_ok = (isinstance(guard_report, dict)
                and guard_report.get("sample_count") == 82
                and set(guard_report.get("paths", ())) == {"press", "benchmark_press"}
                and guard_report.get("violations") == [])
    checks = {"front_test_process": front_ok, "original_lockout_volume": volume_ok,
              "original_guards_rechecked": guard_ok,
              "original_post95_collision_rule": motion_ok,
              "preservation": bool(invariants) and all(invariants.values()),
              "no_frame_count_regressions": not regressions}
    return {"passed": all(checks.values()), "checks": checks}
