#!/usr/bin/env python3
"""Amplitude provenance: every commanded peak of every Phase 9 test traces to committed evidence (read-only).

For each test and each commanded channel, both extremes (max, min; zero skipped) are classified by explicit rules only:
  EXACT_CONTEXT          |peak| equals a number in the spec's atlas context observations (matching observation ids listed)
  STATED_IN_BASIS        |peak| equals a number stated in a sentence of the spec's amplitude_basis that does NOT declare
                         TEST AMPLITUDE (the cited source is the spec author's; this audit cannot verify the citation)
  HALF_OF_SOURCED_TOTAL  2|peak| equals a context/basis number AND the basis text states the split ('half'/'split')
  CONDITION_IN_TEST_ID   a held, non-primary channel whose value is named in the test id (e.g. _at_pronation_60)
  TARGET_MINUS_FITTED_REST  thumb CMC: |peak| == intermetacarpal target - fitted rest angle (both stored on the spec);
                         the committed run must then MEASURE the target at the peak frame (within 1.7e-3 deg)
  DRIVEN_TO_MEASURED_TARGET  thumb opposition palmar abduction: driven until the intermetacarpal angle reaches the clinical
                         maximum stored on the spec; verified only by the run check (target measured at peak)
  LABELLED_TEST_AMPLITUDE   the number is stated in a basis sentence that declares TEST AMPLITUDE, or is a stated and
                         labelled '10%' reversal of a context mean (unsourced, explicitly). This rule takes precedence over
                         context matches: a first draft counted the unsourced hip ab/adduction 20/30 deg, opposition
                         pronation 30 deg and talocrural +20 deg DF as traced through coincidental numbers
  UNTRACED               none of the above (a defect: an amplitude with no recorded basis)
Precedence is the order of this list except that TEST AMPLITUDE statements are applied before context matches.
Numbers are compared at 1e-6 (they are copied, not measured). For intermetacarpal-driven tests the run check uses the
committed samples of the same record.

  amplitude_provenance_audit.py --record R.json --samples S.json --label NAME --out JSON
"""
import argparse, hashlib, json, math, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import isolated_tests as it  # noqa: E402

ROOT = HERE.parents[1]
ANG = math.degrees(3e-5)
LENGTH_CHANNELS = {'glide'}           # the only non-angular command channel (metres)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def numbers(x, out, path=''):
    if isinstance(x, dict):
        for k, v in x.items():
            numbers(v, out, x.get('id', path) if isinstance(x.get('id'), str) else path)
    elif isinstance(x, list):
        for v in x:
            numbers(v, out, path)
    elif isinstance(x, (int, float)) and not isinstance(x, bool):
        out.setdefault(round(abs(float(x)), 6), set()).add(path)
    elif isinstance(x, str):
        for m in re.findall(r'\d+(?:\.\d+)?', x):
            out.setdefault(round(float(m), 6), set()).add(path or 'text')


def context_values(ctx):
    """Only observation VALUE numbers count (mean / median / range / value), never population text, sample sizes, CIs or
    SDs: a first draft matched numbers anywhere in the observation (e.g. 'age 20-44')."""
    out = {}

    def walk(x, oid):
        if isinstance(x, dict):
            if 'value' in x and isinstance(x.get('id'), str):
                vals(x['value'], x['id'])
            for v in x.values():
                if isinstance(v, (dict, list)):
                    walk(v, oid)
        elif isinstance(x, list):
            for v in x:
                walk(v, oid)

    def vals(v, oid, key=''):
        if isinstance(v, dict):
            for k, w in v.items():
                if not re.fullmatch(r'ci.*|sd|se|n|count|.*_n', k, re.I):
                    vals(w, oid, k)
        elif isinstance(v, list):
            for w in v:
                vals(w, oid, key)
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            out.setdefault(round(abs(float(v)), 6), set()).add(oid)
    walk(ctx, None)
    return out


