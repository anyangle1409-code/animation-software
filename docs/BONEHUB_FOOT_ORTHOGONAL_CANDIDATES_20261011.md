# Private foot-component orthogonal source-index review

Follow-on to the existing header/pixel/grid ledger, not new source acquisition
or a repeat of the completed54-mesh/44-pair audits. No source or geometry edits.
Source image SHA256 `2ad6bb4129aa529e0d8d0f059694fccb4d996867cff3cfdf3c1cf1f4250fc776`;
FOOT_LEFT label SHA256 `acb38f4c4f6af83f580160ebd044d30f2908739e4670122823c13e8bfa60d964`.
Existing unchanged samplers:7pixel tests PASS0.411s;11label tests PASS0.097s.
One combined5625-query invocation checked complete image/label gzip CRC and
exact1,075,251,840 decoded bytes each, bounded512KBchunks,24.438s. No whole
decoded volume allocated. Foot layer0 explicitly selected; layer1 not conflated.

Three25x25 planes per previously recorded assumed component centre: X/Y,
X/Z and Y/Z; positive vertical index upward, nearest6x display. Stored window
0..2000 is NOT HU. Equal index scale is deliberately NOT metric aspect ratio.
The original mesh/grid scale relation remains an unaccepted assumption;
these mathematical centres are not bone or contact landmarks.

| Component diagnostic | Centre XYZ | Target label | Target pixels XY/XZ/YZ | Centre stored UINT16 |
| --- | --- | ---: | --- | ---: |
| Calcaneus small component |451/264/110|2|78/18/20|1356|
| Intermediate-cuneiform small component |439/252/105|5|40/7/3|1498|
| Talus small component |451/268/112|1|5/256/224|1434|

All nine centre reads match the target label and repeat the already recorded
centre values. Panel target pixels count the entire named label inside the
patch, NOT just the isolated mesh fragment and NOT validated3D components.
Red represents the target upstream label; cyan other labels; yellow marks
the diagnostic centre index. Three-plane contact sheet actually viewed.

Candidate visual findings: small labelled centre locations occur near or
inside structured grayscale profiles rather than empty homogeneous image
background. Intermediate-cuneiform central label is very small in X/Z and
Y/Z; talus XY few-pixel labels coexist with much larger same-name regions in
orthogonal planes. These are source-label/image review leads, not proof of
fragment validity, correct anatomical segmentation or joint contact. Do not
delete islands, merge masks, pick replacement seeds or infer HU offsets.

Private root:
`C:/Users/Mark/Documents/Codex/2026-10-09/referenced-chatgpt-conversation-this-is-an/work/private-bonehub-components-20261010/foot-orthogonal-candidates-20261011/`.
`foot_orthogonal_grid.png` SHA256 `b99760834d3d84e3aa5acec2def7625e5f7b72f9bb88f1cd142e4bff1cbae801`;
`manifest.json` SHA256 `a51e06005b5edd966e5f75ea0deb91057ec6ee305d394227e118a7dcf99902b7`.
Private diagnostic script SHA256 `1ef3e29431d5b2cb74a0d31fabc1f623bb6b1fb02f560e59b644d402c5ac3791`.
All source bytes, generated medical visualisations and experimental scripts
remain outside Git. No accepted registration, units, anatomy or HU calibration.

Hip evidence reconciliation: preserved calibrated snapshot at a3d000ce has
same-label threshold-connected regions, including ROI/source-end contacts;
678c8c03 weighted paths visit one plane. Neither supplies independently
separated head/socket surfaces and neither resolves the native marker overlap.
Do not rerun those completed computations or treat their connectivity as
clinical fusion/contact. Original four hip pixels and all branch heads retained.
Master4e564028 passed all3CI checks in run38097339835. Full historical suite
remains NOT green; regional readiness stays0READY/9PARTIAL/3BLOCKED.

Next executable action: bounded orthogonal source-index review around preserved
tiny thorax-rib candidates467/111/1585 and438/116/1586, using original THORAX
label layer0 and stored units only. Resolve background/bright-artefact concerns
without asserting scanner-text identity or deleting any component. Independent
anatomical review and producer intensity provenance still required.
