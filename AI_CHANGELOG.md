# AI Change Log

This file records changes made by Codex and Claude. Each assistant must add an
entry whenever it changes code, tests, documentation, assets, exercise
definitions, or repository configuration.

## Unreleased

### Codex — 2026-09-08 — `codex/anatomical-reference-character`

Purpose: improve the dumbbell curl while recording and withdrawing an
unsuccessful imported-character experiment.

- **Retained:** replaced the oversized hex dumbbell ends with smaller round
  plates and reduced peak elbow flexion/shoulder travel so the weights do not
  crowd the chest. The existing grip placement and mirrored finger closure are
  unchanged.
- **Rejected and removed:** an attempted MakeHuman-to-canonical remap passed
  static mesh and bone tests but failed in the real posed preview. Its bind pose
  was incompatible with the canonical skeleton, causing torn shoulders and
  torso sections and fingers to explode away from both hands. The body also did
  not match the requested athletic male reference. All generated mesh data,
  surface-highlighting changes and third-party asset files from that attempt
  have been removed; the last known-good profile character is restored.
- **Regression coverage:** added a contracted-curl skin test which transforms
  every vertex and rejects detached or exploded geometry. This covers the visual
  failure that the earlier bone-only tests missed.

Verification: 122 tests pass, including the new fully posed skin check;
`npm run typecheck` and `npm run build` are clean.

### Claude Opus 5 — 2026-09-08 — `claude/home-gym-pt-animation-txux66`

Purpose: make the studio's character read as a person rather than a mannequin,
and make the muscle overlay usable as exercise instruction.

Preserved Codex's `067e90db` grip work unchanged: `anatomicalGripOffset` is
still what places a one-hand attachment, and its two animation tests still run.

- **Character.** Re-authored the body profiles as an athletic adult male:
  V-taper from a 0.39 m chest to a 0.27 m waist, deltoid caps, biceps and
  triceps mass, a forearm flare into a narrow wrist, patella at the knee, and a
  calf. Added a face — eyeballs with irises and lids, brow, nose, lips, jaw
  corners, ears — and a close-cropped hair shell.
- **Clothing.** Surface colour is now a vertex attribute on the same single
  mesh, so skin, dark fitted shorts, waistband, eyes, lips and hair cost one
  draw call between them. The shorts run from the hip to mid-thigh, leaving
  every joint the exercises work bare.
- **Muscle overlay.** Each belly is now built on an anatomical frame — length
  along the muscle, width across the body, depth through the skin — instead of
  spreading along an arbitrary axis. Bellies taper into tendon at both ends and
  are fitted against the body at runtime, so none of them break the skin during
  the curl and none exceed 7 mm in any other exercise. Re-placed all 21 muscle
  definitions against the new surface.
- **Highlighting.** Primary muscles are now a clear red, secondary a softer
  orange, stabilisers close to flesh tone and untargeted muscles almost
  invisible. For the curl this leaves both biceps as the obvious highlight, with
  the forearm flexors and front deltoids behind them.
- **Grip.** The thumb now extends at the knuckle and folds over, laying it along
  the handle instead of sweeping it past the palm. This rig has no
  carpometacarpal joint, so the thumb cannot oppose across the palm; along the
  bar is as close to a wrap as its joint limits allow.
- **Backdrop.** A studio/light backdrop toggle, so app-facing captures come out
  on a clean light stage instead of the editor's dark one.
- **Tests.** New `body/body.test.ts` cases for the male silhouette, the shorts'
  coverage and the eyes; a new `muscles/muscles.test.ts` covering containment,
  attachment, left/right mirroring, the biceps through the curl and the
  activation palette; a new `equipment/grip.test.ts` checking each handle stays
  wrapped by the fingers and thumb and rigid in the hand throughout both
  dumbbell exercises.

Verification: 121 tests pass; `npm run typecheck` and `npm run build` are clean.

### Codex — 2026-09-08 — `codex/fix-dumbbell-grip-position`

Purpose: keep dumbbell handles visibly enclosed by the fingers throughout
hand-held exercises.

- Moved the default one-hand equipment grip from inside the palm to the centre
  of the curled-finger loop, with mirrored left/right palm-facing offsets.
- Applied the anatomical default to the bicep curl and dumbbell shoulder press.
- Expanded animation tests to check both hands throughout the full repetition
  and detect a handle positioned inside the palm.

Verification: 81 local tests passed on the compatible Codex checkout;
`npm run typecheck` and `npm run build` completed successfully.

## Baseline history

### Claude Opus 5 — 2026-09-08 — commit `e6ef05b4`

Added the anatomical skinned body, corrected mirrored finger flexion, and added
the dumbbell shoulder press and pull-up. Reported 101 passing tests.

### Claude Opus 5 — 2026-09-08 — commit `287f72c6`

Created the initial Home Gym PT Animation Studio, including its canonical rig,
IK, equipment, exercise definitions, editor, retargeting and exporters.

### Repository owner — 2026-09-07 — commit `df07dced`

Created the repository with the initial commit.
