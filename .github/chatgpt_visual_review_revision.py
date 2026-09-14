from pathlib import Path


def replace(path, old, new, count=1):
    p = Path(path)
    text = p.read_text()
    if old not in text:
        raise SystemExit(f"missing anchor in {path}: {old[:140]!r}")
    p.write_text(text.replace(old, new, count))

# Character state owns a monotonic deformation revision for production-visible
# character changes that sit outside the undoable exercise document.
p = Path("src/editor/characterStore.ts")
text = p.read_text()
text = text.replace(
    "  /** Viewport-only A/B switch; export remains production-correct. */\n  correctivesPreview: boolean;",
    "  /** Viewport-only A/B switch; export remains production-correct. */\n  correctivesPreview: boolean;\n  /** Changes whenever production-visible character deformation identity changes. */\n  deformationRevision: number;",
    1,
)
text = text.replace(
    "  setActive: (build: CharacterBuild | null) => void;\n  setCorrectivesPreview: (enabled: boolean) => void;",
    "  setActive: (build: CharacterBuild | null) => void;\n  setCorrectivesPreview: (enabled: boolean) => void;\n  setDeformationControl: (id: string, value: number) => void;",
    1,
)
text = text.replace(
    "  active: null,\n  correctivesPreview: true,",
    "  active: null,\n  correctivesPreview: true,\n  deformationRevision: 0,",
    1,
)
text = text.replace(
    "  setSource: (sourceId) => set({ sourceId }),",
    "  setSource: (sourceId) => {\n    const state = get();\n    if (state.sourceId === sourceId) return;\n    set({ sourceId, deformationRevision: state.deformationRevision + 1 });\n  },",
    1,
)
text = text.replace(
    "  setActive: (active) => set({ active }),\n  setCorrectivesPreview: (correctivesPreview) => set({ correctivesPreview }),",
    "  setActive: (active) => set({ active }),\n  setCorrectivesPreview: (correctivesPreview) => set({ correctivesPreview }),\n  setDeformationControl: (id, value) => {\n    const state = get();\n    const control = state.active?.deformation?.controls?.find((item) => item.id === id);\n    if (!control) return;\n    const before = control.value;\n    control.set(value);\n    if (Math.abs(control.value - before) <= 1e-9) return;\n    set({ deformationRevision: state.deformationRevision + 1 });\n  },",
    1,
)
text = text.replace(
    "      sourceId: defaultCharacterId(),\n      name: null,",
    "      sourceId: defaultCharacterId(),\n      deformationRevision: get().deformationRevision + 1,\n      name: null,",
    1,
)
# Successful imports use the stable source id `import`, so source-id comparison
# alone cannot distinguish a newly loaded file or remapped preserved skeleton.
text = text.replace(
    "      sourceId: source.id,\n      name: importedLabel,",
    "      sourceId: source.id,\n      deformationRevision: useCharacter.getState().deformationRevision + 1,\n      name: importedLabel,",
    2,
)
p.write_text(text)

# Route every persistent UI tuning action through the revision-aware setter.
p = Path("src/editor/panels/CorrectivePanel.tsx")
text = p.read_text()
text = text.replace(
    "  const setEnabled = useCharacter((state) => state.setCorrectivesPreview);",
    "  const setEnabled = useCharacter((state) => state.setCorrectivesPreview);\n  const setDeformationControl = useCharacter((state) => state.setDeformationControl);",
    1,
)
if "control.set(" not in text:
    raise SystemExit("no direct corrective control setters found")
text = text.replace("control.set(", "setDeformationControl(control.id, ")
p.write_text(text)

