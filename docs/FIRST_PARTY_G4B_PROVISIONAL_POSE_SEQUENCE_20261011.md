# G4b — offline original-model sampled movement handoff

**11 October 2026 • software-only first-party PROTOTYPE candidate, not approved human motion.**

Work can now provide an **actual early 3D male character GLB** with its original
rig/bind manifest (G4, PR #59), **plus authored whole-body movement frames**
without waiting for clinical approval of all 206 anatomical bone surfaces.
Chat validates the frames and prepares original source joint-order palettes;
Work remains owner of bone positions, coupled biomechanics and realistic
visible deformation.

## Input conditions

A model must first pass G4 exact source SHA-256 and GLB-to-runtime-bone
rest binding. The offline G4b input has **exact fields**:

- kind: hgpt-provisional-human-pose-frames-v1
- candidateId: EXACT G4 verified source candidate
- sourceSha256: EXACT verified GLB source digest
- exerciseId: stable ASCII exercise label, not an executable prompt
- approvalStatus: DIAGNOSTIC_ONLY (not certified movement)
- durationSeconds: between .05 and 180
- frames: 2..600 actual Work-authored discrete samples, each containing
  timeSeconds and posedWorldByRuntimeBone. First time is zero, last equals
  duration; timestamps strictly increase; every frame has exactly all declared
  named runtime bones, each with a proper rigid affine 4x4 column-major world
  matrix in the same model space.

The source-to-runtime mapping and legal pose palette are **never inferred
from suffixes**. Packed frames preserve source GLB skin joint order. Unknown,
extra, missing or reflected/scaled/sheared world matrices are rejected.
The 10 m broad translation cap is a software corruption guard, not a
physiological distance/ROM threshold. The maximum between-frame translation
and rotation metrics are *diagnostics*, not evidence of plausible human load,
joint-safe ROM, grip/contact fidelity or realistic skin deformation.

## Work handoff example

The example below is a **synthetic two-joint illustration only**. A real original
human source model must provide every actual runtime joint, and each frame's
matrices in precisely the corresponding GLB/native world reference frame.

~~~json
{
  "kind": "hgpt-provisional-human-pose-frames-v1",
  "candidateId": "FunctionalOriginalPrototype",
  "sourceSha256": "REPLACE_WITH_THE_EXACT_64_CHARACTER_G4_MODEL_HASH",
  "exerciseId": "shoulder_press_prototype",
  "approvalStatus": "DIAGNOSTIC_ONLY",
  "durationSeconds": 1,
  "frames": [
    {
      "timeSeconds": 0,
      "posedWorldByRuntimeBone": {
        "upperarm_l": [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1],
        "forearm_l": [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]
      }
    },
    {
      "timeSeconds": 1,
      "posedWorldByRuntimeBone": {
        "upperarm_l": [1,0,0,0, 0,1,0,0, 0,0,1,0, 0.1,0,0,1],
        "forearm_l": [1,0,0,0, 0,1,0,0, 0,0,1,0, 0.2,0,0,1]
      }
    }
  ]
}
~~~

The sample is **not a shoulder press** and makes **no** claim about scapular
rhythm, clavicle curvature, socket mechanics, soft tissue or exercise loads.
For Work's real shoulder validation supply full neutral, early, mid, top and
return frames with the true source runtime bones and independent real-human
movement/pose evidence.

## Calling the first-party API

~~~js
import {validateProvisionalModelHandoff} from './src/viewer/firstPartyPrototypeModelHandoff.mjs';
import {compileProvisionalPoseSequence,getProvisionalPoseFrame}
  from './src/viewer/firstPartyPrototypePoseSequence.mjs';
const model=await validateProvisionalModelHandoff(originalGlbBuffer, modelManifest);
const clip=compileProvisionalPoseSequence(model, workAuthoredClipJSON);
const worldMatricesSourceJointOrder =
  getProvisionalPoseFrame(clip, 1).sourceOrderedWorldMatrices;
~~~

No unsafe interpolation is performed. Linear interpolation between 4x4
rotation matrices is NOT reliable: Work/animation engine must generate
correct quaternion/kinematic intermediate frames, and Chat must separately
validate visually and numerically before claiming smooth playback. This stage
does not implement exercise text parsing or physically based motion generation.

## One-command Work laptop motion preflight

Node 24 is enough; no npm install and no Blender/plugin is required for the
numeric source/rig/clip handoff check:

~~~bash
node scripts/verify-provisional-motion.mjs /path/to/original-human.glb /path/to/model-handoff.json /path/to/work-authored-pose-frames.json
~~~

This checks the actual binary digest, original source bone mapping and the
whole time-ordered 3D world-matrix sequence together. It produces a short
machine-readable summary with explicit **NOT APPROVED** flags, and refuses
tampered/different source assets or invalid frames. It neither renders the
human nor establishes natural exercise biomechanics. Work must inspect
real Blender clips and reference movement separately. Do not upload private
CT/medical source bytes to GitHub.

## Acceptance boundary and tests

Tests use only project-generated synthetic GLB and pose samples. They check
actual SHA-bound source model, all rigid matrices in each original pose,
source order, full timestamps, diagnostic rotations, missing and extra bones,
bad model hashes, tampered handles and refusal of medical/release claims.
Existing G4 handoff, GLB and GPU normal tests and the original Studio
TypeScript/build remain unchanged, run by CI. **Only CI on the exact current
branch HEAD can verify this software stage.**

No clinical skeleton approval, no independent physiological ROM validation,
no loaded-ground/bench/equipment motion proof, no real male muscle/skin
deformation parity, no real prototype GLB supplied by Work yet, no mobile
GPU proof and no app release or full third-party removal.

**Next software task:** native GPU presentation of Work's real authored
geometry/pose samples when available; otherwise continue independent bounded
material/lighting/texture and rig hierarchy support. The current first-party
GPU stage is synthetic and remains draft.