def classify(t):
    ctx = context_values(t['context'])
    basis = t.get('amplitude_basis', '') or ''
    sentences = [x for x in re.split(r'(?<=[.;])\s+', basis) if x]
    bas, bas_test = {}, {}
    for snt in sentences:
        target = bas_test if 'TEST AMPLITUDE' in snt.upper() else bas
        numbers(snt, target)
    id_nums = {round(float(x), 6) for x in re.findall(r'(?<=_)\d+(?=_|$)', t['id'])}
    im = t.get('intermetacarpal')
    chans = {}
    for k in t.get('keys') or []:
        for c, v in k.items():
            chans.setdefault(c, []).append(v)
    rows = []
    for c, vs in chans.items():
        for peak in sorted({max(vs), min(vs)}):
            a = round(abs(peak), 6)
            if a < 1e-12:
                continue
            if c in LENGTH_CHANNELS:
                a = round(abs(peak) * 1000, 6)                  # commanded in metres, stated in millimetres
            r = {'channel': c, 'peak': peak}
            if im and c == t.get('primary') and abs(abs(peak) - (im['target_deg'] - im['rest_angle_deg'])) <= 1e-9:
                r.update(kind='TARGET_MINUS_FITTED_REST', target_deg=im['target_deg'], rest_angle_deg=im['rest_angle_deg'])
            elif im and t['kind'] == 'opposition' and c == 'abduction' and re.search(r'driven .* to the clinical maximum', basis):
                r.update(kind='DRIVEN_TO_MEASURED_TARGET', target_deg=im['target_deg'])     # verified by the run check below
            elif a in bas_test:
                r['kind'] = 'LABELLED_TEST_AMPLITUDE'            # an explicit TEST AMPLITUDE statement beats a coincidental match
            elif round(10 * a, 6) in ctx and re.search(r'10%[^.;]*TEST AMPLITUDE', basis, re.I):
                r.update(kind='LABELLED_TEST_AMPLITUDE', derivation='10% of a context mean, stated and labelled')
            elif a in ctx:
                r.update(kind='EXACT_CONTEXT', observations=sorted(ctx[a]))
            elif a in bas:
                r['kind'] = 'STATED_IN_BASIS'
            elif round(2 * a, 6) in (set(ctx) | set(bas)) and re.search(r'\bhalf\b|split', basis, re.I):
                r.update(kind='HALF_OF_SOURCED_TOTAL', total=round(2 * a, 6))
            elif a in id_nums and c != t.get('primary'):
                r['kind'] = 'CONDITION_IN_TEST_ID'
            else:
                r['kind'] = 'UNTRACED'
            rows.append(r)
    return rows


def audit(rec, atlas, samples):
    specs = it.specs(rec, atlas)
    tests, counts, untraced, im_checks = {}, {}, [], {}
    for t in specs:
        rows = classify(t)
        tests[t['id']] = {'amplitude_basis': t.get('amplitude_basis'), 'peaks': rows}
        for r in rows:
            counts[r['kind']] = counts.get(r['kind'], 0) + 1
            if r['kind'] == 'UNTRACED':
                untraced.append({'test': t['id'], **r})
        if t.get('intermetacarpal') and t['id'] in samples:
            target = t['intermetacarpal']['target_deg']
            meas = [f['intermetacarpal_angle_deg'] for f in samples[t['id']] if 'intermetacarpal_angle_deg' in f]
            best = min(meas, key=lambda m: abs(m - target)) if meas else None
            im_checks[t['id']] = {'target_deg': target, 'closest_measured_deg': best, 'max_measured_deg': max(meas) if meas else None,
                                  'abs_diff_deg': None if best is None else abs(best - target),
                                  'reached': best is not None and abs(best - target) <= ANG}
    return {'tests': len(specs), 'peaks': sum(counts.values()), 'by_kind': dict(sorted(counts.items())), 'untraced': untraced,
            'intermetacarpal_target_reached': im_checks,
            'status': 'TRACED' if not untraced and all(v['reached'] for v in im_checks.values()) else 'GAPS', 'detail': tests}


def main():
    ap = argparse.ArgumentParser()
    for a in ('--record', '--samples', '--label', '--out'):
        ap.add_argument(a, required=True)
    o = ap.parse_args()
    atlas_p = ROOT / 'ORIGINAL_V1_WORK/anatomy/whole_body_movement_atlas.json'
    r = audit(json.loads(Path(o.record).read_text()), json.loads(atlas_p.read_text()), json.loads(Path(o.samples).read_text()))
    Path(o.out).parent.mkdir(parents=True, exist_ok=True)
    Path(o.out).write_text(json.dumps({'schema_version': 1, 'created': '2026-10-09', 'label': o.label, 'kind': 'READ_ONLY_PROVENANCE_AUDIT',
                                       'inputs_sha256': {o.record: sha(o.record), o.samples: sha(o.samples), str(atlas_p.relative_to(ROOT)): sha(atlas_p),
                                                         'scripts/anatomy_fit/isolated_tests.py': sha(HERE / 'isolated_tests.py')}, **r}, indent=1) + '\n')
    print(o.label, {k: r[k] for k in ('status', 'tests', 'peaks', 'by_kind')}, 'untraced', r['untraced'][:4])
    print('  im', {k: (round(v['target_deg'], 3), None if v['abs_diff_deg'] is None else float(f"{v['abs_diff_deg']:.3g}"), v['reached']) for k, v in r['intermetacarpal_target_reached'].items()})


if __name__ == '__main__':
    main()
