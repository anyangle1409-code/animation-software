# G4k — original Work 18-mesh shoulder Blender GLB → true native GPU REST frame

**Sunday 11 October 2026 • First-party Chat Lane G; REAL Work source, not a generic synthetic stand-in.**

## Exact original input

Work's W1 [PR #68](https://github.com/anyangle1409-code/animation-software/pull/68) authored shoulder source GLB from CI artifact 11706909894 (run 38153765790) has 18 separate indexed skinned objects, 4,572 original vertices, six genuine source clavicle/scapula/humerus nodes and 6 original material colours. Exact GLB SHA-256 `fda9c5e653044988fd1e5c58fe352f074071c4be008eceba702bbbef96a4ea5f`. This is **not** Work's eventual approved full-body male mesh and is not clinically accepted.

Earlier G4g–G4i accepted actual original Blender scene hierarchy and source material data without altering the source bones or private Blender asset. [G4j PR #76](https://github.com/anyangle1409-code/animation-software/pull/76) then proved actual six glTF-Y-up source joint WORLD REST × inverseBind parity (max element residual ~3.3947e-7) using exact original SHA, not fake identity bones.

## New native GPU scope

- Extends the existing first-party RGBA32F four-weight skinned WebGL2 shader with an **opt-in unlit original pilot source baseColor preview**, using glTF baseColorFactor as linear and transferring to sRGB for ordinary RGBA8 framebuffer display.
- Adds explicit `renderVerifiedOriginalPilotFlatPose(g4OriginalModel,sourceWorldByBone,{eye,target})`. This calls G4's actual in-memory `packProvisionalModelPose` (protected by the original weak-reference validation plan), refusing forged JSON model handles. It uses the source mesh, exact original WorldRest pose and original source colours, retaining original material doubleSided choice, and draws **all 18 indexed source Work primitives** with the actual GPU bone matrix palette.
- Some untextured original blade objects have no UV0: because the generic WebGL vertex input still requires an aUV0 buffer, the renderer allocates zeroed GPU-only *attribute padding* that the flat-colour fragment NEVER samples. The original Work GLB, `sourceUV0:null`, its skin, materials and actual Blender mesh **remain untouched**; no authored UV coords are fabricated or claimed.
- This is a material-colour **REST-POSE screenshot** only, not physical PBR/roughness illumination, alpha/material transmission, true muscle volume/skin deformation or Work's authored motion world matrices.
- Ordinary legacy 1–8 source GPU drawing, PNG/skinned texture mode, actual source-normal mode and first-party transform-feedback CPU/GPU numeric tests retain unchanged acceptance. This pilot is restricted to the independently validated G4 original source handle, ≤24 parts / 250k vertices and diagnostic source colours.

## CI acceptance contract

The real Chromium test downloads the same pinned Work original shoulder CI artifact, checks exact source hash and source G4 WorldRest/skin, then renders the actual **18 original source meshes twice at original glTF rest** in native WebGL2. It requires 36 actual `drawElements` calls, meaningful source-colour pixels in readPixels, no GPU/browser/network errors, and GPU-captured skinned positions matching the separate first-party CPU oracle to <1e-5 metres on an original Work source triangle group. Produces a real original authored Work GLB rest framebuffer screenshot PNG plus machine JSON (but **never uploads its private .blend or re-publishes GLB source bytes**). The old editor strict typecheck/build is tested unchanged.

## Restrictions and next

The Work native seven `pilot_manifest.json` pose records use a **Z-up/row-major** authored coordinate convention, while GLB source joint transforms are **Y-up/column-major**. A green G4k REST view must not be presented as acceptance of Work's actual 45/90/160 degree animation, scapula biomechanics or motion/shaped body contact. **Next G4l** independently prove exact source-basis transform from Work authored native frames, comparing rendered joint axes against true original GLB at rest and known joint references, before any moving Work pose. Work remains solely responsible for whole-body original mesh, real exercise loading, muscle/axilla deformation and clinical evidence. PT-App 304 existing instructional clips remain untouched.

Keep the draft until exact-head CI passes. [Shared overnight ledger](https://github.com/anyangle1409-code/animation-software/blob/codex/g4j-original-work-gltf-world-rest-20261011/docs/CHAT_LANE_G_OVERNIGHT_LEDGER_20261011.md) and [Work handoff PR #26](https://github.com/anyangle1409-code/animation-software/pull/26) hold ongoing stage and evidence status.
