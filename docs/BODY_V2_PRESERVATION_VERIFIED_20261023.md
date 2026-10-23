# Preservation and read-only verification — 23 October 2026

**These are RECONSTRUCTIONS. They are not confirmed original Claude-session files.**

All three downloaded ZIPs match the live GitHub API digests and supplied digests. All three extracted Blender files match both the supplied recovery-doc hashes and their included SHA256SUMS.txt. No mismatch or network denial occurred. Three private ZIP copies were saved outside Actions, with successful storage receipts; source and extracted-copy hashes were rechecked afterward. No public release or draft release was created.

Read-only inspection run: https://github.com/anyangle1409-code/animation-software/actions/runs/39934502593 (SUCCESS). Inspection code commit: `f73230e922faa9525de120fcfef65b6900ef0417`. Source branch and production assets untouched. No .blend rebuilt, saved, overwritten or repaired. Only new inspection copies were opened.

## Per-model checks

### W8

| Check | Evidence | Result |
|---|---|---|
| Artifact | run39922636070 / 12487119841 | PASS: downloaded, not expired |
| ZIP SHA256, computed vs GitHub API vs supplied | All equal `0a26a895e43922aef1d8872f2e54bb53b88ca6e9c39428060472b75d6f1c2272` | PASS |
| .blend SHA256, computed vs docs vs included manifest | All equal `2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c` | PASS |
| Exact size | ZIP 207,925,544 bytes; .blend 208,036,008 bytes | PASS: measured |
| Saved-by field | bpy.data.version = (5, 2, 44); verifier string 5.2.44 | PASS: field read, not original-session version |
| Running inspection Blender | 5.2.0 LTS | PASS |
| Vertices / polygons / native loop triangles | 219,974 / 439,944 / 439,944 | PASS: measured |
| Groups / shape keys / rig bones | 77 / 79 / 77 | PASS: 77/79 expected inventory |
| Rig | `HGPT_CANONICAL_V4_ORIGINAL` | PASS: object present |
| Modifiers | One Armature modifier, target HGPT_CANONICAL_V4_ORIGINAL; use_deform_preserve_volume=false | PASS: measured |
| Basis content, Claude verifier | `25254ead9cbae1c0df5865c97986ec9be23c0183adacd506ca684c199e24f6d9` | PASS: measured hash, quantized mesh coordinates at 0.01 mm |
| Basis content, independent explicit representation | `37e6f02480bab67230f299ba0609d8e186be3047218e347d9631a7e965ff3301` | PASS: shape-key index0, float64 little-endian, local-space vertex order |
| Basis vs mesh coordinates | True | PASS: coordinates identical at inspection |
| Native preservation | Before/after source and inspection-copy hashes equal | PASS |
| Claude verifier | 4 PASS / 0 FAIL with expected_key=none | PASS for these four limited checks only |
| Permanent private copy | W8_UNVERIFIED_RECONSTRUCTION_20261023.zip | PASS: saved outside Actions; no Actions expiry applies to this copy |
| Source commit / settings | Shared provenance and per-model settings below | Documented; original-session provenance BLOCKED |
| Archive equivalence | W8/v14 discrepancies below; R120 has no approved equivalent archive | FAIL / NOT_ESTABLISHED |
| Anatomical approval / muscle attachment | No approval; no attachment | BLOCKED |

### V14

