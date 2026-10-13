# W1/W2 original-body anatomy attachment — provisional

Separate `codex/functional-original-anatomy-attachment-20261012`, stacked on
the reviewed PR80 head `2af63aedc3ff1c8c5de4974b4e826ec6ce26d81b`. The PR48
owner decision at `f9d4ca0f`, Claude work and later Lane G software branches
remain preserved. This checkpoint changes neither the source Blender file nor
any Chat parser/renderer contract.

## What was actually attached

The newer project-authored guides are constructed around the original male in
the unchanged a003 206-bone rest frame:

- two clavicle tubes use the a003 SC/AC endpoints and an authored S curve;
- two closed scapula bowls use the c004 perimeter, uniformly similarity-fitted
  to the a003 scapula segment, with the prior authored 8 mm recession;
- 24 rib bows and one sternum plate use a003 endpoints;
- all 29 guides receive exactly one one-weight Armature modifier targeting an
  explicitly mapped control of the existing 67-bone runtime rig.

The mapping is deliberately provisional and non-bijective. F-SIDE-001 remains
explicit: anatomical left +X maps to runtime `*_r`, and right maps to `*_l`.
Radius/ulna and tibia/fibula retain the earlier many-to-one limb mapping. All
24 ribs and the sternum collapse to rigid `spine_02` pose-delta attachment.
The 206-bone source stays at rest and still does not drive the body. This is a
truthful guide attachment, not a 206→67 inverse-bind retarget.

## Executed evidence

Five pure contract tests pass: view inventory, F-SIDE-001 and collapse rules,
finite directed-segment similarity fit, collapsed/non-finite refusal, and
fail-closed attachment inventory. Five actual Blender 5.2.1 native tests pass
against the pinned source: all 29 guide objects, single runtime attachments,
unchanged clavicle anchors, visible runtime pose delta with source still at
rest, exact 206/67 counts, 17,946 body vertices, and the original body's sole
enabled runtime driver. The fifth test guards both the workflow's
`--out OUTPUT_PATH` interface and the supported positional form.

The native source is opened with `--factory-startup`. Without that flag this
machine's user add-on/preferences startup can stall before the test expression;
the source itself loads in seconds under factory startup. A first builder
attempt also exposed a real selection-scope defect: Blender conversion included
preselected production objects and evaluated their modifiers. The builder now
deselects the source scene before every temporary curve conversion, and the
native guard proves the original body driver remains unchanged.

Six new neutral, 900 px views were rendered in actual Blender: full-body and
shoulder-context front/side/rear. They are changed-geometry evidence, not
rerenders of PR80's nine views. Private directory:
`C:/Users/Mark/Documents/Codex/hgpt-functional-original-attachment-v1-20261013/`.
Manifest SHA-256:
`23e8aaf938fdd36c294d199e6ce8da7f326298a2d5baf673eb6297ce0b428f18`.
All six manifest-listed PNG hashes were recomputed with zero mismatches. Source
blend SHA-256 remains
`670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56`.
No private render or new native/source byte is added to Git; CI regenerates only
rights-safe project-authored diagnostic proof.

## Reference comparison and exposed defects

The prior qualified qualitative references remain constraints rather than a
fit result: the scapula should present a concave costal surface against the
thorax, and shoulder elevation must be judged as coupled scapulothoracic and
glenohumeral movement rather than a single rigid pivot. This checkpoint has
not performed a new specimen measurement or real-human motion fit.

Visual inspection of neutral full front and shoulder front/side confirms the
S-curved clavicle guides and closed blade bowls are present around the original
male. The side view places the blades posterior to the thorax, but placement is
still coarse. The bowls are oversized guide surfaces rather than accepted
scapulae. The front X-ray exposes steep, coil-like rib bows and guide overlap;
these are not registered rib surfaces or contact geometry. X-ray visibility is
diagnostic only. There is no breathing, contact solver, fitted anatomical axes,
0/90/160 coupled-motion comparison, muscle sliding, skin-weight validation,
deformation acceptance, clinical approval or production approval.

## Exact next action

Define guarded 0/90/160 runtime pose deltas for the attached guides and compare
blade-on-thorax placement, clavicle motion and humeral contribution against
qualified anatomical and real-human references. Correct the rib surface and
blade scale/placement from that comparison before changing the original male's
weights; then quantify shoulder/axilla deformation on broad press and pull-up
motion. Detailed one-to-one registration of all 206 bones remains unnecessary
for this prototype step. Do not repeat the six unchanged neutral views.
