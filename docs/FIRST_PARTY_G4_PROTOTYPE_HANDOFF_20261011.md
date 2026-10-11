# G4 – original human prototype handoff (first-party, SHA-bound)

**11 October 2026 • Chat software lane • PROTOTYPE ONLY, not approved anatomy, movement or release.**

## Why this exists

The owner-approved shared master plan v1.1 (PR #48) allows Work to produce a real original shaped-skeleton human model earlier. Work owns Blender, anatomical positioning, joint mechanics, skin and deformation. Chat owns offline GLB parsing, explicit bind-map verification, native rendering and app integration. This G4 gate catches export/rig compatibility problems early without either side changing joint locations just to make the software fit.

- Accepts complete original GLB ArrayBuffer + an explicit JSON model/rig manifest.
- Snapshots bytes and verifies the exact source SHA-256 using native WebCrypto; a stale manifest is rejected.
- Uses existing restricted, fail-closed source GLB decoders: one primitive OR a shared-skin batched GLB of 2–8 primitives in 1–4 meshes. Maximum source GLB size 32 MiB, 128 joint palette entries, existing four-weight skin scheme.
- Calls the separately audited source-joint → runtime-rig validator for **every primitive**. The original world-rest times inverse-bind matrix must be identity within the pre-existing software-only tolerance 1e-4; bone order is source-preserved.
- Exposes a verified pose packing handle for GPU palette skinning, while explicitly reporting false for source frame registration, clinically proven shoulder biomechanics, mesh deformation acceptance, rights approval and production readiness.
- No HTTP/network fetch, external model API, proprietary anatomy copy, Three.js, third-party JS module or automatic side inference.

## Work-generated manifest template

The digest is deliberately invalid until filled with the exact SHA256 of the actual exported GLB. The two sample joint matrices are only synthetic identity illustrations, **not** valid rest matrices for a real articulated human.

~~~json
{
  "kind": "hgpt-provisional-original-model-handoff-v1",
  "candidateId": "HomeGymPT_Male_FUNCTIONAL_v1",
  "status": "PROTOTYPE_ONLY",
  "glb": {
    "sha256": "REPLACE_WITH_ACTUAL_64_CHARACTER_LOWERCASE_SHA256",
    "layout": "single",
    "sourceFeatures": {"flatColors": false, "uv0": false, "normals": false}
  },
  "frame": {
    "unit": "metre",
    "up": "Y",
    "handedness": "right",
    "basisStatus": "DECLARED_NOT_INDEPENDENTLY_REGISTERED"
  },
  "rights": {
    "projectAuthoredClaim": true,
    "medicalSourceGeometryEmbedded": false,
    "thirdPartyCharacterGeometryEmbedded": false,
    "independentRightsReview": false
  },
  "rig": {
    "sourceToRuntimeBone": {
      "GLB_joint_A": "runtime_joint_A",
      "GLB_joint_B": "runtime_joint_B"
    },
    "runtimeBoneNames": ["runtime_joint_A", "runtime_joint_B"],
    "restWorldByRuntimeBone": {
      "runtime_joint_A": [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1],
      "runtime_joint_B": [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]
    },
    "lateralityStatus": "EXPLICIT_MAPPING_UNVERIFIED"
  },
  "releaseApproved": false
}
~~~

The signed rest matrices must come from the source Blender character export and match the GLB inverse bind matrices. If the test fails, investigate the source/rest frames and identity mapping. **Do not move the human's bones or relax the tests to make bad geometry pass.**

- For a batched source set layout to "batched"; use explicit sourceFeatures boolean flags for genuinely present supported flat colour, UV0 or NORMAL data. Single primitive currently has no source feature adapter.
- This is a limited GLB compatibility prototype, NOT a full glTF importer. If the real character uses currently unsupported node transforms, UV/textures/materials or more mesh primitives, record the actual missing feature and have Chat extend the software; do not pretend it is ready.
- Skin bone suffixes are NOT trusted to identify anatomical left and right. Work must explicitly verify laterality and mapping, especially the historical r95 reversal.
- Source ownership/rights fields are *claims only*, not independent legal certification. CT source geometry, medical material and third-party models must not be embedded into proprietary exported assets.

## Offline preflight on Work's laptop (Node 24, no npm needed)

~~~bash
node scripts/verify-provisional-handoff.mjs /path/to/original-prototype.glb /path/to/model-handoff.json
~~~

Success prints a machine-readable JSON report with the SHA, bounded primitive count, source/runtime bone names, rest numerical residual and explicit unapproved release flags. Any failure exits nonzero and must be diagnosed at the source or through a separately reviewed first-party software feature. The script prints no private GLB bytes or medical records.

Programmatic integration:

~~~js
import {validateProvisionalModelHandoff,packProvisionalModelPose}
  from './src/viewer/firstPartyPrototypeModelHandoff.mjs';
const handle = await validateProvisionalModelHandoff(glbArrayBuffer, manifest);
const sourceJointOrderPosePalette =
  packProvisionalModelPose(handle, runtimeBoneWorldPoseMap);
~~~

The validated handle is **PROTOTYPE ONLY**; full-body human muscle/skin movement, source rights, anatomical joint centres, realistic loads, performance, application export and distribution remain unverified.

## Test boundary and next steps

New first-party fixture tests cover actual GLB SHA, input mutation safety, multi-mesh GLB and all skin-joint binds, explicit source/runtime naming, missing/duplicate/forged source parts, malformed frames/rights declarations, invalid or reflected rest matrices, pose packing and tamper rejection. An actual filesystem CLI test runs the same gate with temp GLB/JSON files. CI also exercises earlier GLB and GPU LBS tests and the unchanged legacy-editor typecheck/build.

Passing *synthetic* fixture/CLI tests is **not** evidence of a correct ORIGINAL-v1 human. Next steps are richer original material/texture support and then early compatibility with Work's real provisional mesh and pose metadata. Do not remove Three.js or temporary third-party exercise clips before true original human model and full app parity.
