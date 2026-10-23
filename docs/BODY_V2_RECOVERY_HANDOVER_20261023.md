> **Cloud recovery follow-up, 23 October 2026:** isolated [draft PR #125](https://github.com/anyangle1409-code/animation-software/pull/125) now configures Blender 5.2.0 / Python 3.13 recovery, retained artifacts, four native validation jobs and guarded PR124 muscle staging. GitHub confirms Blender/dependency installation passed in [initial run 39916468327](https://github.com/anyangle1409-code/animation-software/actions/runs/39916468327). Reconstruction remains in progress; no rebuilt model or anatomy pass is claimed yet. [Expanded run 39918805189](https://github.com/anyangle1409-code/animation-software/actions/runs/39918805189) is queued and reuses completed exact model bytes when available. See `docs/BODY_V2_ACTIONS_RECOVERY_LEDGER_20261023.md`; final cloud results will be appended below. The original blocked-session account follows unchanged.

# Body v2 recovery handover — 23 October 2026

**Bottom line: no Blender file was rebuilt, saved, rendered or tested in this session.** The session's container had no
Blender or `bpy`, and its network gateway refused every route to get one. Everything that needed Blender is BLOCKED, and
nothing below claims otherwise. What this session did produce: pinned source identity, an offline evidence audit that
passes, one command that rebuilds and verifies everything on a machine with `bpy`, and a derived shoulder/arm muscle
work order.

`PT_MODEL_VERSION` is untouched at `1.0`. No production asset, `ORIGINAL_v1`, validated skeleton or existing `.blend`
was opened for writing, modified or overwritten. Nothing was merged or deployed.

## Result matrix (your 8 priority items)

| # | Task | Status | Evidence |
|---|---|---|---|
| 1 | Reconstruct W8 / v13s | **BLOCKED** | No `bpy`. Command is ready: `scripts/body_v2/rebuild_w8_v14_verified.sh` |
| 2 | Reconstruct v14 (legs, feet, torso) | **BLOCKED** | Same script, step 2. v14b is the default-settings output of `legs_v2_blender.py` |
| 3 | R120, separate and experimental | **BLOCKED** | Same script, step 3, written to its own `R120_base/` and `R120/` folders |
| 4 | Verify against original evidence | **PARTIAL** | Offline: 18/18 PASS (see below). Rebuilt files: not possible, none exist |
| 5 | Save the Blender files safely | **BLOCKED** | The script refuses an existing output folder and makes outputs read-only |
| 6 | Front/side/back/three-quarter renders | **PARTIAL** | Archived reviewer renders only, in `docs/recovery_20261023/archived_renders_v13s_v14a_v14b.jpg`. **Not** freshly rendered |
| 7 | Skeleton, joint, deformation, exercise tests | **PARTIAL / BLOCKED** | Python: PR #124 38/38 PASS. TypeScript suite (`vitest`) and every Blender benchmark: BLOCKED, `npm` and PyPI unreachable |
| 8 | Paths, SHA256, Blender version, commits, results | **PARTIAL** | This document. No `.blend` paths or hashes exist yet |
| — | Muscle work (PR #124), shoulders and arms first | **PREPARED, NOT STARTED** | Worklist below. No isolated model copy was made because the model is not verified |

## Why Blender was not available

- `pip install bpy==5.2.0`: `pypi.org:443` answered **403 (policy denial)** from the egress gateway. Direct DNS also fails,
  because `pypi.org` is on the session's no-proxy list.
- `https://download.blender.org/`: **403** through the same gateway.
- `npm ci`: `registry.npmjs.org` unresolvable. A half-installed `node_modules` was deleted.
- GitHub is reachable (clone, fetch, push), but it hosts no `bpy`.
- The proxy README says not to retry or route around 403s, so I stopped.

## Pinned identities

| Item | Value |
|---|---|
| Repository | `anyangle1409-code/animation-software` |
| Branch of this work | `claude/home-gym-pt-animation-txux66`, started from `97a5dc33d2a692fd83d9dddfdc4a418e57af135c` |
| `main` | `287f72c6a6ac9b1dcd771946ef548d77a40b8ea1` |
| R41/R57 source commit | `025d5f28fa7eba2064fba565b1c9b60119cdd2cb` on `codex/r57-local-s7-temporal-study-20261020` (fetched, checked out as a separate worktree) |
| PR #124 head (muscles) | `7c820d6` (`work/experimental-anatomical-muscles-20261022` lineage; **not merged**) |
| R41 input `.blend` | `ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend` |
| R41 SHA256 | `4c44b1fe14aeefd9a976f45baada60b4b81aaaa7cd736a300ca7cede2b0aaf2e` — 5,294,269 bytes, zstd-compressed. Matches the hash PR #124 pins |
| Blender / Python for the rebuild | `bpy` 5.2 wheel with Python 3.13 (from `docs/BODY_V2_BLEND_SOURCES.md`). PR #124 says R57 specifies Blender 5.2.1. **Neither was verified installed** |

### The four W8 screenshots

PR #124 pins their hashes (`CURRENT_W8_VISUAL_QA_20261022.md`). The image files are in no repository I can reach, so I
could not check them, and **screenshots cannot prove which `.blend` produced them**.

| File | SHA256 |
|---|---|
| `full_w8.jpeg` | `b9f92d67a2948a5776ccb6375af94058c142017ffb73a548fb243e7613a12438` |
| `arm_front.jpeg` | `93bac98ed25e79391f37aee2d57fcc9f05070fc7230a1b10eedebdc4f8d33a8d` |
| `legs_front.jpeg` | `e7405219a10e066529880e63b5bc0d5f84e6545c84a970260b54269d27516d9f` |
| `feet_side.jpeg` | `6894aeb202655d6d9865cd8e25a4da95b6424ace5f5c6863b6ee0137910acd99` |

If you hold the files, `sha256sum` them against this table. A match only confirms you have the same images.

## What the three Blender files are, and what is not confirmed

`docs/BODY_V2_BLEND_SOURCES.md` states that `body_v2.blend` (v13s / **w8**, ~200 MB), `body_v2_legs.blend` (v14a, ~200 MB)
and `body_v2_rebuilt.blend` (R120, ~300 MB) were **never committed**. They are reproducible from scripts in this repo plus the R41 input.

- **Not confirmed:** that any rebuilt file is byte-identical to the one saved in the original session. Blender saves are
  not byte-reproducible, so the verifier compares content (counts, a basis-mesh hash, report values), not the file hash.
- **R52/R57 work is not in a rebuilt W8.** The builder starts from R41 and installs its own S7 deltoid keys. R52 with S7 muted
  equals R41, R57 was rejected in the R58 handoff, and PR #124 says R41 alone does not contain the R52/R57 unsaved increments.
  Whether the original session's W8 file had any of it cannot be known from the repo.
- **Left/right is not verified.** The verifier's `mirror_x_max_dev_mm` measures geometric mirror symmetry only. PR #124 warns
  that anatomical left (+X) may map to runtime `_r` (finding F-SIDE-001), so `_l`/`_r` suffixes must not be trusted.
  Anatomical side needs an independent landmark-based check on the rebuilt file.
- **Which Blender last saved the original W8:** unknown. The verifier prints `bpy.data.version` for any file you give it.

## What was actually verified (executed in this session)

`python3.13 -I scripts/body_v2/verify_offline_evidence.py <repo> <r57src> docs/recovery_20261023/offline_evidence_check.json`
→ **18 PASS, 0 FAIL**:

- R41 hash equals the pinned value; size 5,294,269.
- v13s: 21,600 → 219,974 vertices; offsets array is 219,974 × 3 and finite; largest offset 104.29 mm; standing-pose
  self-intersections 0; mirror symmetry 0.0117 mm.
- v14a and v14b: 77 vertex groups, 79 shape keys, 219,974 → 238,067 vertices, stature 1.8562 m before and after, 0 winding
  conflicts, 0 new non-manifold edges, both feet 26,877 vertices / 289.6 mm.

This proves the archived evidence is internally consistent. It says nothing about a rebuilt `.blend`.

Also executed: `compare_rebuild_to_archive.py` self-test (4/4 PASS against the archive itself) and PR #124's own suite:
`python -m unittest discover -s experiments/anatomical_muscles/tests` → **38 tests OK**; `visual_qa` → PASS with
`native_validation: NOT_RUN`; all 12 exercise phases compile.

Syntax-checked only, never run against Blender: `verify_body_v2_blend.py`, `rebuild_w8_v14_verified.sh` (`bash -n`).
**Treat their first real run as a test of the scripts as well as of the model.**

## Run this on a machine with Blender (about 45 min)

```
git clone https://github.com/anyangle1409-code/animation-software && cd animation-software
git checkout claude/home-gym-pt-animation-txux66
python3.13 -m venv .venv && . .venv/bin/activate
pip install "bpy~=5.2.0" numpy scipy scikit-image lazy_loader packaging Pillow   # the docs say "bpy 5.2 wheel"; exact patch version unrecorded
scripts/body_v2/rebuild_w8_v14_verified.sh ~/hgpt_recovery_20261023
```

Outputs (all read-only afterwards): `W8/body_v2.blend`, `V14/body_v2_legs.blend`, `R120/body_v2_rebuilt.blend`
(experimental), `verify/*.json`, `verify/comparison_new.jpg`, `MANIFEST.sha256`. Judge W8 by
`verify/w8_vs_archive.json` (rig edits identical to archive, report numbers within 1e-4, offsets within 0.01 mm) and
`verify/w8_blend.json`. Add `--skip-r120` to skip the experiment.

### Accessible method for obtaining the verified files

None exists yet, because no files were built. Once the script has run and the verify JSONs show PASS, publish with a
GitHub Release (asset limit 2 GiB each, so the 100 MB repo limit does not apply; do **not** commit them):

```
gh release create body-v2-recovery-20261023 --repo anyangle1409-code/animation-software \
  --target claude/home-gym-pt-animation-txux66 --prerelease \
  --title "Body v2 W8 / v14 / R120 rebuilt blends (unreviewed)" --notes-file ~/hgpt_recovery_20261023/MANIFEST_HEADER.json \
  ~/hgpt_recovery_20261023/W8/body_v2.blend ~/hgpt_recovery_20261023/V14/body_v2_legs.blend \
  ~/hgpt_recovery_20261023/R120/body_v2_rebuilt.blend ~/hgpt_recovery_20261023/MANIFEST.sha256
```

Anyone downloading must run `sha256sum -c MANIFEST.sha256`. Keep R120 labelled experimental.

## Muscle work (PR #124)

Read in full: `CLAUDE_HANDOFF.md`, `EXERCISE_MUSCLE_CONTRACT.md`, `CURRENT_W8_VISUAL_QA_20261022.md`. Its package is
standard-library Python only and passes here.

**Attachment was not started** because the contract requires the correct model first, then a native rig inventory, then
reviewed landmarks, and I have no Blender. Inventing anchors would be fabrication, so I did not.

Prepared: `docs/recovery_20261023/muscle_attachment_worklist_shoulder_arm.json` — **42 records** (14 shoulder, 14 arm, 14
scapula), 30 of them referenced by the curl and shoulder-press contracts; every field is copied from PR #124 or counted;
every binding is still unresolved. Order: one shoulder side, verify the contralateral side independently, then arms.

After a verified v14 exists, on the PR #124 lineage:

```
python -m experiments.anatomical_muscles.prepare --source <V14/body_v2_legs.blend> \
  --out <new_dir>/HomeGymPT_V14_MUSCLE_EXPERIMENT.blend --sha256 <sha256 of the source>
blender --background --factory-startup --disable-autoexec --python-exit-code 1 \
  --python experiments/anatomical_muscles/inspect_blender.py -- <that copy> <sha256> <inventory.json>
```

`inspect_blender.py` has never been executed by anyone. The first visual priorities (from the W8 screenshot triage) are
`W8-VIS-AXILLA-001` (axillary slit) and `W8-VIS-SHOULDER-002` (spherical shoulder cap).

## Known failures and open items

- Every Blender-side check, render, benchmark and the TypeScript tests: **not run**.
- Previously recorded failures stay failed: PR107 preserve-volume, PR113 W4 refit and hip-fold, R54/R55/R57 shoulder
  experiments (see `CLAUDE_HANDOFF.md`, "Prior failures").
- R120 "is still being validated" per the sources doc; its status here is unknown.
- Left/right, R52/R57 contents and the original W8 provenance remain unconfirmed, as above.

<!-- CLOUD_RECOVERY_RESULTS -->

# Cloud Body v2 recovery results

Run: https://github.com/anyangle1409-code/animation-software/actions/runs/39918805189
Commit: `6e4823e50ce8081fc5ec3a722d88dfa4e03ca1bb`

Reconstruction/archive checks: FAIL / INCOMPLETE.
All 13 × 9 movement paths executed for all four inputs: False.
Zero collapse/stretch/intersection quality gate across all inputs: False.
Application and pinned test suites: FAIL / INCOMPLETE; exit codes {'vitest': '0', 'typecheck': '0', 'scripts': '1', 'scripts_tests': '1', 'scripts_blender_tests': '1', 'muscles': '0', 'guards': '0'}.
Anatomical and visual approval: NOT GRANTED. R120 remains EXPERIMENTAL.

| Model | Path | SHA256 |
|---|---|---|
| W8 | W8/body_v2.blend | 2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c |
| V14 | V14/body_v2_legs.blend | 5969aa98122e267b6bdd94fdfaf6d2877a1b27f7ea8d11c6a8e078b467b0ff91 |
| R120 | R120/body_v2_rebuilt.blend | fb3b0acfc68bc59952b0fc6c45f7d7715717207fd9ba0b7f2b124e905ce2ddcb |

See RECOVERY_RESULT.json, verify/, native/, tests/, native/V14/muscle/ and logs/ for exact failures and discrepancies.
Missing reports or renders are never a pass. Raw failure counts across different mesh topologies are diagnostic, not a like-for-like improvement claim.
W8 screenshot source identity and unsaved R52/R57 increments remain unresolved.
PT_MODEL_VERSION 1.0 preserved. No production replacement, merge or deployment.
