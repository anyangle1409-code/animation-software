# Claude pelvic CT Blender review (2026-10-09)

Branch `claude/pelvis-ct-blender-review-20261009`, based on the live Claude head `f3f725f`. Codex PR #15 (`4680b49`) was used as a read-only source of evidence and tooling design and was not modified, merged, rebased or pushed to.

## Bottom line

- **The original CT PNGs and headers could not be reached from the cloud session** (the NLM host returned 403 through the egress policy; not retried or bypassed). Therefore **no image was viewed, no SHA was re-verified here, and no real Blender run happened**. The six SHA-256 pins are PR #15's, copied byte-for-byte (`PINNED_INPUTS_PROVENANCE.json`).
- Consequently every anatomical statement is **UNVERIFIED**. The landmark register holds 13 landmarks: **0 VERIFIED / 0 CANDIDATE / 13 UNVERIFIED**.
- What this branch delivers is a fully tested, fail-closed pipeline so the laptop run is one command, plus the skeleton-side findings that do not need CT.
- No canonical skeleton geometry was changed. No c005; c004 is untouched and unaccepted. Readiness stays 0 READY / 9 PARTIAL / 3 BLOCKED. The donor is not treated as a canonical 182 cm male.

## Live heads (after `git fetch --all --prune`)

| Ref | Commit |
|---|---|
| origin/codex/independent-pelvis-stl-intake-20261009 | `4680b49802240f3363e10f0db6c5d90cd0057cba` |
| origin/claude/skeleton-anatomical-development-20261009 | `f3f725f46c33ab1d4d480070f56ddc6b350f3d87` |
| main checkout (`/home/claude/animation-software`) | `main` at `287f72c6a6ac9b1dcd771946ef548d77a40b8ea1` |
| this branch (base) | `f3f725f`, an ancestor of the Codex branch |

The main checkout had no uncommitted work to preserve; all new work lives in a separate worktree.

## Deliverables

| Item | File |
|---|---|
| Pinned input manifest (copy) and provenance | `audit/.../pinned_six_frames_from_pr15_4680b49.json`, `PINNED_INPUTS_PROVENANCE.json` |
| Physical slice-to-region index and additional ranges | `audit/.../physical_slice_to_region_index.{json,md}` |
| Landmark candidate register (13 entries, all UNVERIFIED) | `audit/.../landmark_candidate_register.json` |
| Skeleton-versus-source report | `audit/.../skeleton_vs_source_inspection.{json,md}` |
| Geometry/hash module (stdlib) | `scripts/anatomy_fit/ct_pelvis_window_geometry.py` |
| Blender scene setup (private external CT paths) | `scripts/anatomy_fit/ct_pelvis_review_scene_blender.py` |
| Register schema and validator | `scripts/anatomy_fit/ct_landmark_register.py` |
| Slice index generator | `scripts/anatomy_fit/ct_pelvis_slice_index.py` |
| Skeleton report generator | `scripts/anatomy_fit/ct_pelvis_skeleton_vs_source_report.py` |
| CI | `.github/workflows/pelvis-ct-blender-review.yml` |

(`audit/...` = `ORIGINAL_V1_WORK/anatomy/audit/claude_pelvis_ct_review_20261009/`.)

## Slice-to-region index

| Window | Files | Scanner S (mm) | Region |
|---|---|---|---|
| A | cvm1749f / 1752f / 1755f | -357 / -360 / -363 | UNVERIFIED |
| B | cvm1797f / 1800f / 1803f | -405 / -408 / -411 | UNVERIFIED |

The windows are 9 mm thick each, separated by an uncovered **39 mm** gap. Full SHAs are in the index files. Grid: 0.898438 mm in-plane, 3 mm slice-centre spacing.

## Skeleton versus source (from repo records, no CT)