| Check | Evidence | Result |
|---|---|---|
| Artifact | run39922636070 / 12487932177 | PASS: downloaded, not expired |
| ZIP SHA256, computed vs GitHub API vs supplied | All equal `a0b42c23c1346afca1729b52460a5d79c3b0dd0f378c8e9e51a6dc676398ce64` | PASS |
| .blend SHA256, computed vs docs vs included manifest | All equal `5969aa98122e267b6bdd94fdfaf6d2877a1b27f7ea8d11c6a8e078b467b0ff91` | PASS |
| Exact size | ZIP 210,721,114 bytes; .blend 211,149,283 bytes | PASS: measured |
| Saved-by field | bpy.data.version = (5, 2, 44); verifier string 5.2.44 | PASS: field read, not original-session version |
| Running inspection Blender | 5.2.0 LTS | PASS |
| Vertices / polygons / native loop triangles | 238,065 / 419,870 / 476,126 | PASS: measured |
| Groups / shape keys / rig bones | 77 / 79 / 77 | PASS: 77/79 expected inventory |
| Rig | `HGPT_CANONICAL_V4_ORIGINAL` | PASS: object present |
| Modifiers | One Armature modifier, target HGPT_CANONICAL_V4_ORIGINAL; use_deform_preserve_volume=false | PASS: measured |
| Basis content, Claude verifier | `f4d8bfc043dab9c45d13ac242165cc60c9a684b890906ac3e4eba1bb8970ef92` | PASS: measured hash, quantized mesh coordinates at 0.01 mm |
| Basis content, independent explicit representation | `9a86cd7b4bc247f8d98a732c529c847fce8f416fb23d6cd2e06d71595abc4563` | PASS: shape-key index0, float64 little-endian, local-space vertex order |
| Basis vs mesh coordinates | True | PASS: coordinates identical at inspection |
| Native preservation | Before/after source and inspection-copy hashes equal | PASS |
| Claude verifier | 4 PASS / 0 FAIL with expected_key=none | PASS for these four limited checks only |
| Permanent private copy | V14_UNVERIFIED_RECONSTRUCTION_20261023.zip | PASS: saved outside Actions; no Actions expiry applies to this copy |
| Source commit / settings | Shared provenance and per-model settings below | Documented; original-session provenance BLOCKED |
| Archive equivalence | W8/v14 discrepancies below; R120 has no approved equivalent archive | FAIL / NOT_ESTABLISHED |
| Anatomical approval / muscle attachment | No approval; no attachment | BLOCKED |

### R120 — EXPERIMENTAL

| Check | Evidence | Result |
|---|---|---|
| Artifact | run39922636070 / 12488550235 | PASS: downloaded, not expired |
| ZIP SHA256, computed vs GitHub API vs supplied | All equal `a282c8a4e0e80051b80ca5b9c437cf55f6fa2a6d4bf5f0d4e3ac4fa54ee74ca8` | PASS |
| .blend SHA256, computed vs docs vs included manifest | All equal `fb3b0acfc68bc59952b0fc6c45f7d7715717207fd9ba0b7f2b124e905ce2ddcb` | PASS |
| Exact size | ZIP 314,408,162 bytes; .blend 314,795,547 bytes | PASS: measured |
| Saved-by field | bpy.data.version = (5, 2, 44); verifier string 5.2.44 | PASS: field read, not original-session version |
| Running inspection Blender | 5.2.0 LTS | PASS |
| Vertices / polygons / native loop triangles | 347,840 / 645,944 / 695,524 | PASS: measured |
| Groups / shape keys / rig bones | 77 / 79 / 77 | PASS: 77/79 expected inventory |
| Rig | `HGPT_CANONICAL_V4_ORIGINAL` | PASS: object present |
| Modifiers | One Armature modifier, target HGPT_CANONICAL_V4_ORIGINAL; use_deform_preserve_volume=false | PASS: measured |
| Basis content, Claude verifier | `cbb49062d2566eaa9295c273278cfb44fb085562938ac474f36d5967e8bc37ec` | PASS: measured hash, quantized mesh coordinates at 0.01 mm |
| Basis content, independent explicit representation | `dddcd0627dcdcf6d12fb840f9a6e3dc8636d35484aea5edf93aba56840474e12` | PASS: shape-key index0, float64 little-endian, local-space vertex order |
| Basis vs mesh coordinates | True | PASS: coordinates identical at inspection |
| Native preservation | Before/after source and inspection-copy hashes equal | PASS |
| Claude verifier | 4 PASS / 0 FAIL with expected_key=none | PASS for these four limited checks only |
| Permanent private copy | R120_UNVERIFIED_RECONSTRUCTION_20261023.zip | PASS: saved outside Actions; no Actions expiry applies to this copy |
| Source commit / settings | Shared provenance and per-model settings below | Documented; original-session provenance BLOCKED |
| Archive equivalence | W8/v14 discrepancies below; R120 has no approved equivalent archive | FAIL / NOT_ESTABLISHED |
| Anatomical approval / muscle attachment | No approval; no attachment | BLOCKED |

