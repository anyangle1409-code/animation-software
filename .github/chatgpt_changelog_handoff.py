from pathlib import Path

path = Path('AI_CHANGELOG.md')
text = path.read_text(encoding='utf-8')
anchor = '## Unreleased\n\n'
entry = '''### ChatGPT — 2026-09-14 — selected-joint focus camera and curl realism guardrails

Added a diagnostic **Focus selected** camera mode for imported-character review. It follows the currently selected resolved joint during playback with a close 32° view and side-aware three-quarter offset, while reusing scratch vectors to avoid per-frame allocation. App-facing Recommended/full-body framing is unchanged. Validated feature commit `9126b7b`: TypeScript passed, **203 tests passed / 1 optional real-character diagnostic skipped** across 19 files, and the production build passed with only the existing Vite chunk-size advisory.

Hardened the bicep-curl validator without changing the accepted motion, model, rig, grip closure or equipment attachment. Added explicit anti-shrug clavicle limits, tightened upper-arm takeover to a 10° ceiling, required the dumbbell grip to remain supinated, constrained sideways wrist deviation to ±10°, and added the user-facing common error **Shrugging the shoulders**. New negative tests deliberately inject a shrug, 18° upper-arm takeover, lost supination and 20° wrist deviation and confirm each rule fires. Validated commit `d2b3a24`: TypeScript passed, **207 tests passed / 1 optional skipped** across 20 files, and the production build passed with only the existing chunk-size advisory.

Tomorrow review is now documented in `docs/BICEP_CURL_REVIEW_HANDOFF.md`. Use the proven v5 candidate first, then A/B the review-only `OUTER_ELBOW` candidate at curl mid/top with **Focus selected**. For grip, keep 85% as the baseline and compare 80/75/70/65% through the live production generator. Do not promote `outerSmooth` or a lower permanent grip closure from offline numbers alone; visual elbow silhouette, secure finger enclosure, thumb placement, palm loading, rigid dumbbell centring and bilateral symmetry are the acceptance gates. Temporary validation workflows/helpers were removed after the validated commits landed.

'''
if anchor not in text:
    raise SystemExit('Unreleased anchor not found')
if 'selected-joint focus camera and curl realism guardrails' not in text:
    text = text.replace(anchor, anchor + entry, 1)
path.write_text(text, encoding='utf-8')
