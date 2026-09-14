from pathlib import Path


def replace(path, old, new):
    p = Path(path)
    text = p.read_text()
    if old not in text:
        raise SystemExit(f"missing anchor in {path}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1))

p = Path("src/editor/panels/GripPanel.tsx")
text = p.read_text()
anchor = '''      <p className="panel__note">\n        Presets only change deterministic finger closure; they do not move the wrist, equipment or\n        accepted arm animation. Changes remain undoable.\n      </p>\n\n      <details className="grip-digit-details">\n'''
replacement = '''      <p className="panel__note">\n        Presets only change deterministic finger closure; they do not move the wrist, equipment or\n        accepted arm animation. Changes remain undoable.\n      </p>\n\n      <h4>Fine closure A/B</h4>\n      <div className="button-row grip-presets">\n        {[0.65, 0.7, 0.75, 0.8, 0.85].map((closure) => (\n          <button\n            type="button"\n            key={`fine-closure-${closure}`}\n            className={Math.abs(exercise.hands.closure - closure) < 1e-6 ? 'is-active' : ''}\n            onClick={() => setGripClosure(closure)}\n          >\n            {Math.round(closure * 100)}%\n          </button>\n        ))}\n      </div>\n      <p className="panel__note">\n        Fine presets leave the playhead untouched, so thumb opposition, finger wrap and palm loading\n        can be compared on the exact same pose.\n      </p>\n\n      {exercise.id === 'dumbbell_bicep_curl' && (\n        <>\n          <h4>Curl review frames</h4>\n          <div className="button-row grip-presets">\n            {[\n              { label: 'Bottom', time: 0 },\n              { label: 'Mid lift', time: 1 },\n              { label: 'Peak', time: 2 },\n              { label: 'Mid lower', time: 4 },\n              { label: 'Return', time: 5 },\n            ].map((point) => (\n              <button\n                type="button"\n                key={`curl-grip-frame-${point.label}`}\n                className={Math.abs(time - point.time) < 1 / Math.max(1, clip.fps) ? 'is-active' : ''}\n                onClick={() => setTime(point.time)}\n              >\n                {point.label}\n              </button>\n            ))}\n          </div>\n          <p className="panel__note">\n            Review the same closure at bottom, mid-concentric, peak, mid-eccentric and return before\n            accepting a permanent grip change.\n          </p>\n        </>\n      )}\n\n      <details className="grip-digit-details">\n'''
if anchor not in text:
    raise SystemExit("missing GripPanel preset anchor")
text = text.replace(anchor, replacement, 1)
p.write_text(text)

replace(
    "docs/STUDIO_CAPABILITY_ROADMAP.md",
    "- Per-digit closure trims can independently adjust thumb/index/middle/ring/pinky on top of the active grip profile while unspecified digits continue to follow global closure. Defaults are absent, so accepted grips remain byte-for-byte generator-compatible until an author opts in.",
    "- Per-digit closure trims can independently adjust thumb/index/middle/ring/pinky on top of the active grip profile while unspecified digits continue to follow global closure. Defaults are absent, so accepted grips remain byte-for-byte generator-compatible until an author opts in. Fine 65/70/75/80/85% closure presets leave the playhead untouched for same-pose A/B; Dumbbell Bicep Curl also exposes direct Bottom/Mid lift/Peak/Mid lower/Return review-frame buttons.",
)

p = Path("AI_CHANGELOG.md")
text = p.read_text()
entry = r'''### ChatGPT — 2026-09-14 — fine grip closure and curl review frames

Grip review now has one-tap 65/70/75/80/85% fine closure presets in addition to the broader Loose/Training/Closed presets. Fine presets use the existing deterministic `setGripClosure` path and deliberately leave the playhead, wrist and equipment transform untouched, so thumb opposition, four-finger wrap and palm loading can be compared on the exact same pose.

Dumbbell Bicep Curl additionally exposes Bottom (0.00s), Mid lift (1.00s), Peak (2.00s), Mid lower (4.00s) and Return (5.00s) review buttons directly in the Grip workspace. This matches the retained review plan while keeping the authored 85% closure unchanged until a visual decision is made. No per-digit override, handle offset, wrist angle or exercise motion is changed automatically.

'''
marker = "## Unreleased\n\n"
if marker not in text:
    raise SystemExit("missing changelog marker")
text = text.replace(marker, marker + entry, 1)
p.write_text(text)

print("Applied fine grip closure and curl review-frame controls")
