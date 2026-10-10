# Home Gym PT — private original CT candidate correction/rejection capture

**10 October 2026 · Built on draft PRs #19–#22 · NOT accepted anatomy**  
**Isolated branch:** `codex/ct-private-anatomy-annotation-20261010`

## New capability without Claude tokens or extra software

The existing one-command, SHA-verified scanner CT review now creates **two private browser files for each of the five original candidate source planes**:

- `cvm####f_source_review.svg` — original three-slice, two-window scanner viewer with the prior unverified points.
- `cvm####f_tentative_review.html` — the **new completely offline correction/rejection capture** using the same six windowed image panels and **unchanged original point locations**.

All 10 proposed points across the 5 original candidate planes are now reviewable in this way. The HTML uses embedded original-source-derived PNG windows (6 per plane) and JavaScript written in this repository. It has a restrictive Content Security Policy, no network calls, no external packages, no paid API and no third-party viewer.

**Run on Windows without changing Claude's production files:**

```powershell
git fetch origin
git worktree add --detach ../HGPT-CT-Review origin/codex/ct-private-anatomy-annotation-20261010
cd ../HGPT-CT-Review
./start_private_ct_review.cmd
```

The original scans remain privately cached in `%USERPROFILE%\HomeGymPT_Private_Original_CT_Review\original_NLM_CT_sources`. The Start Here page is `%USERPROFILE%\HomeGymPT_Private_Original_CT_Review\PRIVATE_CT_VIEW\START_HERE_private_CT_review.html`. It now links both the static review and the correction/rejection capture for each source.

The separate one-click Blender review still works: `start_private_ct_blender_review.cmd`. It is an optional protected viewer only and cannot establish the scanner-to-model registration or modify the accepted skeleton.

## Source-preserving correction workflow

1. Open the **private tentative correction/rejection form** for the desired original CT plane. Select one of the exact immutable source-pinned candidate IDs.
2. Select **Reject original hypothesis** if the old pixel clearly is not useful, or **Tentative pixel** and click the **centre** original scan image to record a substitute. Keep original points visible; replacements are overlaid in cyan/yellow and are explicitly NOT called bones. Add notes about source anatomy and ambiguity; do not write unsupported approval.
3. Enter an alias (2–32 letters/digits/underscore/dash) and select **Export private tentative JSON**. The browser downloads a local `cvm####f_tentative_pixels.json`; nothing is uploaded.
4. Independently run the **original scanner HU recheck** against your local cache. For example, using Windows PowerShell in the isolated review worktree:

```powershell
py -3 scripts/anatomy_fit/nlm_ct_private_annotation_capture.py `
  --private-export "$env:USERPROFILE\Downloads\cvm1873f_tentative_pixels.json" `
  --ct-dir "$env:USERPROFILE\HomeGymPT_Private_Original_CT_Review\original_NLM_CT_sources" `
  --bundle ORIGINAL_V1_WORK/anatomy/audit/nlm_pelvic_ct_full_series_candidate_bundle_20261009.json `
  --calibration ORIGINAL_V1_WORK/anatomy/audit/nlm_pelvic_ct_full_series_hu_calibration_20261009.json `
  --review ORIGINAL_V1_WORK/anatomy/audit/nlm_pelvic_ct_full_series_candidate_review_20261009.json `
  --out "$env:USERPROFILE\HomeGymPT_Private_Original_CT_Review\PRIVATE_CT_VIEW\cvm1873f_tentative_checked_v1.json"
```

This step checks the saved original source frame/header SHA identities and geometric source pins, rejects moved/reordered original points, and **recalculates tentative Hounsfield units from the untouched original 16-bit scanner pixels** rather than mistaking the rewindowed 8-bit preview for quantitative CT. A mismatched file or unsupported anatomy approval flag fails closed. Existing outputs are never overwritten.

## Limits — no false anatomical certification

This workflow records **reviewer-supplied hypotheses**, not a verified femoral-head or acetabular cortex. A bright pixel, local point correction or HU measurement cannot by itself establish bone identity, 3D boundaries, articular gaps or the accepted rig coordinate transform. The recorded alias is not evidence of expertise. The independent anatomical review and a matching 3D surface are still needed.

Nothing is merged into the canonical skeleton or first-party production character. The previous **0/7 required true pelvic osseous landmarks accepted** and **0 READY / 9 PARTIAL / 3 BLOCKED** remain unchanged. Original a003, c001–c004 and Claude/Work commits are preserved; c005 remains unapproved.

**Verification:** the new GitHub Actions workflow `.github/workflows/nlm-ct-private-annotation.yml` runs first-party cross-branch original-source tests, malicious/tampered annotation tests, and independent recovery of original and corrected HU from real NLM PNG and GE header bytes. No source image, browser review or manually supplied annotations are uploaded as GitHub artifacts.


## Source-pinned three-slice outline capture (additional, tentative only)

The same local Start Here page now links **PRIVATE tentative 3-slice contour drawing** views. Each self-contained offline HTML displays the three adjacent original CT images in both viewing windows. A reviewer can choose an **unverified** candidate structure, click outline points on one scan, undo a point, discard a draft, finish a polygon, switch to another source plane, and export private JSON.

These outlines are provisional 2D human review hypotheses, **not certified contours, named bone surfaces or a 3D segmentation**. One centre plane and two adjacent 3-mm slices are insufficient for a complete pelvic bone reconstruction. Original source images are never published to Git, and the local HTML has no network requests.

The exported local file is named e.g. cvm1873f_tentative_contours.json. Each closed outline must contain 3–240 unique original source pixels and a prior unverified named region label; maximum 50 outlines. The first-party validator rejects bow-tie/self-crossing geometry, altered/reordered scanner SHA pins, unexpected labels, forged bone acceptance, changed acquisition groups, out-of-range pixels or invalid aliases.

**Run the original-source physical geometry recheck** from the isolated worktree, replacing paths with your private folder as needed:

    py -3 scripts/anatomy_fit/nlm_ct_private_contour_capture.py --private-export "%USERPROFILE%\Downloads\cvm1873f_tentative_contours.json" --ct-dir "%USERPROFILE%\HomeGymPT_Private_Original_CT_Review\original_NLM_CT_sources" --bundle ORIGINAL_V1_WORK/anatomy/audit/nlm_pelvic_ct_full_series_candidate_bundle_20261009.json --calibration ORIGINAL_V1_WORK/anatomy/audit/nlm_pelvic_ct_full_series_hu_calibration_20261009.json --original-plate-sidecar "%USERPROFILE%\HomeGymPT_Private_Original_CT_Review\PRIVATE_CT_VIEW\cvm1873f_source_review.json" --out "%USERPROFILE%\HomeGymPT_Private_Original_CT_Review\PRIVATE_CT_VIEW\cvm1873f_contour_checked_v1.json"

This computes polygon area **in scanner mm²** from the original GE field of view and unchanged 16-bit source vertex HU. Scanner physical area is an objective property of the reviewer-drawn pixel shape, **not proof the shape is a genuine cortical boundary**. Absolute HGPT registration and pixel-origin convention remain unresolved. Only an independent anatomical inspection across sufficient slices could potentially upgrade confidence.

**Verified against real original CT sources:** https://github.com/anyangle1409-code/animation-software/actions/runs/38053484090 — both CI jobs passed, including a source-pinned scanner area test. No medical image upload or source-derived production model. The seven true pelvic landmarks remain **0 accepted** and canonical regional freeze still **0 READY / 9 PARTIAL / 3 BLOCKED**.
