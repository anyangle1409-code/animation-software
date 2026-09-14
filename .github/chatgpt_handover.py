from pathlib import Path

path = Path('AI_CHANGELOG.md')
text = path.read_text(encoding='utf-8')
marker = '## Unreleased\n'
heading = '### ChatGPT — 2026-09-14 — minimum-jerk secondary motion for curl'
entry = f'''\n{heading}\n\nContinued the software-level bicep-curl refinement without changing the character asset. Added a reusable `minimumJerk` easing kind using the fifth-order trajectory `10t^3 - 15t^4 + 6t^5`. Unlike the existing cosine `lift` curve, this reaches both zero velocity and zero acceleration at each endpoint, which is useful for secondary joints that begin moving part-way through a phase. The ordinary resistance-training `lift` curve remains the default for prime movement.\n\nThe dumbbell curl now uses `minimumJerk` only on the already-delayed upper-arm motion: the upper arms still wait until 55% of the concentric and 20% of the eccentric, but their small authored 4-degree shoulder drift now leaves and returns to the held pose without the acceleration step of the cosine curve. Elbow flexion/supination, start and peak poses, 126-degree peak flexion, 5.5-second repetition, grip, fingers, equipment attachment, clavicle depression, contact locks, canonical rig, retargeting, skin weights and the candidate GLB are unchanged. The retained Library candidate reviewed for this pass is `HomeGymPT_Male_HAND_REPAIR_CANDIDATE.glb` version 5, SHA-256 `dfb0fea61e4053412f4213a5904dab1ed06b416003faf4ef0eb13c27e8d5702f`.\n\nAdded regression coverage for the minimum-jerk curve itself, including near-zero endpoint velocity and acceleration. Full branch validation on Node 22 passed: `npm run typecheck`; `npm test` with **194 passed and 1 optional real-character diagnostic skipped**; and `npm run build`, with only the existing >500 kB chunk warning. No asset was modified. The next elbow work should remain topology-aware; do not amplify the retained radial elbow corrective, because that experiment was already rejected for adding bulk without fixing the angular silhouette.\n'''

if heading not in text:
    if marker not in text:
        raise SystemExit('Unreleased marker not found')
    path.write_text(text.replace(marker, marker + entry + '\n', 1), encoding='utf-8')
