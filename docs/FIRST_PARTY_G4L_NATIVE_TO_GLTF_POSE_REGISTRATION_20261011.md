# G4l — Work native Blender Z-up ROW-MAJOR ↔ actual original glTF Y-up COLUMN-MAJOR source registration

**Sunday 11 October 2026 • Chat Lane G • actual original Work shoulder artifact, NOT full human approval**

## Why this matters

The W1 PR #68 Blender source artifact has seven truly authored diagnostic shoulder pose records for angles 0, 45, 90, 135, 160, 90, 0 **degrees rotation FROM REST**, with six source clavicle/scapula/humerus controls. Every control stores `rest_world_row_major`, `pose_world_row_major`, `skin_palette_native_row_major` in native Blender **+X anatomical left / +Y posterior / +Z superior**. The shipped GLB uses native glTF **Y-up, right-handed, column-major** world matrices. Treating native ROW matrices as GLB columns, or treating authored degrees as absolute humerothoracic elevation, would produce wrong shoulder animation despite passing unrelated primitive skinning tests.

## Independent original-source basis finding

Against the actual immutable original GLB source SHA `fda9c5e653044988fd1e5c58fe352f074071c4be008eceba702bbbef96a4ea5f`, the **world** basis is a left multiplication `GltfWorld = BlenderToGltf * NativeWorld`, where `BlenderToGltf = Rx(-90°)` rotates native +Z superior to glTF +Y superior and native +Y posterior to glTF -Z. This is NOT a blind conjugation of every world transform. All 6 original source rest matrices independently match actual original GLB hierarchical source Y-up/rest within ~1e-6 and glTF/source inverseBind values independently match the actual authored native SKIN matrix with `GltfSkin = BlenderToGltf * NativeSkin * GltfToBlender` across all seven frames. The mathematical basis is proper (determinant positive), does not scale, reflect or reposition anatomical bones.

## Implementation

New source module `src/viewer/firstPartyWorkNativePoseRegistration.mjs` accepts only:
- A genuine G4/first-party **SHA256-verified** in-memory original project source model handle with all 18 actual source meshes and 6 properly ordered joint node inverse binds.
- Independently derived G4j original Y-up glTF WORLD REST for every source bone, `restWorld × sourceInverseBind ≈ I`.
- Authentic Work W1 unapproved `pilot_manifest.json` source declaration, explicit native and GLB coordinate conventions, six exact source control labels with no missing bones or unexpected extra variants, and original GLB exact pinned source SHA.

For every one of the seven input samples the module independently checks the **native-rest-to-original glTF world REST** residual and the **native authored skin-palette vs original glTF poseWorld×inverseBind** residual for all six source bones; 0° and return-to-0° palettes must be near identity. Then it passes each converted 6-bone palette through the G4 original in-memory source rig pose validator, snapshots 7 source palettes privately (WeakMap), and returns only typed diagnostic source metadata. A caller may retrieve one exact original source authored joint palette at a time through `readRegisteredWorkPoseFrame(handle,index)`; no interpolation, new exercise motion generation, fake body proportions or clinical approval can be implied.

## Real CI proof

Dedicated Actions workflow downloads *exact previously verified* Work W1 PR68 CI artifact #11706909894, reads its original SHA-verified GLB plus all seven native pose records and executes the complete 18-mesh G4 SHA/rig + G4j WORLD REST + G4l frame converter. It rejects incorrect source joint palette, wrong pose identities, nonaffine/unfinite matrices, changed source bytes and attempts to infer arbitrary exercise data. It uploads **only JSON numeric residuals and original authored sample metadata**, not original Work binary/native Blender files. The inherited G4j and pose tests also run. **Only claim success after exact-head CI**.

## Hard open limitations

This proves **coordinate-system and authored source-skin numerical parity**, not physical/clinical accuracy of shoulder exercises: the authored 160° sample is rotation-from-rest and not independently measured absolute humerothoracic elevation, Work PR71 fixes a later profile but does not replace the PR68 model's current seven source-pose records. The pilot is shoulders only and has not been independently tested against real loaded human videos, scapula/rib/thorax contact or naturally deforming full-body male muscle/skin; rights/production approval remain false. Work owns that development.

**Next Chat step:** G4m use the real converted palettes to move all 18 actual Work source meshes in Chromium WebGL2; verify GPU capture vs independent CPU source-mesh skinning, source colour, frame-to-frame geometry movement and exact authored 7-frame order while clearly captioning the demonstration as unverified authored diagnostic rather than accepted realistic human motion. PT App current 304 temporary reference clips remain unchanged. Review ledger `docs/CHAT_LANE_G_OVERNIGHT_LEDGER_20261011.md` and share progress on Work PR #26.