- c004's pelvic, lumbar and hip entries are identical to a003; it differs only in 85 ribs/sternum/arm bones.
- a003 inter-HJC 166.61 mm (z -0.34 against Tannenbaum 169.3 ± 7.8); sacrum stick 103.08 mm (z -0.45).
- a003 HJC midpoint to S1 (sacrum tail) is 130.57 mm at 27.0° versus the provisional P1 S1 frame's 107 mm at 9.2°. The sacrum, L4, L5 and hip-bone sticks are low confidence, and the S1 comparison is a diagnostic only (stick end vs derived endplate centre; supine donor vs standing sources). Pelvic incidence and HJC-to-S1 distance are the posture-independent quantities.
- Seven skeleton quantities were checked for CT testability: none is computable now; the windows suffice for at most the in-plane head/cup diameters, and only if an equatorial slice is in a window.

## Method and uncertainty

- Pixel to scanner-RAS uses the header TL/TR/BR corners (column = TL→TR, row = TR→BR). Both pixel-origin conventions are carried. The envelope is a conservative linear sum (0.5 px convention + 0.5 px cell + picking allowance, default 2 px) plus ±1.5 mm in S, labelled "not a confidence interval".
- Unverified conventions: that +R/+A/+S are patient right/anterior/superior (laterality must be confirmed with an anatomical cue on the image), the PNG-to-HU calibration (never assumed), and the scanner-to-Home Gym PT world transform (not applied; the CT is shown in a separate display bay at an offset that aligns with no hip level).
- Citations used are only those already vetted in the repo (Arand 2019, Musielak 2019, Tannenbaum 2011, Gras 2015, Hasegawa 2017, StatPearls pelvic joints, the 1991 pelvic joints review). **No labelled CT atlas page could be opened here**, so a reviewer-supplied atlas figure cross-check is required before any CANDIDATE.
- Review triggers (inter-ASIS, head diameter, head separation, and so on) are deliberately wide escalations, not targets to fit.

## Additional slice ranges needed

1. **Bridge** the gap: 13 frames, candidate ids 1758…1794 (step 3), hypothesised S -366…-402 mm.
2. **Context** review of sparse frames 1701 / 1650 / 1602 to locate the iliac crest and L4/L5.
3. **Contiguous runs** sized from reviewer-identified levels with `required_contiguous_range` (indicative: acetabulum+head 18-20 frames per side, S1 to apex 35-40, symphysis 10-14, whole pelvis about 90-110).
4. **Caudal extension** toward the 1948 (S -556 mm) fiducial.

The `S = 1392 - index` mapping is proven only for the six pinned frames; check every new header.

## Blender workflow (to run on the laptop)

```
blender -b [accepted_skeleton.blend] --python scripts/anatomy_fit/ct_pelvis_review_scene_blender.py -- \
  --ct-dir <PRIVATE_DIR_OUTSIDE_REPO> --cache-dir <PRIVATE_DIR_OUTSIDE_REPO> \
  --report-out <new.json> [--save-as <new private .blend>] [--fresh] [--skip-ct]
```

It validates all 12 files against the pins before any scene change, aborts on any mismatch, creates six display-only planes with corner markers in `CT_REVIEW_PRIVATE__DISPLAY_ONLY_NOT_REGISTERED`, reads the existing skeleton non-destructively (snapshot before/after, abort on change), never packs images, and writes create-only outputs. **It has been tested only against a fake `bpy`, never in real Blender.** After viewing, a reviewer uses `ct_pelvis_window_geometry.py place` / `ct_landmark_register.py observe` to produce provenance blocks, then `ct_landmark_register.py validate --ct-dir <PRIVATE>`.

## Tests

`python3 -m unittest discover -s scripts -p 'test_ct_*.py'` → 110 tests, OK locally (about 15 s), stdlib only, synthetic CT data, fake `bpy`. Geometry results were cross-checked against PR #15's implementations on identical synthetic inputs. CI run: see the PR/branch Actions page (recorded below).

CI result: GitHub Actions run 37946213695 (workflow "Pelvis CT Blender review (stdlib only)") succeeded on the first commit; it ran all tests, the evidence drift checks and the no-tracked-CT check.

## Blockers

- Original CT unreachable from the cloud (403): real SHA re-verification, image review and the real Blender run are pending on the laptop.
- No atlas figure cross-check was possible.
- Image laterality and scanner-to-world registration unresolved.

## Stopped here

No canonical skeleton geometry was changed and no skeleton change is recommended. Findings are for independent review.
