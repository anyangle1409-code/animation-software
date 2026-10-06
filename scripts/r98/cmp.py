import json, sys
tags=sys.argv[1:]
R={t:json.load(open(f'/home/user/r98/m_{t}/matrix_report.json'))['poses'] for t in tags}
poses=list(R[tags[0]])
print('pose'.ljust(26)+''.join(f'{t:>14}' for t in tags))
for p in poses:
    print(p.ljust(26)+''.join(f"{R[t][p]['self_intersections']:>6}/{R[t][p]['edge_ratio_max']:>5.2f}  " for t in tags))
print('SUM SI'.ljust(26)+''.join(f"{sum(R[t][p]['self_intersections'] for p in poses):>14}" for t in tags))
print('MAX ER'.ljust(26)+''.join(f"{max(R[t][p]['edge_ratio_max'] for p in poses):>14.2f}" for t in tags))
print('P99 ER'.ljust(26)+''.join(f"{max(R[t][p]['edge_ratio_p99'] for p in poses):>14.2f}" for t in tags))
print('P1 ER'.ljust(26)+''.join(f"{min(R[t][p]['edge_ratio_p1'] for p in poses):>14.3f}" for t in tags))
