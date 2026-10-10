# Home Gym PT — ZERO-CLAUDE laptop original CT review handoff
**10 October 2026 · Noncanonical source-validation aid · independent branch `codex/one-command-private-ct-laptop-20261010`**

## Purpose

Give the owner the **next useful visual anatomical review** on their own laptop without using any Claude or ChatGPT Work usage. Everything required is a first-party Python 3 standard-library script in this repository, with one launcher. **No Blender, pip package, cloud model, API key, or paid service is needed to view the original CT evidence.** Blender is only required later when real osseous boundaries are identified and reviewed.

This deliberately does **not** modify the skeleton, model, rig, meshes, exercise solver or accepted source records. All displayed candidate points are from the original audited hypotheses, with low HU values and invalidated anatomical certainty preserved.

## Windows laptop: preserve Claude's current branch and local Blender work

From a terminal inside the **existing `animation-software` repository**, enter:

```powershell
git fetch origin
git worktree add --detach ../HGPT-CT-Review origin/codex/one-command-private-ct-laptop-20261010
cd ../HGPT-CT-Review
./start_private_ct_review.cmd
```

You may also **double-click `start_private_ct_review.cmd`** in the new `HGPT-CT-Review` folder. The launcher searches for Python 3 (prefers `py -3`), runs the verified workflow and opens the private review index in the default browser.

**Important:** This creates a *separate worktree*. Do not switch branches, stash, reset, rebase, discard or update Claude's active Blender files to view these results. The tool writes scanned medical-source files and derivative images only inside the owner's user home directory, OUTSIDE all Git worktrees.

### macOS/Linux equivalent

After `git fetch origin`, use:

```sh
git worktree add --detach ../HGPT-CT-Review origin/codex/one-command-private-ct-laptop-20261010
cd ../HGPT-CT-Review
sh start_private_ct_review.sh
```

Alternatively, directly inside the isolated worktree:

```sh
python3 scripts/anatomy_fit/nlm_ct_laptop_review.py --open
```

## Exactly what you get

The default command retrieves **15 exact original Visible Human Male CT 16-bit PNG frames and 15 original scanner GE headers**, pinned against the trusted manifest with matching SHA-256 checks and original byte counts. It covers **ALL 10 previously proposed image point hypotheses** from five distinct centre source planes (each with a preceding and following group-matched slice).

| Original centre scan | Existing hypothesis point regions | Original source acquisition group | Is it an accepted anatomical bone? |
|---|---|---|---|
| `cvm1764f` | Two iliac-blade points | Group 1 | No |
| `cvm1794f` | Central sacral point | Group 1 | No |
| `cvm1824f` | Two further iliac-blade points | Group 1 | No |
| `cvm1873f` | Left/right femoral-head and acetabular hypotheses | Group 2 | No |
| `cvm1903f` | Central pubic-region point | Group 2 | No |

Each centre source is displayed together with its adjacent originals in two independently windowed views: **soft-tissue (−200 to 400 HU)** and **bone review (−200 to 1600 HU)**. Four hip hypothesis pixels in `cvm1873f` are colour-ringed, but rings and colours are **annotation only**.

The local index opens from:

- **Windows:** `%USERPROFILE%\HomeGymPT_Private_Original_CT_Review\PRIVATE_CT_VIEW\START_HERE_private_CT_review.html`
- **macOS/Linux:** `~/HomeGymPT_Private_Original_CT_Review/PRIVATE_CT_VIEW/START_HERE_private_CT_review.html`

Double-click that **Start Here** HTML file any time afterward without rerunning the downloader. The five `*.svg` files are embedded-window image plates for zoomable browser inspection; each has a `*.json` companion with exact source coordinates, original measured HU and **non-acceptance** flags.

### Source and privacy safety

- Pinned original PNG/header pairs are downloaded **directly from the official NLM URLs**, with hash and length checked BEFORE writing. Redirects and content drift cause a hard failure.
- Existing exact source files may be reused after verifying SHA-256; mismatched existing files are NOT silently overwritten or repaired.
- Generated images and source bytes are never checked into Git, uploaded to GitHub Actions artifacts, or added to production assets.
- All output directories must resolve outside every currently checked-out repository worktree; never copy the scan bytes or visualized plates into the project.
- The first run creates the private `PRIVATE_CT_VIEW` directory. Running the generator again into a nonempty output directory fails closed to avoid deleting prior evidence; **open the existing Start Here HTML file instead** or select a new `--workspace`.
- None of this uses Claude tokens, your personal NLM login, Blender plugins or third-party Python packages. It requires a working internet connection only to retrieve the original publicly available data.

## What to inspect without spending Claude usage

Open `cvm1873f_source_review.svg` first. Check the actual left/right source CT against the four marked proposed head/socket positions; their measured HU values are **291, 305, 438 and 510 HU** respectively. At lower HU thresholds a continuous **intensity-only** path exists within the axial plane for each proposed pair. That must not be interpreted as real hip-bone fusion or a validated joint contact. Assess the underlying anatomy, neighbouring slices and clear cortical interfaces manually.

Then open the group-1 iliac/sacrum and group-2 pubic views. Seven of ten original candidate centres fail 300 HU; don't assume they point to identifiable bone, and don't auto-snap them to a neighbouring bright pixel. Keep both possible CT pixel/FOV centre-origin conventions marked unverified. No scanner-to-HGPT world registration has been established.

### What Claude should NOT repeat later

Source downloading, scanner-header/PNG SHA matching, 72-original-slice HU addend verification, 37-vs-35 group separation, original candidate point HU screens, simple HU-region connectivity, bilateral HU shortest intensity routes, and all ten private scan review plates have **already been automated and validated**.

Only use Claude or Blender assistance later for the actual **expert anatomical interpretation, distinct named bone surface identification, true pelvic landmark verification, independent scanner-to-canonical registration, pose/joint verification, and remaining skeleton regions**. The same geometry still must not be modified until independently verified.

## Verifiable development references

- Stacked draft PR #19: https://github.com/anyangle1409-code/animation-software/pull/19
- Stacked draft PR #20: https://github.com/anyangle1409-code/animation-software/pull/20
- Independent one-command laptop PR: opened after verified CI.
- Main script: `scripts/anatomy_fit/nlm_ct_laptop_review.py`
- Five individual source review plates: `scripts/anatomy_fit/nlm_ct_private_slice_review_plate.py`
- Complete first-party test suite: `scripts/test_nlm_ct_laptop_review.py`

### Anatomical stop line

Formal status remains **0 READY / 9 PARTIAL / 3 BLOCKED**. **0/7 required pelvic true bony landmarks independently accepted**. No canonical skeleton freeze or production asset promotion permitted, and original a003, c001–c004 are unchanged; c005 is not approved.
