"""Collect existing evidence without converting missing checks into passes; hash artifacts."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys

NATIVE = ('R41', 'W8', 'V14', 'R120')
TESTS = ('vitest', 'typecheck', 'scripts', 'scripts_tests', 'scripts_blender_tests', 'muscles', 'guards')
MODELS = {'W8': 'W8/body_v2.blend', 'V14': 'V14/body_v2_legs.blend', 'R120': 'R120/body_v2_rebuilt.blend'}
CHECKS = ('offline_evidence_check', 'w8_vs_archive', 'w8_blend', 'v14_blend')


def digest(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def collect(root):
    checks, missing = {}, []
    for name in CHECKS:
        path = root / 'verify' / (name + '.json')
        if not path.exists():
            missing.append(str(path.relative_to(root)))
            checks[name] = False
        else:
            summary = json.loads(path.read_text()).get('summary', {})
            checks[name] = summary.get('pass', 0) > 0 and summary.get('fail') == 0
    v14 = root / 'verify/v14_report_vs_archive.json'
    checks['v14_report_vs_archive'] = v14.exists() and json.loads(v14.read_text()).get('identical') is True
    if not v14.exists(): missing.append(str(v14.relative_to(root)))
    files = {}
    for name, relative in MODELS.items():
        path = root / relative
        files[name] = {'path': relative, 'sha256': digest(path), 'bytes': path.stat().st_size} if path.exists() else None
        if not path.exists(): missing.append(relative)
    for name, folder in [('W8', 'W8/renders'), ('V14', 'V14'), ('R120', 'R120')]:
        for view in ('front', 'back', 'side', 'front34'):
            relative = f'{folder}/V2_skin_stand_{view}.png'
            if not (root / relative).exists(): missing.append(relative)
    tests = {}
    for name in TESTS:
        path = root / 'tests' / (name + '.exit')
        tests[name] = path.read_text().strip() if path.exists() else 'MISSING'
    movements = {}
    for name in NATIVE:
        path = root / 'native' / name / 'benchmarks.json'
        movements[name] = json.loads(path.read_text()).get('summary', {}) if path.exists() else {}
    return {'reconstruction_pass': all(checks.values()) and all(files[n] for n in ('W8', 'V14'))
                and not any(p.startswith(('W8/', 'V14/')) for p in missing),
            'movement_execution_complete': all(m.get('complete') is True for m in movements.values()),
            'movement_quality_pass': all(m.get('quality_pass') is True for m in movements.values()),
            'test_suites_pass': all(code == '0' for code in tests.values()), 'test_exit_codes': tests,
            'anatomical_approval': 'NOT_GRANTED', 'checks': checks, 'files': files, 'missing': missing,
            'movements': movements, 'R120_status': 'EXPERIMENTAL — no archive equivalence or production approval'}


def manifest(root):
    paths = sorted(p for p in root.rglob('*') if p.is_file() and p.name != 'MANIFEST.sha256' and 'r57src' not in p.parts and 'muscle-src' not in p.parts)
    with (root / 'MANIFEST.sha256').open('w') as out:
        for path in paths:
            out.write(f'{digest(path)}  {path.relative_to(root).as_posix()}\n')


def main():
    root = Path(sys.argv[1]).resolve()
    result = collect(root)
    result['run_url'] = os.environ.get('RECOVERY_RUN_URL')
    result['evidence_commit'] = os.environ.get('RECOVERY_COMMIT')
    result['updated_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (root / 'RECOVERY_RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
    lines = ['# Cloud Body v2 recovery results', '', f"Run: {result['run_url']}", f"Commit: `{result['evidence_commit']}`", '',
             f"Reconstruction/archive checks: {'PASS' if result['reconstruction_pass'] else 'FAIL / INCOMPLETE'}.",
             f"All 13 × 9 movement paths executed for all four inputs: {result['movement_execution_complete']}.",
             f"Zero collapse/stretch/intersection quality gate across all inputs: {result['movement_quality_pass']}.",
             f"Application and pinned test suites: {'PASS' if result['test_suites_pass'] else 'FAIL / INCOMPLETE'}; exit codes {result['test_exit_codes']}.",
             'Anatomical and visual approval: NOT GRANTED. R120 remains EXPERIMENTAL.', '',
             '| Model | Path | SHA256 |', '|---|---|---|']
    for name, file in result['files'].items():
        lines.append(f"| {name} | {file['path'] if file else 'MISSING'} | {file['sha256'] if file else 'MISSING'} |")
    lines += ['', 'See RECOVERY_RESULT.json, verify/, native/, tests/, native/V14/muscle/ and logs/ for exact failures and discrepancies.',
              'Missing reports or renders are never a pass. Raw failure counts across different mesh topologies are diagnostic, not a like-for-like improvement claim.',
              'W8 screenshot source identity and unsaved R52/R57 increments remain unresolved.',
              'PT_MODEL_VERSION 1.0 preserved. No production replacement, merge or deployment.']
    (root / 'RECOVERY_RESULT.md').write_text('\n'.join(lines) + '\n')
    manifest(root)
    print(json.dumps({k: result[k] for k in ('reconstruction_pass', 'movement_execution_complete', 'movement_quality_pass', 'missing')}))


if __name__ == '__main__': main()
