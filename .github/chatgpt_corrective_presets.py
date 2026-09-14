from pathlib import Path


def replace(path, old, new):
    p = Path(path)
    text = p.read_text()
    if old not in text:
        raise SystemExit(f"missing anchor in {path}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1))

p = Path("src/editor/panels/CorrectivePanel.tsx")
text = p.read_text()
anchor = '''              />\n              {control.note && <small>{control.note}</small>}\n'''
replacement = '''              />\n              <div className="button-row">\n                {[0, 0.25, 0.5, 0.75, 1].map((fraction) => {\n                  const preset = control.min + (control.max - control.min) * fraction;\n                  return (\n                    <button\n                      type="button"\n                      key={`${control.id}-preset-${fraction}`}\n                      className={Math.abs(control.value - preset) < 1e-9 ? 'is-active' : ''}\n                      onClick={() => {\n                        control.set(preset);\n                        refreshControls((value) => value + 1);\n                        setWholeRep(null);\n                      }}\n                    >\n                      {Math.round(fraction * 100)}%\n                    </button>\n                  );\n                })}\n              </div>\n              <small>Preset comparison changes only corrective strength; the playhead stays on the same frame for a fair silhouette A/B.</small>\n              {control.note && <small>{control.note}</small>}\n'''
if anchor not in text:
    raise SystemExit("missing corrective slider anchor")
text = text.replace(anchor, replacement, 1)
p.write_text(text)

replace(
    "docs/STUDIO_CAPABILITY_ROADMAP.md",
    "- Corrective tuning can run an on-demand 0/25/50/75/100% whole-rep strain sweep, report worst P99/max frame for each value, restore the pre-scan tuning and pose, and jump to any measured value for visual review without automatically choosing a winner.",
    "- Corrective tuning can run an on-demand 0/25/50/75/100% whole-rep strain sweep, report worst P99/max frame for each value, restore the pre-scan tuning and pose, and jump to any measured value for visual review without automatically choosing a winner. One-tap 0/25/50/75/100% strength presets also leave the playhead untouched, allowing a fair same-frame silhouette comparison before using the strain timestamps.",
)

p = Path("AI_CHANGELOG.md")
text = p.read_text()
entry = r'''### ChatGPT — 2026-09-14 — same-frame corrective comparison presets

Added one-tap 0/25/50/75/100% presets to each character-level corrective tuning control. Unlike the existing strain-sweep review action, these presets change only corrective strength and deliberately leave the playhead untouched. This lets an author hold the curl on the exact same peak frame and tap through candidate strengths for a fair elbow-silhouette A/B before consulting strain metrics.

The existing whole-rep sweep remains separate and still restores the pre-scan value/pose; its `Review this value at worst P99` action can still move to each candidate's measured worst frame. No exercise pose, skin weights, authored default or automatic approval threshold is changed by the new presets.

'''
marker = "## Unreleased\n\n"
if marker not in text:
    raise SystemExit("missing changelog marker")
text = text.replace(marker, marker + entry, 1)
p.write_text(text)

print("Applied same-frame corrective comparison presets")
