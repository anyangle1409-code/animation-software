from pathlib import Path


def replace(path, old, new):
    p = Path(path)
    text = p.read_text()
    if old not in text:
        raise SystemExit(f'missing anchor in {path}: {old[:120]!r}')
    p.write_text(text.replace(old, new, 1))

replace(
    'src/exercises/definitions/bicepCurl.ts',
    "      correction: 'Keep the elbows pinned under the shoulders through the whole range.',",
    "      correction: 'Keep the elbows roughly under the shoulders; allow only a small natural drift near the top.',",
)

replace(
    'docs/BICEP_CURL_REVIEW_HANDOFF.md',
    '**Current retained head before this handoff update:** `b2a7db71adea054383d22282e3660a04e78d9a62`',
    '**Current retained head before this handoff update:** `1edbd65f3cf19e10986e60875a7724b9e3ad9619`',
)
replace(
    'docs/BICEP_CURL_REVIEW_HANDOFF.md',
    'Latest full validation after the grip-review pass: **285 passed, 1 optional real-character diagnostic skipped, across 35 test files.**',
    'Latest full validation after the deformation-aware visual-review pass: **287 passed, 1 optional real-character diagnostic skipped, across 36 test files.**',
)
replace(
    'docs/BICEP_CURL_REVIEW_HANDOFF.md',
    '- `b2a7db7` — fine grip review controls and curl review frames.',
    '- `b2a7db7` — fine grip review controls and curl review frames.\n- `1edbd65` — visual sign-off bound to production deformation state.',
)

p = Path('AI_CHANGELOG.md')
text = p.read_text()
marker = '## Unreleased\n\n'
entry = '''### ChatGPT — 2026-09-14 — align curl coaching wording with validated natural elbow drift\n\nUpdated the `elbow_drift` correction text from “pinned under the shoulders through the whole range” to “roughly under the shoulders; allow only a small natural drift near the top.” This is a wording-only change: the retained curl motion, technique thresholds and generated clip are unchanged. It removes a contradiction between the coaching copy and the validated 4° / ~21.55 mm late upper-arm/elbow contribution that is intentionally present to keep the curl lifelike rather than mechanically pinned.\n\nThe bicep-curl handoff was also refreshed to the deformation-aware approval checkpoint (287 passing tests + 1 optional skip across 36 files).\n\n'''
if marker not in text:
    raise SystemExit('missing changelog marker')
p.write_text(text.replace(marker, marker + entry, 1))

print('Aligned curl coaching wording and refreshed handoff validation state')
