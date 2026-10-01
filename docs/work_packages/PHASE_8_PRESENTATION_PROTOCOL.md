# Phase 8 numeric materials / presentation protocol

Prepared only; Phase 8 remains NOT STARTED.

This package turns the Phase 8 requirements into a candidate-bound numeric
material/provenance and presentation-state workflow. It does not decide whether the
character looks good; real app-distance renders and owner review remain required.

## Material provenance

Start from:

`ORIGINAL_V1_PHASE8_MATERIAL_PROVENANCE_TEMPLATE.json`

The final record must use status `MATERIAL_PROVENANCE_COMPLETE`, bind the exact
candidate SHA and enumerate every material assigned to the body or garment.

For each material record:

- assigned scope;
- independent_authorship=true;
- numeric_only=true;
- third_party_content=false;
- external_image_sources=false;
- hashed operation/source evidence.

The material set and body/garment assignment must exactly match the captured scene.

The Phase 8 policy is deliberately strict:

- numeric materials only;
- no third-party textures;
- no external HDRIs;
- no linked material libraries;
- no geometry or weight changes.

## One-command presentation-state capture

After Phase 7 is genuinely complete:

```bat
RUN_ORIGINAL_V1_PHASE8_PRESENTATION.bat <rN> <material-provenance.json> <fresh-output-dir>
```

The runner verifies live branch/remote HEAD, clean state, Phase 7 completion,
Blender availability, candidate bytes and same-candidate provenance before
capturing.

It writes:

- `presentation_scene_capture.json`
- `presentation_scene_verification.json`

The Blender capture records:

- all body/garment material slots;
- shader node types and numeric socket defaults;
- any image node references;
- world node state;
- lights and transforms;
- cameras and transforms;
- active camera;
- render engine and output dimensions;
- colour management;
- linked libraries.

The verifier blocks image/texture shader inputs, image/HDRI world inputs, linked
materials/lights/cameras/libraries, unresolved shader socket values, missing
camera/render state or incomplete/incorrect material provenance.

An `EVIDENCE_COMPLETE` result still has `phase_complete=false` and
`production_approved=false`.

## Fixed real-render plan

Use:

`ORIGINAL_V1_PHASE8_PRESENTATION_CAPTURE_PLAN.json`

It removes ambiguity around later review coverage.

Required real captures include matched bare/dressed neutral front/rear/side/3/4,
dressed shoulder press, curl, squat, lunge, push-up and row at app-distance context,
plus representative skin and cloth close-ups.

The anatomy specification's 300–700 full-body pixel height is retained only as an
app-distance review context. It is not a device or runtime performance promise.

Every real capture must record candidate SHA, pose/view, camera, lighting,
renderer/version, colour management, output dimensions and crop. If those differ,
record the mismatch instead of calling it a quantitative before/after comparison.

## Readability review

The actual Phase 8 review must check that presentation does not conceal:

- joint collapse;
- fingertips / grip contact;
- waist and garment clearance;
- floor penetration/contact;
- silhouette defects.

No automatic shader score can satisfy `readable_application_views` or
`no_concealed_body_failures`.

## Exit boundary

Phase 8 still requires:

- unchanged geometry/weight evidence;
- actual source-bound renders;
- declared viewing conditions;
- real readability review;
- published review snapshot;
- verified Phase 8 exit packet.

Current r29 / Phase 3 is not eligible. This tooling exists now to remove future
setup/provenance work from Claude's Blender session.
