from pathlib import Path

path = Path('AI_CHANGELOG.md')
text = path.read_text(encoding='utf-8')
marker = '## Unreleased\n'
heading = '### ChatGPT — 2026-09-14 — preserve imported morph conventions'
entry = f'''\n{heading}\n\nHardened the candidate-specific imported deformation path for future characters that already carry expressions or body-shape morphs. `importedElbowDeformation` previously set `geometry.morphTargetsRelative = true` whenever it appended the elbow corrective. Three.js uses one morph convention for the entire geometry, so that could reinterpret a source character's pre-existing absolute morph targets. The importer now leaves the source convention untouched: on relative geometries the elbow target remains a delta; on absolute geometries it writes base position plus the same corrective delta. The current male candidate's rendered result is unchanged; this is an importer-safety correction, not another elbow-shape change.\n\nAdded two regression cases alongside the directional elbow tests. They seed a character with a pre-existing absolute morph and with a pre-existing relative morph, append the corrective, and verify both the convention flag and the original morph data remain unchanged. The existing opt-in and 8 mm directional safety-cap tests remain. Final Node 22 validation: `npm run typecheck` passed; `npm test` passed **198 tests with 1 optional real-character diagnostic skipped** across 17 files; `npm run build` passed with only the existing >500 kB Vite chunk advisory. `docs/CHARACTER_CANDIDATE_REPAIR.md` now records this guardrail and the 198/1 result.\n'''

if heading not in text:
    if marker not in text:
        raise SystemExit('Unreleased marker not found')
    path.write_text(text.replace(marker, marker + entry + '\n', 1), encoding='utf-8')
