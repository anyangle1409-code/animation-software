"""Validate complete sample correspondence before numerical comparisons."""
def validate_samples(a,b,ba,bb):
    expected=[i/40 for i in range(41)]
    for report in (a,b):
        if [row['t'] for row in report['press']] != expected:
            raise ValueError('Expected every one of the 41 ordered full-press times')
    names=set(ba['benchmarks'])
    if len(names)!=13 or set(bb['benchmarks'])!=names:
        raise ValueError('Expected the same complete 13 benchmark movements')
    for name in names:
        x=[row['t'] for row in ba['benchmarks'][name]['frames']]
        y=[row['t'] for row in bb['benchmarks'][name]['frames']]
        if not x or x!=y:
            raise ValueError(f'Missing or mismatched actual frames for {name}')
