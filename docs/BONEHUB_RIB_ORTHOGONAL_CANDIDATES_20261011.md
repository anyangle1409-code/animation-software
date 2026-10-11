# Private rib-fragment orthogonal source-index review

Follow-on to the existing two axial rib patches, not repeated source acquisition
or component removal. Preserved Rib4left64-face centre467/111/1585 and8-face
centre438/116/1586, each X/Y,X/Z,Y/Z25x25 patches.3750queries,17.781s;
existing unchanged bounded samplers, layer0 in original3D THORAX segmentation.
Complete gzip CRC and decoded lengths verified: image1,075,251,840bytes;
label537,625,920bytes. No whole decoded volume allocated. Image hash before
and after reading matches `2ad6bb4129aa529e0d8d0f059694fccb4d996867cff3cfdf3c1cf1f4250fc776`;
label hash matches `786da6e14d9e57e9622ff74f49bfc0f9fae4ce99946149ddc41a73773dc04f46`.
Fresh unchanged sampler tests earlier in this continuation:7pixel+11label PASS.

Stored UINT16 display0..2000 is NOT HU, equal index scale is NOT metric aspect.
Nearest6x display, increasing vertical index upward; yellow centre, target
upstream label5 red. Matching named labels is not independent anatomical truth.
Six-plane contact sheet actually viewed; centres repeat stored29 and11.

| Diagnostic centre | Target pixels XY/XZ/YZ | Stored values under target XY/XZ/YZ |
| --- | --- | --- |
|467/111/1585|10/4/4|12..45 /28..39 /29..45|
|438/116/1586|1/2/1|11 /11..25 /11|

Candidate visual observations: isolated tiny labelled samples occur in dark
background, near a high-contrast structured bright feature. Orthogonal planes
show this feature as thin, short stripe-like sections; neither marker-centred
patch provides convincing bone-profile evidence. This corroborates an unresolved
source-label/image concern, NOT proven segmentation error, accepted bone absence,
scanner-text identification, intensity calibration or authority to delete a mesh.
Patch counts include any same-name label in the window, not only mesh fragments.
Retain all original components, labels, source bytes and coordinate assumptions.

Private root:
`C:/Users/Mark/Documents/Codex/2026-10-09/referenced-chatgpt-conversation-this-is-an/work/private-bonehub-components-20261010/rib-orthogonal-candidates-20261011/`.
`rib_orthogonal_grid.png` SHA256 `ac4234237f656c540ba8f39cc300c1a93c914ec79c8095b9384111063969571e`;
`manifest.json` SHA256 `4d6e7a3b4ecf1762862ba858daac0f999b334b04a6a40831ab57464e3e29dcde`.
Private script SHA256 `ca9862f6e0c8ebe91611bf26eb404b0a399dc4a9fc4a4d2e10b11d0246e70a74`.
Medical data, visualisations and experimental scripts remain outside Git.
No anatomy, registration, HU, contact, physiological or canonical gate advanced.

Next: finish orthogonal candidate review for the remaining previously pinned
rib1left/rib3left and right-hamate component centres, respecting hand layer1.
Do not repeat foot/rib4 views or infer valid/invalid anatomy from named masks.
Qualified independent anatomical review and producer intensity provenance remain
required for any acceptance. Full inherited regression remains NOT green.