# Visual sign-off identity now includes the character deformation revision.
p = Path("src/editor/store.ts")
text = p.read_text()
text = text.replace(
    "  visualReview: { document: StudioDocument; characterSourceId: string } | null;",
    "  visualReview: { document: StudioDocument; characterSourceId: string; deformationRevision: number } | null;",
    1,
)
text = text.replace(
    "  markVisualReview: (characterSourceId: string) => void;",
    "  markVisualReview: (characterSourceId: string, deformationRevision: number) => void;",
    1,
)
text = text.replace(
    "    markVisualReview: (characterSourceId) =>\n      set({ visualReview: { document: get().document, characterSourceId } }),",
    "    markVisualReview: (characterSourceId, deformationRevision) =>\n      set({ visualReview: { document: get().document, characterSourceId, deformationRevision } }),",
    1,
)
p.write_text(text)

# Review requires production correctives and an exact deformation-revision match.
p = Path("src/editor/panels/ReviewPanel.tsx")
text = p.read_text()
text = text.replace(
    "  const sourceId = useCharacter((state) => state.sourceId);\n  const sourceStatus = useCharacter((state) => state.sourceStatus);",
    "  const sourceId = useCharacter((state) => state.sourceId);\n  const sourceStatus = useCharacter((state) => state.sourceStatus);\n  const correctivesPreview = useCharacter((state) => state.correctivesPreview);\n  const deformationRevision = useCharacter((state) => state.deformationRevision);",
    1,
)
text = text.replace(
    "  const visualPassed =\n    visualReview?.document === document && visualReview.characterSourceId === sourceId;\n  const approved = review.automatedPass && visualPassed;",
    "  const visualPassed =\n    visualReview?.document === document &&\n    visualReview.characterSourceId === sourceId &&\n    visualReview.deformationRevision === deformationRevision;\n  const approved = review.automatedPass && visualPassed && correctivesPreview;",
    1,
)
text = text.replace(
    "        grip contact, equipment stability and overall naturalness. Any document edit or character\n        change invalidates the sign-off automatically.",
    "        grip contact, equipment stability and overall naturalness. Any document edit, character\n        change or export-aware deformation tuning change invalidates the sign-off automatically. Raw\n        skinning is diagnostic only and cannot be signed off because export uses production correctives.",
    1,
)
text = text.replace(
    "          disabled={!review.automatedPass || sourceStatus.kind !== 'idle'}",
    "          disabled={!review.automatedPass || sourceStatus.kind !== 'idle' || !correctivesPreview}",
    1,
)
text = text.replace(
    "          onClick={() => (visualPassed ? clearVisualReview() : markVisualReview(sourceId))}",
    "          onClick={() =>\n            visualPassed\n              ? clearVisualReview()\n              : markVisualReview(sourceId, deformationRevision)\n          }",
    1,
)
text = text.replace(
    "      </div>\n      <p className=\"panel__note\">Automated review sampled {review.sampledFrames} frames.</p>",
    "      </div>\n      {!correctivesPreview && (\n        <p className=\"panel__note\">Enable Correctives on before production visual sign-off.</p>\n      )}\n      <p className=\"panel__note\">Automated review sampled {review.sampledFrames} frames.</p>",
    1,
)
p.write_text(text)

# Character-store regression: effective changes bump once; no-op/unknown controls do not.
p = Path("src/editor/characterStore.test.ts")
p.write_text(r'''import { afterEach, describe, expect, it } from 'vitest';
import type { CharacterBuild, DeformationControl } from '../character';
import { useCharacter } from './characterStore';

describe('character deformation review revision', () => {
  afterEach(() => {
    useCharacter.setState({ active: null, deformationRevision: 0, correctivesPreview: true });
  });

  it('increments only when an effective production deformation value changes', () => {
    let value = 0.25;
    const control: DeformationControl = {
      id: 'outer-elbow',
      label: 'Outer elbow',
      min: 0,
      max: 1,
      step: 0.05,
      defaultValue: 0,
      get value() {
        return value;
      },
      set(next) {
        value = Math.max(0, Math.min(1, next));
      },
    };
    const active = {
      deformation: { update: () => undefined, controls: [control] },
    } as unknown as CharacterBuild;
    useCharacter.setState({ active, deformationRevision: 0 });

    useCharacter.getState().setDeformationControl('outer-elbow', 0.5);
    expect(value).toBe(0.5);
    expect(useCharacter.getState().deformationRevision).toBe(1);

    useCharacter.getState().setDeformationControl('outer-elbow', 0.5);
    expect(useCharacter.getState().deformationRevision).toBe(1);

    useCharacter.getState().setDeformationControl('missing', 0.9);
    expect(useCharacter.getState().deformationRevision).toBe(1);

    useCharacter.getState().setDeformationControl('outer-elbow', 2);
    expect(value).toBe(1);
    expect(useCharacter.getState().deformationRevision).toBe(2);
  });
});
''')

