# Physical slice-to-region index (pinned frames) and additional ranges needed

All region statuses are **UNVERIFIED**; no image was reviewed in the cloud session.

| Win | File | Scanner S (mm) | Slab S range (mm) | Pixel (mm) | Thick (mm) | PNG SHA-256 | Header SHA-256 | Region |
|---|---|---|---|---|---|---|---|---|
| A | cvm1749f.png | -357 | -358.5 to -355.5 | 0.898438 | 3 | `66eb930264a574dda410df6ed04d21bb2fe3a7a95de421f80344dbc42736f734` | `d22d9df35f00a3c566ebacd18fadb84c69ce81a4f442f7f03b6ac71608c3e672` | UNVERIFIED |
| A | cvm1752f.png | -360 | -361.5 to -358.5 | 0.898438 | 3 | `899687e75c0d57a97c64d498330c60b2fb61bb836e55ebc4f6202234c9939c73` | `3d9c48641c45c2e1cd035eb11a4b83bee42240ef94f26bb479f8fd1944a72c38` | UNVERIFIED |
| A | cvm1755f.png | -363 | -364.5 to -361.5 | 0.898438 | 3 | `5a9f46fd7b1334d72c29e98e9e6384666414aa2c7b2b85e0da3029dac096d643` | `f9ecacadcc956bbe26c27be5b1dc201e3977e1e0c695af6d9d51a935f1610012` | UNVERIFIED |
| B | cvm1797f.png | -405 | -406.5 to -403.5 | 0.898438 | 3 | `7ba206fd8110c66334dff8387d1df839249aa778c421b013fb07fc5b43ac2072` | `1feadc69adf294a79fa66dd474e613256be0fd57572e7eea7e019fa2ac52b8b4` | UNVERIFIED |
| B | cvm1800f.png | -408 | -409.5 to -406.5 | 0.898438 | 3 | `57371cc19aa7cc468f5cc8c12ef01d0d0c740e0a0da1d5e93f238dda09f92d69` | `e159990a7bb612e904ca98ee0972510242ea2ec69e77bcb245174c9743486e0a` | UNVERIFIED |
| B | cvm1803f.png | -411 | -412.5 to -409.5 | 0.898438 | 3 | `73ede100af03ce8fa6ae2b190326aa539b999e4ed4f69a89fc6a29771ecb19a5` | `f5d4e555c90f07ae51929ebbdfa72b82954398471860bc6aa3cdca72c00d91ce` | UNVERIFIED |

Uncovered gap between windows: **39 mm**.

Each window is 9 mm of axial section. Only in-plane observations at a single level are possible (for example an equatorial cross-section circle, if a reviewer finds one). Surfaces, sphere centres in S, endplate orientation and any length along S cannot be obtained, and nothing here is a 3D pelvis.

## Additional ranges needed

- Tier A bridge: 13 frames, candidate ids 1758..1794 (step 3), hypothesised S -366..-402 mm. close the 39 mm gap so a reviewer can follow structures between windows A and B.
- Tier B context: ids 1701, 1650, 1602, hypothesised S -309, -258, -210 mm. find iliac crest, L4/L5 and sacral levels so contiguous runs can be sized from real levels.
- Tier C runs: after a reviewer names iliac-crest-top S and ischial-tuberosity/pubic-bottom S, size the run with required_contiguous_range(levels, margin_mm=6) in ct_pelvis_window_geometry.py. Indicative 3 mm frame counts: whole pelvis surface iliac crest to ischium about 90-110 (pelvic height + ischium; sized from real levels); each acetabulum and head 18-20 per side (about 53 mm); S1 to sacral apex about 35-40; pubic symphysis 10-14.
- Tier D: extend toward the 1948 (S = -556 mm) fiducial named by the PR #15 scout, only after its header is checked.

The id-to-S mapping S = 1392 - index is a hypothesis proven only for the six pinned frames; check each header before use.
