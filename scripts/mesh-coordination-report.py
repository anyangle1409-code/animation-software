"""Tabulate mesh-coordination-report.sh logs: arm-to-chest distance per exercise,
and equipment within 10 mm or pressing a pad, per character."""
import collections, re, sys

out, runs = sys.argv[1], sys.argv[2:]
baseline = {m.group(1): float(m.group(2)) * 1000 for m in re.finditer(
    r'^\s+([a-z_]+):\s+([0-9.]+),', open('src/exercises/selfCollision.test.ts').read(), re.M)}
closest, clearance = collections.defaultdict(dict), collections.defaultdict(dict)
for run in runs:
    text = open(f'{out}/{run}.log').read()
    for m in re.finditer(r'^\s+([a-z_]+)\s+[LR]\s+closest\s+([-0-9.]+) mm', text, re.M):
        closest[m.group(1)][run] = min(closest[m.group(1)].get(run, 1e9), float(m.group(2)))
    for m in re.finditer(r'^\s+(PASS|FAIL)\s+([a-z_]+)\s+([a-z_]+)\s+(closest|deepest)\s+([-0-9.]+) mm\s+inside (\d+)', text, re.M):
        ok, exercise, item, kind, value, inside = m.groups()
        clearance[(exercise, item, kind)][run] = (float(value), int(inside))
cell = lambda v: f'{v:.2f}' if v is not None else '—'
print('| Exercise | ' + ' | '.join(runs) + ' | Last vs baseline |')
print('|---|' + '---:|' * len(runs) + '---|')
for exercise in sorted(closest, key=lambda e: closest[e].get(runs[-1], 99)):
    last = closest[exercise].get(runs[-1])
    below = last is not None and exercise in baseline and last < baseline[exercise] - 1.0
    print(f'| `{exercise}` | ' + ' | '.join(cell(closest[exercise].get(r)) for r in runs) + f" | {'below' if below else 'within'} |")
print()
print('| Exercise | Item | Measure | ' + ' | '.join(runs) + ' |')
print('|---|---|---|' + '---:|' * len(runs))
for key in sorted(clearance):
    values = [clearance[key].get(r) for r in runs]
    if key[2] == 'deepest' or min(v[0] for v in values if v) < 10:
        print(f'| `{key[0]}` | {key[1]} | {key[2]} | ' + ' | '.join(
            (f'{v[0]:.2f}' + (f' ({v[1]} inside)' if v[1] and key[2] == 'closest' else '')) if v else '—' for v in values) + ' |')