The saved-by field `(5, 2, 44)` is recorded literally. It must not be turned into a claim that a marketed Blender patch release called 5.2.44 made Claude's originals. Their last-saving Blender version remains UNKNOWN. The running app reports 5.2.0 LTS. Hashes of quantized coordinates and exact coordinate bytes are different definitions and are not expected to match. Neither coordinate hash alone includes topology, weights, keys or rig data. Ordered-polygon hashes and complete group/key names are in the evidence JSON.

## Source and settings

The bytes were first built by Actions run39916468327 at `ca444ce7fd749d607e698e1d70922212567e04a2`, then repackaged unchanged by run39922636070. The Claude source/handover revision is `9fb56a2763cda3036421c075013277bd5dee262e`, built on97a5dc3. That is script provenance, not proof of exact archive reproduction.

Input R41: `ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend` at `025d5f28fa7eba2064fba565b1c9b60119cdd2cb`; documented input SHA256 `4c44b1fe14aeefd9a976f45baada60b4b81aaaa7cd736a300ca7cede2b0aaf2e`. This preservation pass did not redownload/hash that separate input, so this input provenance is cited from existing workflow/evidence, not newly independently checked.

Recorded build environment: Python3.13, bpy5.2.0, numpy/scipy/scikit-image/lazy_loader/packaging/Pillow. Render overrides: V2_SKIN_SCALE=1, V2_SKIN_SAMPLES=24; PY=python, LIBGL_ALWAYS_SOFTWARE=1, OPENBLAS_NUM_THREADS=1, OMP_NUM_THREADS=2. Source commands inspected in .github/workflows/body-v2-recovery.yml at01f1e9 and pinned rebuild_w8_v14_verified.sh:

| Model | Recorded reconstruction settings |
|---|---|
| W8 | V2_SAVE_BLEND=1; build_body_v2_sculpt_blender.py with R57-source checkout, new W8 output, positional scale2.0; v13s/w8 defaults |
| v14 | legs_v2_blender.py on reconstructed W8, default legs/feet/torso settings (v14b intent) |
| R120 | Separate legs-only base with V2_TORSO_RELIEF=0 and V2_PEC_JUNCTION=0; rebuild_v2_blender.py; experimental |

The unchanged Claude verifier was fetched from9fb56a2 and executed on actual Blender in this pass. Its expected_key=none mode makes four checks: body present, rig present, armature target present, file bytes unchanged. It does not test archive counts, anatomy, side mapping or movement acceptance. Its plain-skinning label only checks an armature tuple; the supplementary inspection separately measured Preserve Volume=false.

## Failed archive and movement gates

- W8 offset-array maximum3.59286mm vs0.01mm guard; proportion maximum0.837573mm. Correspondence is not established: these are array discrepancies, not proven anatomical point displacements.
- v14 has238065vertices vs238067archived:2fewer.
- 1skeleton/12W8/10v14 JSON differences retained; skeleton Y-shift difference0.000432mm.
- R120 is experimental with no confirmed archive equivalence.
- All3 fail grip solver and zero-collapse/stretch/intersection gates in recorded movement diagnostics. The production67-bone bridge is incompatible with77authoring bones. Anatomical approval NOT_GRANTED.
- No evidence establishes unsaved R52/R57 increments in these reconstructions or establishes which original blend generated the four W8 screenshots.

