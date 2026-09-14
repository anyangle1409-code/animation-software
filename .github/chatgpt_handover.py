from pathlib import Path

path = Path('AI_CHANGELOG.md')
text = path.read_text(encoding='utf-8')
marker = '## Unreleased\n'
heading = '### ChatGPT — 2026-09-14 — phase-local joint timing; natural curl shoulder sequencing'
entry = f'''\n{heading}\n\nReviewed the animation generator itself rather than changing the character asset. The generator previously exposed only phase-level easing, so every joint moved on the same normalized clock between the authored start and peak poses. Added optional `MovementPhase.jointTiming` with per-bone `delay`, `finish`, and easing. `generateClip` carries that timing onto the outgoing phase keyframe and `sampleClip` remaps only explicitly timed bones; all other joints keep the existing resistance-training easing. No intermediate stop-start keyframes are inserted.\n\nThe dumbbell curl is the first validation use. Both upper arms now remain at the relaxed bottom position until 55% of the concentric while elbow flexion begins immediately, then complete only the already-authored 4° forward drift near the top. On the eccentric, the elbows begin opening first and the upper arms wait until 20% of the phase before settling back. Start and peak poses, the 5.5 s repetition tempo, 126° peak elbow flexion, clavicle depression, supinated grip, finger closure, equipment attachment, contact locks, canonical rig, imported-character retargeting, skin weights and candidate GLB are unchanged.\n\nRegression coverage now explicitly checks elbow-before-shoulder sequencing in addition to the existing loop, grip, equipment rigidity, contact, symmetry and technique validation. Branch validation on Node 22: `npm run typecheck` passed; `npm test` passed **193 tests with 1 optional real-character diagnostic skipped**; `npm run build` passed with only the pre-existing >500 kB chunk warning. No character asset was changed by this software pass.\n'''

if heading not in text:
    if marker not in text:
        raise SystemExit('Unreleased marker not found')
    path.write_text(text.replace(marker, marker + entry + '\n', 1), encoding='utf-8')
