# Female CT original-pixel comparison and actual Blender diagnostic

Courtesy of the U.S. National Library of Medicine. Three-sample independent
female subject evidence only; not registered to HGPT, not replacement source
skeleton geometry and not canonical anatomical acceptance.

Official [original GE index](https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Female-Images/radiological/normalCT/index.html)
enumerated `c_vf1800.fre.Z`, `c_vf1801.fre.Z`, `c_vf1802.fre.Z` before fetching.
Published compressed sizes302736/302879/302117 matched bounded no-redirect
HTTPS responses. Each original Unix-compressed GE decoded successfully using
the laptop's Git gzip tool:527704bytes =3416header +512x512x2samples.
The2128byte official README declares that layout, but inconsistently includes
male filenames/description within its female directory. Record this discrepancy,
do not treat the prose as independent proof of subject identity or coverage.
Actual female-index object names, preserved headers and size/sample comparisons
are the evidence. Current NLM access/terms record remains in the preceding probe.

|Slice|Compressed new local SHA256|Decoded GE SHA256|
|---|---|---|
|1800|`26d2aa20af5982b9c2091411d7185a0e3c6c3d9f512c546d6e7e1e870ff55050`|`1a206df0428f263889f1949f1277a5dd3870914a2e40a6234a2b60187b0af5f3`|
|1801|`fb0636b99cd530f780823290e72374f517337ea9411c1d731a9244be282d9a06`|`205e6aad195042e998f3c260c19d11acfa0d2c49351f7dfe9c32d38d5b4ab9de`|
|1802|`3fe3e21188cedaa96ae281d104e5e2d682a363dbd94e2a9e08bc3c8a1cdcd76d`|`d2f593274b507d59003aba629bc123067211676ee9a2d74e2a9686a21a760780`|

These are newly computed local pins, not pre-existing independent immutable
checksum matches. PNG/header pins are in the preceding fine-spacing probe.
All262144samples per image,786432total, compare EXACTLY in file order between
original big-endian GE and strict decoded16bit PNG. Different counts0/0/0;
maximum differences0/0/0. Unchanged generic comparison primitive used; male
72-slice aggregate gate was NOT reused, modified or bypassed for this subject.
Header-declared-1024HU addend may therefore be applied to these3PNG arrays only.
No whole female archive calibration, scanner accuracy or anatomical validity claim.
No scaling-by16 assumption; source values preserved.

Fresh unchanged tests: raw/PNG6PASS0.280s; scanner geometry20PASS0.016s;
window geometry42run,41PASS/1SKIP28.112s. An initial mistyped test filename ran
zero tests and was rejected; correct suite above was then executed.
Private report script initially used an incorrect helper result key and failed
with KeyError; inspected actual helper contract, corrected private consumer only,
reused all existing downloads and verified successful report. No production fix.

Six HU display rasters, windows[-200,400]/[-200,1600], generated outside Git.
Every one of1572864display samples cross-checked against an independent numeric
formula and PIL-decoded raster. Unchanged strict PNG decoder and window encoder.
Contact sheet actually viewed: coherent bilateral elongated bright profiles and
posterior small profiles across3adjacent slices. Candidate pelvic-looking plane,
not independently verified bone identity, coverage, joint centres or landmarks.
No seeds/masks or geometry changes. No seven pelvic landmarks accepted.

Actual Blender5.2.1LTS factory-startup background display:6source-image planes,
2threads, Cycles1sample,1560x1100,render58.562s. Native output actually viewed.
This is a2D diagnostic layout, NOT spatial1mm stacking/3D reconstruction.
Native display omits contact-sheet text, therefore no full-contact-sheet fidelity
claim. Independent scene-reopen test1PASS0.441s verifies6quad planes, exact
file/hash bindings,512x512,Closest sampling,6external/unpacked FILE textures,
and false volume/canonical gates. Native generator's8image-datablock total
includes Blender internal images; it does NOT mean8external medical images.

Private root: `C:/Users/Mark/Documents/Codex/hgpt-private-female-ct-header-probe-20261011/`.
Raw comparison report SHA256 `c43c4e210a40bda0a68edb5335dacdcb8f8cae2b9c22759a5fec8302c37329a9`.
Official README new local SHA256 `c72dcd4a2bbbf0ff2f4cd87369056ab4bcd12e7fd2d68d5a11da9cec7236dfd1`.
Native Blend `4915fa43cfb0fd301060e7f78cddf36a9fb112465b069586668ecd66013efefd`;
native PNG `76d99a566ac00d1cca9681e6a802bff66afa4f70d8c87ed2d2d460170370d5fd`.
All original/source rasters, raw headers and private scene/scripts stay outside Git.
Only privacy-safe metadata committed. Qualified independent review still required.

Previous master478160e passed all3CI checks in run38098446797. Full regression
NOT green; regional readiness0READY/9PARTIAL/3BLOCKED remains unchanged.

Next executable action: bounded official-index scout above/below these3planes,
acquiring selected headers/original GE/PNG with exact enumerated sizes and
numeric comparisons, to establish candidate pelvic extent before any contiguous
larger acquisition. Scout gaps are NOT contiguous coverage. Then validate every
header/grid neighbour in the chosen segment and record independent identity/
landmark review needs. Never merge subjects or fit new-subject geometry to HGPT.