## Preservation locations and limits

The three private ZIP copies are independently accessible as the three named deliverables accompanying this report. Each contains the untouched reconstructed .blend and its original SHA256SUMS.txt. The live Actions API confirms model artifacts expire2027-01-21 at08:09:09UTC. Their private copies do not depend on Actions retention. No original files were found or claimed to exist by this preservation pass. Storage creation receipts establish successful copying; no separate remote read-back of those private copies has been performed.

Native report artifact IDs: W8=12492858388,V14=12492614380,R120=12493008077 (run39934502593). Report ZIPs were downloaded and digests verified. Reports and manifests are also preserved with this deliverable.

## Locate the originals

Please check the machine and the Blender process that created the earlier files. Original W8/v14/R120 existence is still unconfirmed.

1. Keep any open unsaved Blender session open. Before opening another file or recovering a backup, preserve the open state using File > Save Copy into a NEW EMPTY folder, with a new name such as HomeGymPT_W8_RECOVERY_20261023_143000.blend. Do not use Save or Save As. If your version does not offer Save Copy, stop before choosing another save operation.
2. Inspect File > Open Recent. Also inspect recent-files.txt under Blender's version-specific config directory:
   Windows: %APPDATA%\Blender Foundation\Blender\<version>\config\recent-files.txt
   macOS: ~/Library/Application Support/Blender/<version>/config/recent-files.txt
   Linux: ~/.config/blender/<version>/config/recent-files.txt
   A recent-files entry proves only a path was recorded, not that its bytes still exist.
3. Check the configured Temporary Files directory in Edit > Preferences > File Paths and the system temp directory (%TEMP% on Windows; $TMPDIR or /tmp on macOS/Linux). Look for quit.blend, *_autosave.blend and other .blend autosave files. Do not quit the original session to look for quit.blend; quitting may replace last-session recovery data.
4. Search the original project directories and backup/cloud-sync locations for *.blend, *.blend1 and *.blend2, including body_v2.blend, body_v2_legs.blend and body_v2_rebuilt.blend. Copy candidates into separate new suffixed folders before opening. Preserve their original filenames, modification dates and paths as evidence. A .blend1 is a backup, not automatically the desired final version.
5. Only after preserving an open unsaved state, File > Recover > Last Session or Auto Save can help locate recovery files. Work from copied recovery files and never save over the source. Screenshots alone cannot identify the generating .blend.
6. Hash each recovered COPY:
   Windows PowerShell: Get-FileHash -Algorithm SHA256 -LiteralPath 'C:\new-folder\HomeGymPT_W8_RECOVERY_20261023_143000.blend'
   macOS: shasum -a 256 '/new-folder/HomeGymPT_W8_RECOVERY_20261023_143000.blend'
   Linux: sha256sum '/new-folder/HomeGymPT_W8_RECOVERY_20261023_143000.blend'
7. Supply the copied files, SHA256 values, source path/session, and known commit/settings. Until compared, label them recovered session candidates rather than confirmed originals. Compare bytes, topology, Basis coordinates, weights, keys and rest skeleton before inferring equivalence.

No original Blender version, unsaved R52/R57 increments, screenshot provenance or anatomical side is established by these instructions.


## Later-stage status

Anatomical left/right remains BLOCKED for certification: object/bone names and mirror symmetry are not independent landmark-orientation evidence. The inventory lists saved landmark objects but this pass does not certify their anatomical sides. F-SIDE-001 must be resolved with native positional/visual evidence before bindings are accepted.

PR124 handoff and exercise contract at7c820d68de69dcdef7d567e836302123df953446 were read. Permanent IDs and independent curl/press/squat contracts are preserved. Source/content acceptance and reviewed landmark gates remain failed/unresolved; user approval is additionally required before attachment. The42record shoulder/arm worklist has no invented anchors. No muscle attachment, geometry, weight or corrective change was started.

