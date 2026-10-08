#!/usr/bin/env python3
"""Derive a Phase 9 run input from an audit candidate record without editing it.

The isolated-test runner checks record['provenance']['out_blend_sha256'] against the blend it opens. Audit candidates
built from a003 inherit a003's provenance, so this writes a run-local copy whose only change is that hash (set to the
candidate blend) plus a 'movement_run_input' note naming the untouched source record and its sha256.

  prepare_candidate_movement_run.py --record CAND.json --blend CAND.blend --out RUN/inputs/record_for_run.json
"""
import argparse, copy, hashlib, json
from pathlib import Path


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def derive(record_path, blend_path):
    rec = json.loads(Path(record_path).read_text())
    out = copy.deepcopy(rec)
    out['provenance']['out_blend_sha256'] = sha(blend_path)
    out['movement_run_input'] = {'derived_from_record': str(record_path), 'derived_from_sha256': sha(record_path),
                                 'blend': str(blend_path), 'only_change': 'provenance.out_blend_sha256 set to the candidate blend',
                                 'inherited_out_blend_sha256': rec['provenance']['out_blend_sha256']}
    return out


def main():
    ap = argparse.ArgumentParser()
    for a in ('--record', '--blend', '--out'):
        ap.add_argument(a, required=True)
    o = ap.parse_args()
    out = Path(o.out)
    if out.exists():
        raise FileExistsError(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(derive(o.record, o.blend), indent=1) + '\n')
    print('written', out)


if __name__ == '__main__':
    main()
