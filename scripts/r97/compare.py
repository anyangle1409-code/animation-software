import json, sys, numpy as np
rows = {}
for tag in sys.argv[1:]:
    r = json.load(open(f'mfull_{tag}/matrix_report.json'))['poses']
    rows[tag] = r
names = list(rows[sys.argv[1]].keys())
def agg(tag, key, fn, sel=None):
    v = [rows[tag][n][key] for n in names if sel is None or sel(n)]
    return fn(v)
groups = {'all': None, 'le120': lambda n: not any(f'_{t}_' in n for t in ('150','170')) , 'overhead': lambda n: any(f'_{t}_' in n for t in ('150','170')), 'exercise': lambda n: n.endswith('like') or n.startswith(('horizontal','arm_behind','bent','lateral','front_raise'))}
print(f"{'tag':6s} {'group':9s} {'SI_sum':>7s} {'SI_max':>6s} {'emin':>6s} {'p1min':>6s} {'p99max':>7s} {'emax':>6s} {'shrink':>7s}")
for tag in rows:
    for g, sel in groups.items():
        print(f"{tag:6s} {g:9s} {agg(tag,'self_intersections',sum,sel):7d} {agg(tag,'self_intersections',max,sel):6d} {agg(tag,'edge_ratio_min',min,sel):6.3f} {agg(tag,'edge_ratio_p1',min,sel):6.3f} {agg(tag,'edge_ratio_p99',max,sel):7.2f} {agg(tag,'edge_ratio_max',max,sel):6.2f} {min(rows[tag][n]['transition_shrink_min']['l'] for n in names if sel is None or sel(n)):7.3f}")