# Studio regression records the revision as part of sign-off identity and retains
# the existing document-reference invalidation semantics.
p = Path("src/editor/store.test.ts")
text = p.read_text()
addition = r'''

describe('visual review identity', () => {
  it('records character deformation revision and becomes stale after a document edit', () => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
    const signedDocument = useStudio.getState().document;
    useStudio.getState().markVisualReview('review-character', 7);
    expect(useStudio.getState().visualReview).toEqual({
      document: signedDocument,
      characterSourceId: 'review-character',
      deformationRevision: 7,
    });

    useStudio.getState().setGripClosure(0.8);
    expect(useStudio.getState().document).not.toBe(signedDocument);
    expect(useStudio.getState().visualReview?.document).toBe(signedDocument);
  });
});
'''
text += addition
p.write_text(text)

# Docs + shared AI handoff.
replace(
    "docs/STUDIO_CAPABILITY_ROADMAP.md",
    "- Visual sign-off is bound to the exact Studio document identity and active character source; edits or character swaps invalidate it automatically. Only automated-pass + matching visual sign-off displays `APPROVED`.",
    "- Visual sign-off is bound to the exact Studio document identity, active character source and production deformation revision; exercise edits, character/import changes or export-aware corrective tuning invalidate it automatically. Raw-skinning preview cannot be signed off because export uses production correctives. Only automated-pass + matching visual sign-off displays `APPROVED`.",
)
replace(
    "docs/BICEP_CURL_REVIEW_HANDOFF.md",
    "- **Correctives on / Raw skinning** remains a viewport-only A/B and does not alter the clip/source mesh/export.",
    "- **Correctives on / Raw skinning** remains a viewport-only A/B and does not alter the clip/source mesh/export. Production visual sign-off is disabled in Raw skinning, and any permanent export-aware corrective change increments the character deformation revision so an older sign-off cannot remain valid.",
)

p = Path("AI_CHANGELOG.md")
text = p.read_text()
entry = r'''### ChatGPT — 2026-09-14 — bind visual sign-off to production deformation state

Closed an approval-integrity gap introduced by live export-aware character correctives. Visual sign-off previously matched only Studio document identity plus character source id, so changing a character-level elbow corrective after sign-off could leave the old approval looking current even though GLB export would now use a different deformation value.

Character state now carries a monotonic `deformationRevision`. Persistent corrective UI edits route through a revision-aware setter that increments only when the effective control value really changes; no-op/unknown writes do not advance it. Successful preserved/rebound imports and import mapping rebuilds also advance the revision because the stable `import` source id alone cannot distinguish different loaded character content. The temporary whole-rep corrective sweep still manipulates/restores the raw control directly, so a diagnostic scan that ends on the original value does not invalidate approval.

Visual sign-off records the current deformation revision and Review requires document identity + character source + deformation revision to match. Production approval is also suppressed and the sign-off button disabled while `Raw skinning` preview is active, because export always uses production correctives. Returning to Correctives on restores an otherwise-current sign-off only when no production value changed.

Regression coverage verifies revision changes only for effective control edits and that Studio sign-off records the character revision alongside its existing document-reference identity.

'''
marker = "## Unreleased\n\n"
if marker not in text:
    raise SystemExit("missing changelog marker")
text = text.replace(marker, marker + entry, 1)
p.write_text(text)

print("Applied production deformation-aware visual review identity")
