"""Prepare hash-identical isolated copy after reconstruction content gates only.

No authored landmarks or tissue geometry. Native quality and anatomy remain separate gates.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys

REQUIRED = ('offline_evidence_check', 'w8_vs_archive', 'w8_blend', 'v14_blend')


def ready(root):
    for name in REQUIRED:
        path = root / 'verify' / (name + '.json')
        if not path.exists(): return False
        summary = json.loads(path.read_text()).get('summary', {})
        if summary.get('fail') != 0 or summary.get('pass', 0) <= 0: return False
    path = root / 'verify/v14_report_vs_archive.json'
    return path.exists() and json.loads(path.read_text()).get('identical') is True


def main():
    root, package, out = map(lambda p: Path(p).resolve(), sys.argv[1:])
    out.mkdir(parents=True, exist_ok=False)
    if not ready(root):
        (out / 'preparation.json').write_text(json.dumps({'status': 'BLOCKED', 'reason': 'Reconstruction evidence missing or differs from archive; no model copy or attachments authored.'}, indent=2))
        return
    sys.path.insert(0, str(package))
    from experiments.anatomical_muscles.prepare import copy_experiment, digest
    from experiments.anatomical_muscles.compile_exercise import load_inputs, compile_request
    from experiments.anatomical_muscles.registry import expand, SEED
    source = root / 'V14/body_v2_legs.blend'
    candidate = out / 'HomeGymPT_V14_MUSCLE_EXPERIMENT_UNAPPROVED.blend'
    result = copy_experiment(source, candidate, digest(source))
    result.update({'status': 'staging_copy_only', 'attachment_validation': 'NOT_RUN', 'anatomical_approval': 'NOT_GRANTED',
                   'priority': ['shoulders', 'arms', 'pelvis', 'legs'], 'muscle_commit': '7c820d68de69dcdef7d567e836302123df953446'})
    (out / 'preparation.json').write_text(json.dumps(result, indent=2) + '\n')
    registry = expand(json.loads(SEED.read_text()))
    (out / 'permanent_muscle_ids.json').write_text(json.dumps(registry, indent=2) + '\n')
    library, _ = load_inputs()
    samples = [compile_request(ex['id'], phase['id'], progress, activation)
               for ex in library['exercises'] for phase in ex['phases']
               for progress in (0.0, 0.5, 1.0) for activation in (0.0, 1.0)]
    (out / 'exercise_contract_samples.json').write_text(json.dumps(samples, indent=2) + '\n')
    for name in ('CLAUDE_HANDOFF.md', 'EXERCISE_MUSCLE_CONTRACT.md', 'CURRENT_W8_VISUAL_QA_20261022.md', 'exercise_contracts.json'):
        shutil.copyfile(package / 'experiments/anatomical_muscles' / name, out / name)
    subprocess.run([sys.executable, str(package / 'experiments/anatomical_muscles/inspect_blender.py'), '--',
                    str(candidate), result['source_sha256'], str(out / 'inventory.json')], check=True)
    (out / 'NEXT_ATTACHMENT_GATES.md').write_text('''# Muscle attachment staging — no attachment approval

The experiment is a byte-identical copy of the recovered v14 candidate. Bindings remain unresolved.
Read the included Claude handoff and permanent ID registry. Begin with one shoulder, verify the opposite anatomical
side independently using native landmarks, then arms, pelvis and legs. Use the curl, press and squat contract IDs.
Activation remains independent of skeletal position; samples include zero/full activation at identical pose progress.
Do not infer anchors from suffixes, body proximity, screenshot colour or unreviewed test fixtures.
Author shoulder/axilla paths and broad attachment patches before skin masks; test actual path lengths, wrapping,
clearance, neutral return and deformation throughout the trajectories. Preserve all source files and rest bones.
The native movement reports and eight existing W8 visual findings still require review before anatomical approval.
''')


if __name__ == '__main__': main()
