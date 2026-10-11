# G4d — first-party typed exercise → exact SHA-bound Work-authored pose binding

**11 October 2026. Chat-owned Lane G diagnostic integration; no new Blender or biomechanical movement production.**

## Purpose

Home Gym PT must eventually accept a command like **left-arm standing dumbbell shoulder press neutral grip**, animate a real first-party character and never silently swap a clip intended for a different exercise, hand, grip, posture, model, material or piece of equipment. Previously, the standalone G4c exercise command recogniser (PR #65) and the G4b Work-authored GLB/pose parser (PR #60) had no end-to-end exercise/pose-variant matching. This **G4d** interface ties them without pretending that arbitrary text already generates human movement.

New first-party module: `src/exercise/firstPartyExercisePoseBinding.mjs`.

Its `bindFirstPartyExerciseToDiagnosticPose(command, verifiedOriginalModelHandle, workAuthoredRawPoseClip, exactWorkClipDeclaration)`:
- Re-parses the user command with the G4c fail-closed vocabulary rather than trusting a user-modified intent object.
- Matches **exact** exercise movement ID, SHA-256 verified GLB model, candidate ID, declared equipment, laterality, posture and grip against the author's original pose-clip declaration.
- Requires the old G4/G4b legitimate source handle, rest/inverseBind/joint order and every complete rigid source bone pose/normal world matrix to pass original validation, then copies all pose palettes to a private snapshot to prevent later caller mutation.
- Returns only `BOUND_DIAGNOSTIC_ONLY`, with an audited list of required but **unverified biomechanics** and flags explicitly false for clinical ROM, actual shoulder mechanics, independently observed source authorship, physically checked equipment contact, actual motion synthesis and production release.
- Exposes `getBoundDiagnosticExerciseFrame(binding,index)` to return one **copied** original-authored discrete joint matrix palette per accepted source pose index. There is no unsafe matrix interpolation or invented pose between authored frames. A forged binding or fractional index fails.

## Work pose declaration schema

The pose JSON remains the original G4b contract at docs/FIRST_PARTY_G4B_PROVISIONAL_POSE_SEQUENCE_20261011.md (must use e.g. exerciseId `overhead_press`). Add a separate small JSON declaration of **author-reported intended use**. It is NOT independent scientific evidence; Work and Chat must verify movement against real human reference and contacts separately.

~~~json
{
  "kind": "hgpt-first-party-clip-intent-declaration-v1",
  "sourcePoseSetId": "HomeGymPTOverheadPressDiagnosticA01",
  "candidateId": "REAL_G4_MODEL_CANDIDATE_ID",
  "sourceSha256": "REPLACE_WITH_THE_EXACT_G4_GLb_SHA256",
  "exerciseId": "overhead_press",
  "parameters": {
    "equipment": "dumbbell",
    "laterality": "left",
    "posture": "standing",
    "grip": "neutral"
  },
  "statedOrigin": "WORK_AUTHORED_SOURCE_CLAIM",
  "biomechanicsReview": "UNVERIFIED_DIAGNOSTIC"
}
~~~

The `parameters` fields must match exactly what was declared in the user command. If the command omits equipment, laterality, posture or grip, the corresponding authored parameter MUST be null: the engine must not silently select a one-arm, seated or special-grip clip for an unspecified request. This is intentionally strict for now. Relaxation or alternatives require explicit owner policy, user choice and separately reviewed variation logic; the body must not be moved just to make format matching pass.

## Local usage

~~~js
import {validateProvisionalModelHandoff}
  from './src/viewer/firstPartyPrototypeModelHandoff.mjs';
import {bindFirstPartyExerciseToDiagnosticPose,getBoundDiagnosticExerciseFrame}
  from './src/exercise/firstPartyExercisePoseBinding.mjs';

const model=await validateProvisionalModelHandoff(originalGlbArrayBuffer,modelManifest);
const playback=bindFirstPartyExerciseToDiagnosticPose(
  'left arm standing dumbbell shoulder press neutral grip',
  model,actualWorkPoseClip,actualWorkClipDeclaration);
const firstOriginalJointOrderedPalette=getBoundDiagnosticExerciseFrame(
  playback,0).sourceJointOrderedPalette;
~~~

A green source/command/pose binder check means these files are consistent and have numerically acceptable matrices. It **does not establish** real scapulohumeral/clavicle/scapular movement, anatomically correct body/mesh proportions, loaded equipment contacts, realistic soft-tissue/skin deformations or original human model asset rights. A synthetic 2-joint shoulder fixture can pass purely to test software; this must never be claimed to be a real shoulder press.

## Test evidence and next tasks

The first-party Node suite uses a self-generated synthetic two-joint binary GLB and three author-labelled pose frames. It verifies SHA/candidate/exercise ID, exact all-four qualifier binding, forged model/refusal, invalid rest/rig/frame data, contradictions, unauthorized approval flags, metadata mutation and every exposed bone-palette snapshot. It runs the inherited text/GLB/pose tests and unchanged studio TypeScript build in a dedicated GitHub Actions workflow. Mark **VERIFIED software** only after exact-head CI succeeds.

**Next Chat action:** when Work publishes the *actual rights-safe original character GLB and pose evidence*, verify it through this same contract, add only genuinely needed renderer/rig/mesh support, and later connect it to real first-party app playback and exercise solver. Do not duplicate Work's skeleton, detailed CT atlas, biomechanics or Blender labor; no early removal of Three.js studio or the 304 temporary instructional clips.

See the owner-approved [shared plan v1.1](https://github.com/anyangle1409-code/animation-software/blob/codex/shared-autonomous-master-plan-20261011/docs/HOME_GYM_PT_SHARED_AUTONOMOUS_MASTER_PLAN.md).
