# Bounded component orthogonal first-review completion

This completes first-pass source-index display for the previously flagged
11small components:3foot+8rib,33planes total. Additional3-plane hamate-right
main-shell control is separate:4600faces, NOT an extra small fragment or
anatomical landmark. No anatomical readiness, registration, HU calibration,
mesh correction, source unit acceptance or independent second review implied.

Continuation:18new planes at the remaining6rib centres,11250queries16.484s;
3hamate planes1875queries18.594s. Existing bounded512KB samplers checked
complete original gzip CRC/decoded lengths and exact source pins. Image
1,075,251,840decoded bytes; THORAX537,625,920; HAND_RIGHT1,075,251,840.
Fresh unchanged tests:7pixel PASS0.123s;11label PASS0.043s. No decoded volume
allocated, source image changed, label relabelled or component removed.

| Remaining diagnostic | Centre XYZ | Layer/label | Target pixels XY/XZ/YZ | Centre stored UINT16 |
| --- | --- | --- | --- | ---: |
| Rib1left2faces |370/115/1587|0/2|1/1/1|19|
| Rib3left8faces |376/116/1585|0/4|2/1/1|13430|
| Rib4left6faces A |459/115/1585|0/5|10/2/1|22|
| Rib4left6faces B |466/115/1586|0/5|1/2/4|6|
| Rib4left4faces |429/116/1585|0/5|1/2/1|25|
| Rib4left2faces |445/119/1585|0/5|1/1/1|47290|
| Hamate-right main-shell control |136/123/1070|1/3|299/312/225|1236|

All21new centre readings equal their named upstream label, consistent with
prior samples; mathematical centres remain nonlandmarks. Counts include any
same-name label inside each25x25patch, not just a mesh component. Display
stored window0..2000, nearest6x, vertical index increasing upward. Equal index
aspect is NOT metric aspect; grid/mesh correspondence remains an assumption.

Both contact sheets actually viewed. Remaining rib patches show isolated
labels in dark background or on/near saturated structured bright features,
appearing as thin sections in orthogonal planes. No convincing marker-centred
bone profile established. What produced the feature is not independently
verified; do not claim scanner text, correct/incorrect anatomy, or permission
to delete source islands. Very high stored values are not HU evidence.
Hamate control has a larger labelled region overlapping a structured grayscale
profile in all3planes, but this does not independently identify the bone,
validate its segmentation, define contact or register it to the HGPT skeleton.

All private paths are beneath existing
`C:/Users/Mark/Documents/Codex/2026-10-09/referenced-chatgpt-conversation-this-is-an/work/private-bonehub-components-20261010/`:

| Private artifact | SHA256 |
| --- | --- |
|rib-remaining-orthogonal-candidates-20261011/rib_remaining_orthogonal_grid.png|`fb5af215aac0af1a22e2af0d96fa45ff26068507eff352823e1cb653583a7ea6`|
|rib-remaining-orthogonal-candidates-20261011/manifest.json|`70c20761a8d1ff4d1fa5bc0bcf4334a0d938c98b8d58c1cd16c6f68a2f2bb13c`|
|hamate-layer1-orthogonal-control-20261011/hamate_layer1_orthogonal_grid.png|`7a625db296cfbacbb6ca5ccefde909d38e4ce1908952ab6d60c9d6d21e277544`|
|hamate-layer1-orthogonal-control-20261011/manifest.json|`e68221d80c867bc123cfaac4929ee285a8f6b83730214f2a05b9cf24cf60384b`|

Private rib script SHA256 `1d298c22894a57193ebb656ce279e7d0019d2742fa82955dc50201e35bd5d449`;
hamate script `8a2445b535aa5ec099a37ee5b724f0f71ddaa7275144828de3b4531068cdca90`.
They and all medical outputs remain outside Git. Original image/THORAX pins
are in the preceding rib ledger; HAND_RIGHT pin is
`94f70b738d823f70d4cf1f12f32cf44a7221f38ff8627a5c3c8c9ab60685d2dd`.
Mastera5ec99eb passed all3CI checks, run38097804597. Full inherited regression
remains NOT green. Regional readiness remains0READY/9PARTIAL/3BLOCKED.

Next executable action: do not regenerate completed33fragment/3control planes.
For geometry/anatomy acceptance retain qualified independent review, original
producer intensity provenance and source-registration blockers. Meanwhile
investigate primary-source metadata for an independently sourced finer-resolution
contiguous pelvic CT candidate. Verify access/licensing, subject/acquisition,
native source spacing and image/header provenance before any private acquisition;
do not substitute a new subject, guessed file sequence or atlas for the source
skeleton, and do not silently promote geometry.
