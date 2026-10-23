"""Fail-closed completeness and existing deformation thresholds, not anatomy approval."""
import math

METRICS = ('collapse_lt_0_1', 'stretch_gt_2', 'self_intersecting_pairs')


def summarize(benchmarks, expected_names, frames):
    complete = set(benchmarks) == set(expected_names) and bool(expected_names)
    failures = []
    for name in expected_names:
        rows = benchmarks.get(name, {}).get('frames', [])
        complete = complete and len(rows) == frames
        for i, row in enumerate(rows):
            for metric in METRICS:
                value = row.get(metric)
                valid = isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0
                if not valid or value != 0:
                    failures.append({'benchmark': name, 'frame': i, 'metric': metric, 'value': value})
    return {'complete': complete, 'quality_pass': complete and not failures, 'quality_failures': failures,
            'scope': 'zero self-intersections, area collapse below 0.1 and stretch above 2; diagnostic only, no anatomical approval'}


def verified_remesh_count(report, source_sha256, measured_count):
    """Only permit a count already linked to this exact source by native verification."""
    summary = report.get('summary', {})
    if (report.get('sha256') != source_sha256 or summary.get('fail') != 0
            or summary.get('pass', 0) <= 0 or measured_count <= 0
            or report.get('measured', {}).get('body_vertices') != measured_count):
        raise ValueError('Native source identity/count verification mismatch')
    return measured_count
