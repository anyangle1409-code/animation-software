"""Compare a recomputed JSON report with its committed copy.

Structure, keys, strings, integers, booleans and nulls must match exactly. Floats must agree to a
relative 1e-9 (absolute 1e-12 near zero): recomputation on another platform or NumPy build can change
the last binary digit, which is not a change in the evidence.
"""
import math


def report_differences(stored, actual, path='$', rel=1e-9, abs_tol=1e-12):
    if isinstance(stored, bool) or isinstance(actual, bool) or stored is None or actual is None:
        return [] if stored is actual or (type(stored) is type(actual) and stored == actual) else [f'{path}: {stored!r} != {actual!r}']
    if isinstance(stored, float) or isinstance(actual, float):
        if not isinstance(stored, (int, float)) or not isinstance(actual, (int, float)):
            return [f'{path}: {stored!r} != {actual!r}']
        if math.isnan(stored) and math.isnan(actual):
            return []
        return [] if math.isclose(stored, actual, rel_tol=rel, abs_tol=abs_tol) else [f'{path}: {stored!r} != {actual!r}']
    if type(stored) is not type(actual):
        return [f'{path}: type {type(stored).__name__} != {type(actual).__name__}']
    if isinstance(stored, dict):
        if set(stored) != set(actual):
            return [f'{path}: keys differ {sorted(set(stored) ^ set(actual))}']
        return [d for k in stored for d in report_differences(stored[k], actual[k], f'{path}.{k}', rel, abs_tol)]
    if isinstance(stored, list):
        if len(stored) != len(actual):
            return [f'{path}: length {len(stored)} != {len(actual)}']
        return [d for i, (a, b) in enumerate(zip(stored, actual)) for d in report_differences(a, b, f'{path}[{i}]', rel, abs_tol)]
    return [] if stored == actual else [f'{path}: {stored!r} != {actual!r}']
