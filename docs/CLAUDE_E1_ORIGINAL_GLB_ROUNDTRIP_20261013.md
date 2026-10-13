# E1: ORIGINAL_v1 native → GLB → native round-trip parity (Claude, 13 Oct 2026)

**Script:** `scripts/verify_original_glb_roundtrip_blender.py`. It uses Blender 5.2.1's built-in glTF exporter on the unchanged a003 source (`670a37bf…cbbe56`).

**Isolation:**
- The GLB goes to a private temporary directory and is deleted after the run; only `ORIGINAL_V1_WORK/anatomy/audit/claude_e1/original_glb_roundtrip_report.json` is kept.
- No Lane G parser or renderer code was touched.
- This complements Lane G's PR83/85/86, which validate Work's PR81 review GLB in Node/WebGL2.

**Verdict: PASS.**

| Check | Native | Re-imported |
|---|---|---|
| Body vertices / triangles | 17,946 / 35,888 | 17,946 / 35,888 |
| Skin joints (deform bones) | 67 (67 bones) | 67; hierarchy and names identical |
| Max influences / weight sums | 4 / exactly 1.0 | — |
| Morph targets | 6 legacy shoulder correctives (`HGPT_SHOULDER_CORR/FLEX/SCAP_L/R`), all weight 0 | same 6 |
| Rest vertex mapping | — | max 5.0e-7 m |
| Posed parity: rest, shoulder abduction 90°, elbow flexion 90°, squat-like hip −90°/knee 100°, trunk flexion 30° | — | max **0.0007 mm**, mean 0.0002 mm |

GLB size: 1,492,440 bytes. Work's PR81 review GLB is 1,495,720 bytes; its bytes were not compared because it is private.

## Findings

1. **Bone-shape leak.** With `use_selection=True` on body + rig, the exporter also writes the unskinned 42-vertex `Icosphere` (the rig's bone display shape) as a second mesh. Exclude it from review and production exports, for example by clearing custom bone shapes on the export copy. Lane G's G4q preflight expects exactly one mesh, so it would reject such a file.
2. **The 67-joint contract holds through glTF.** The 95-control toe trial (Work PR105) and any helper deformer would change the joint count. They need owner and Lane G agreement (ledger F5/W3).
3. **Scope limits:**
   - This is LBS parity only. Native dual-quaternion or other skinning is not claimed.
   - No real-browser GPU check is made.
   - No exercise animation is exported.

**CI:** `.github/workflows/original-glb-roundtrip.yml` runs the check with pinned Blender 5.2.1 and fails on anything but PASS.
