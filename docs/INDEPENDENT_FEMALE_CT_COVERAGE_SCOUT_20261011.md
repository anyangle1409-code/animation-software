# Independent female CT coverage scout and coordinate break

Courtesy of the U.S. National Library of Medicine. Noncontiguous exploratory
source evidence only; no complete pelvic volume or canonical anatomy accepted.
Continues the raw/Blender checkpoint without repeating its three renders.

Enumerated official [GE](https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Female-Images/radiological/normalCT/index.html),
[PNG](https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Female-Images/PNG_format/radiological/normalCT/index.html)
and [header](https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Female-Images/PNG_format/radiological/normalCTHeaders/index.html)
objects1700/1900/2000 before bounded no-redirect acquisition. Published sizes
matched all9objects. Original GE527704bytes each; all786432additional pixels
match their respective PNG arrays exactly in file order,zero differences.
Each privacy-safe header declares-1024HU addend; these3arrays calibrated only.
All6window displays cross-checked numerically after PIL decoding and actually
viewed together. No raw headers/patient identifiers emitted to Git or logs.

|Source|Header/PNG/compressed GE bytes|S mm|Normal RAS|
|---|---|---|---|
|1700|16483/263077/298710|-737|0,0,+1|
|1900|16485/252272/288528|-937|0,0,+1|
|2000|16484/243307/272931|-96|0,0,-1|

All headers declare512x512,0.9375mm X/Y,1mm thickness/nominal spacing.
2000 coordinate reset and reversed normal demonstrate incompatibility with
a single assumed filename-derived scanner grid. Exact acquisition boundary,
scanner explanation and cross-group transform have NOT been established.
Do not infer S=-1037 for2000, repair/reverse normals or merge these grids.
The gap1700->1900 is200mm, NOT measured1mm neighbour continuity.

Viewed1700: central round bright profile with posterior bright structure,
body abdomen-like contour and peripheral upper-limb-looking profiles.
Viewed1900: broad bilateral body contour, bilateral rounded external bright
profiles and thinner medial profiles; candidate lower-pelvic/proximal-limb plane.
Viewed2000: separate bilateral rounded soft-tissue contours with small bright
rings; candidate limb-shaft plane, separate scanner frame. These are cautious
first-review observations, NOT verified named bones, accepted coverage endpoints,
landmarks, segmentation seeds or registration. Qualified second review required.

Private root `C:/Users/Mark/Documents/Codex/hgpt-private-female-ct-coverage-scout-20261011/`.
Safe report SHA256 `7ef513f54bbc7a4caa06c23a0603d03ef8fd5a873aa18e0fa30af1ddf82b4371`;
contact sheet `ea8c91a9115ed7c6d09b3dad61875daf4ba156fc6879766cf076129142930998`.
Report contains all9new local object pins,3decoded GE pins,6window pins and
privacy-filtered geometry. New local pins are NOT independent pre-existing SHA matches.

Header SHA2561700 `7b2d2d378147a7634eb34b8c9d8c1a321aee3952c4459fb7d4bd1b797a26d627`,
1900 `f9a7a560705b878de317119bc2bb4bb28e7ab7515b328591bc932a2b69aea430`,
2000 `290cf6f24a9cd8f8cbc0a48f68db7305d84e7501b08143b26e01e7f42bfc28b9`.
PNG SHA2561700 `54835e0c0b0679086ac378e3acc9f35ce6601a386efd2ffa4020a2c6d8de3bb9`,
1900 `c7a60fdcabede3c364aafdc6b211386cf089239fb2736079b6cf2cad86fdefc1`,
2000 `7e3af8eb9161dc1f1f22bf65c65b7007464975c5cd36550f8a6a372b5f739372`.
Decoded GE SHA2561700 `2b8f2492c0eec8e6821f23b7d1f2c133042781606cddf00c14a44ca3d6033063`,
1900 `3b9c195b204086e492b4d0d2e05014033ee717bbc76ac9fe2bc46fd0c2c0ccfa`,
2000 `8ec18c0e5e5626a10e6f53daf6b12500f357a89eab70d9afca781bf24b6bec1e`.

Tests earlier in same execution: unchanged raw6PASS, scanner20PASS,
window41PASS/1SKIP and actual Blender scene-reopen1PASS. Scout per-object
exact length/decompression/full-array comparison/numeric display assertions PASS.
No new production code or test bypass. Prior35115558 CI run38099041113 started;
do not report latest checks green until verified. Full regression remains NOT green.

Next: enumerate and privately verify all headers1700..1900 using bounded
fetches and reused1800..1802/1700/1900 bytes. Require exact published size,
privacy-safe header parsing and every adjacent-grid check; stop/split on any
incompatibility. Only then choose a contiguous candidate image acquisition within
one verified scanner group. Source identity, pixel-centre convention, independent
bone/landmark review and HGPT registration remain separate unfulfilled gates.
