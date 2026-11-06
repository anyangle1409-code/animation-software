# Home Gym PT — F12d ZIP transfer verification receipt (2026-11-06)

**Status:** Seven of seven model ZIPs and the START_HERE ZIP received in the user's ChatGPT conversation; F12d bytes successfully reconstructed and verified in the ChatGPT working container. **The model is still a WIP candidate, NOT approved as Female V1.**

## File receipt / byte-for-byte verification

- Reconstructed file: `HGPT_Female_F12d_ChestShorts_WIP.blend`
- Actual size (independent read): **151,227,275 bytes**.
- Independently calculated SHA-256 on the assembled file:
  `89df9517421d983e0de812efd2d18a660e19bd6fa0284cdc45945b19affa3b6c`
- This exactly matches the Claude-supplied `MANIFEST.json` full-file checksum and byte size.
- For each of parts 01–07, ZIP file size + ZIP SHA-256 + the uncompressed part's size + the uncompressed part's SHA-256 were individually checked against that manifest.
- The `HGPT_F12d_START_HERE.zip` passed ZIP archive integrity checking and path traversal safety checks, and its contents were extracted.
- Independent SHA-256 of `HGPT_F12d_START_HERE.zip`: `ca8e8b27e56c114ee5d38f821b91cbb71e15c75a40dd59704e25da7028b43a00`.
- Source Claude transfer commit now at `8056f71ddc42415fa266766974a4cd2f119b10b9` (manifest, guide, verification script pushed). Its earlier F12d modelling commit is `3bee9e1f1f6f8ca8fe21bcbec0ef892974cb14ca`.

## Verification scope / honest limitations

- This establishes the **exact original bytes** have survived transfer. This container did **not** have Blender 5.2.x installed, so a fresh Blender file-open check **has not** been independently performed by ChatGPT. Claude's supplied `F12d_verify_blender521.json` is an expected-baseline report, **not proof of a new Work check**.
- Work must obtain the actual eight ZIP attachments or reconstructed `.blend` through an authorised private file transfer. A GitHub receipt or GitHub commit does not contain licensed geometry.
- Before editing, Work must reconstruct or receive the model, check the full hash, and open it in Blender 5.2.x. It must independently compare object counts, image packing, armature/weights, geometry and external dependency state against `F12d_verify_blender521.json`.
- The model is **unapproved**; user still wants correction of bra and shorts shape/fit before final standing approval. Full movement development remains paused. Preserve Male 07c and earlier checkpoint files without editing.
- Reported F12d unresolved quality concerns: visually pointed shorts gusset and waistband, **12 uncovered skin vertices at hip 90°/knee 90°**, bra one non-manifold edge and strap knots, 52 hand self-intersection pairs and thumbs, low-quality ponytail. Bone-weight sums >1 on some body vertices must be normalized/checked before external engine export.
- **Source licence**: original Meshy generation rights must be confirmed prior to public distribution.

## Work starting instructions

Read `docs/WORK_F12D_CONTINUATION_20261106.md`, then Claude's latest `review-assets/meshy_retopo_20261105/README.md`, the F12d reports and the transfer `START_HERE.md`/`MANIFEST.json`. Work should branch off the latest Claude source commit or an equivalent isolated branch, avoiding any writes to Claude's branch; store licensed model data privately, not in public GitHub. Do not start any edits without byte-identical model availability and fresh Blender check. Continue only female standing model correction and limited structural preflight, then stop for user's visual approval.

## Backups still needed

- Female F11a rollback remains only in Claude's temporary session unless independently exported.
- Approved Male 07c `.blend` is reported as ~18 MB in the Claude session, not part of these eight ZIPs.
- User intends permanent Male/Female anatomical and appearance V1 packages on Windows laptop after approvals. Do not label F12d as a final V1.
