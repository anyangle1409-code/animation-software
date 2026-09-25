# Draft reference-family expansion — status

## Branch

`work/internal-reference-family-packs-20260925`

Based on the R2 scaffold. The live source branch is untouched.

## What this branch adds

The internal reference engine now has draft packs for:

1. curl;
2. overhead press;
3. squat;
4. lunge (split squat, forward lunge, reverse lunge);
5. hinge / dumbbell Romanian deadlift;
6. bent-over row.

All remain `status: "draft"`. None may gate approval or drive correction until
their envelopes are independently reviewed and the tests below are green.

## Evaluator extensions

Added reusable world/body-relative checks:

- `rootPositionEnvelope`;
- `relativeLandmarkEnvelope`;
- `segmentAngleEnvelope`;
- `landmarkStationary`;
- `landmarkDistanceEnvelope`.

World distances can be normalized by:

- standing height;
- shoulder width;
- arm length;
- torso length.

This allows a reference to describe human-relative geometry rather than one
character's pixels or raw metres.

## Reference packs

### Overhead press

Checks include:
- phase order;
- racked elbow depth;
- overhead lockout;
- elbow ROM;
- shoulder elevation and excursion;
- lumbar brace;
- upright torso;
- wrist neutrality;
- hand lockout height;
- bilateral arm/elbow symmetry;
- monotonic dumbbell rise/lower.

Supports standing and seated reference ids separately.

### Squat

Checks include:
- phase order;
- normalized root depth;
- torso angle;
- lower-back neutrality;
- hip depth relative to knee;
- knee tracking;
- planted feet;
- bilateral hip/knee symmetry;
- monotonic pelvis descent/rise.

### Lunge

Uses distinct phase expectations:
- split squat: eccentric → bottom → concentric → top;
- stepping lunges: step → bottom → drive → stand.

Checks include:
- upright torso;
- neutral spine;
- square pelvis;
- back-knee depth;
- front-knee tracking;
- front-knee fore/aft position;
- correct planted contact for the variant;
- normalized forward/reverse step length for stepping variants.

### Hinge / RDL

Checks include:
- phase order;
- root/body hinge angle;
- neutral lower and upper back;
- soft knee;
- long arms;
- hips back;
- hips high;
- dumbbell/hand path close to legs;
- planted feet;
- bilateral knee symmetry.

### Bent-over row

Checks include:
- phase order;
- fixed hinge posture;
- torso stationary;
- neutral lower back;
- elbow driven behind torso;
- elbow flexion at squeeze;
- elbows tucked;
- neutral forearm/grip;
- neutral wrist;
- bilateral arm/elbow symmetry;
- monotonic dumbbell rise/lower.

## Review cameras

The deterministic review-camera layer now also supports local close-ups for:
- hands;
- shoulders;
- feet/knees.

These do not use the interactive Focus camera.

## Tests prepared

- `src/reference/worldChecks.test.ts`
- `src/reference/familyPacks.test.ts`
- expanded `src/reference/reviewCamera.test.ts`

The family-pack test checks every accepted library reference and also deliberately
damages one press, squat, lunge, RDL and row to prove the intended reference
check can fail.

## Required validation

Run:

```
npm run typecheck
npm test -- \
  src/reference/worldChecks.test.ts \
  src/reference/familyPacks.test.ts \
  src/reference/reviewCamera.test.ts \
  src/reference/evaluate.test.ts \
  src/reference/measure.test.ts
npm run build
```

If green, run the complete suite.

If an accepted exercise falls outside one of these draft envelopes:
- do not edit the accepted exercise;
- print the measured value;
- decide whether the draft envelope is wrong;
- keep the pack draft until independently reviewed.

## Important

The numbers in these packs are intentionally broad first-pass human-motion
corridors. They are not certified biomechanics merely because a current library
exercise fits them.

The next calibration step is to inspect the measured reports for the accepted
library examples and tighten only where the independent movement definition
supports doing so.
