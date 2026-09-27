# V15f ring_L protected/anchor blocker diagnosis

- Candidate: `checkpoints\v15_manual\v15f_deep_hand_rebuild_checkpoint_004.blend`
- Compared with: `checkpoints\v15_manual\v15f_deep_hand_rebuild_checkpoint_003.blend`
- Operation: read-only; no candidate geometry was saved

## Classification summary

- owned: 1301
- editable core: 904
- direct protected: 7
- patch boundary: 0
- anchor buffer only: 390
- graph adjacent to protected: 62
- tracked: 1301
- source: 181
- ring bone weight owned: 1301

### >35-degree problem edges

- face adjacent to anchor only: 2
- face adjacent to direct protected: 7
- fully editable core: 7
- mixed owned: 1
- touches anchor only: 102
- touches direct protected: 9

## Ten required answers

1. The visible segmentation aligns with the listed >35-degree same-owner edges and their two adjacent faces, especially cross-band/diagonal bands and the largest radius-profile discontinuities. Exact IDs are in problem_edges and profile_anomalies.
2. 9 problem edges directly touch a protected contact vertex; another 7 have a protected vertex in an adjacent face.
3. 102 problem edges touch only the conservative anchor/boundary envelope and 2 are face-adjacent to it without touching a direct protected vertex. 7 are fully inside the editable core.
4. Checkpoint 004 moved 475 tracked ring_L vertices (max 0.316648 mm), all outside the fixed direct/anchor sets. Its fairing improved aggregate dihedral ratios but could only change support next to the fixed bands, so the dominant silhouette/face-flow bands remained.
5. Primary causes are inherited irregular face/edge flow plus uneven longitudinal spacing and cross-section transitions. Vertex position contributes at movable support points. Bind-pose reproduction and exact original weight rows rule out bone weighting as the primary cause. Smooth shading is already active, so normals/shading cannot explain or legally hide the geometry defect.
6. Legal degrees of freedom are: move non-protected ring_L core vertices within existing audit limits; add minimal ring_L vertices with normalized transferred weights/UVs and zero new source/tracking IDs; and reconstruct edges/faces while retaining every original tracked/source vertex, all protected coordinates/weights, hierarchy and other body geometry.
7. Yes in principle: fixed protected coordinates still permit topology rerouting and new support geometry between them, plus movement of non-protected neighbours. The result must prove equal contact and pass the existing numeric and visual gates.
8. Yes. The accepted guards require protected source vertices and their coordinates/skin rows to remain exact; they do not require the same incident triangulation. Original tracked vertices cannot be deleted, but edges/faces around fixed anchors may be reconstructed and revalidated.
9. A constrained topology bridge/reroute is the strongest remaining legal hypothesis because it directly changes the face flow that checkpoint 004 could not affect. It should use fixed original vertices as boundary points and add only sparse internal support where needed.
10. The 682 direct protected classifications are evidence-backed by the reviewed push-up floor-contact guard and are genuinely required. The four-edge anchor envelope is broader than that accepted invariant: it is a conservative transition rule created by V15 preparation. Its coordinates remain fixed for this attempt, but topology-only reconstruction around those vertices is legal and testable without weakening contact protection.

## Ranked legal strategies

### 1. fixed-anchor face-flow reroute

- Editable region: ring_L faces incident to the strongest PIP/DIP/cross-band problem clusters
- Protected boundary: all direct protected, patch-boundary and anchor-buffer vertex coordinates remain bit-identical
- May move: only non-protected ring_L core vertices in the bounded cluster
- Must remain identical: all protected coordinates/weights, every original source/tracking ID, all other digits/body, rig and mechanics
- Permitted topology: rotate/dissolve/recreate local faces and add sparse internal support vertices; never delete an original vertex
- Expected visual effect: replace transverse segmented face bands with longitudinal/circumferential flow while retaining joint volume and taper
- Numeric risks: new >50/>100 folds, degenerate or nonmanifold faces, changed surface fingerprint, weight normalization on new vertices
- Rollback: start from checkpoint 004; save a uniquely numbered trial/checkpoint; preserve rejection evidence

### 2. fixed-boundary patch bridge

- Editable region: one narrow problem band between fixed protected/anchor islands
- Protected boundary: same fixed coordinates and exact skin rows
- May move: new internal vertices and adjacent legal core vertices only
- Must remain identical: all original protected/source/tracked vertices and non-ring_L geometry
- Permitted topology: remove only faces, bridge the retained boundary with regular longitudinal/circumferential quads, triangulate for audit
- Expected visual effect: add missing circumferential support and regularise a locally under-supported band
- Numeric risks: tracking/UV transfer errors, boundary/nonmanifold defects, excessive density, new folds
- Rollback: independent trial from checkpoint 004

### 3. constrained longitudinal redistribution

- Editable region: fully editable core stations adjacent to the strongest fixed bands
- Protected boundary: direct protected plus complete anchor envelope fixed
- May move: existing core vertices only, with sub-millimetre capped movement and per-station volume preservation
- Must remain identical: topology, protected/anchor positions, weights and all unrelated surfaces
- Permitted topology: none beyond optional safe edge rotation; position solve targets spacing/profile rather than generic smoothing
- Expected visual effect: reduce radius jumps and shaft lumps without changing contacts
- Numeric risks: repeat of checkpoint 004's visually insufficient result; taper loss
- Rollback: independent trial from checkpoint 004

## Unattended trial outcome

Three materially distinct legal approaches were completed from checkpoint 004.

1. **Fixed-anchor face-flow reroute — rejected.** Twenty-four non-overlapping
   anchor-buffer triangle diagonals were rotated without moving any vertex.
   The nonplanar quads produced 24 new ring-left folds over 100 degrees. The
   opposite rotation setting and a face-normal recalculation reproduced the
   same result, proving this was geometric rather than a clockwise/tool flag.
2. **Fixed-boundary support bridge — rejected.** Forty-six new support vertices
   were added to 46 anchor-adjacent cross/diagonal faces; all original vertices
   remained exact. General invariants passed, but ring-left gained five severe
   folds and its >35 and >50 sharp-length ratios worsened.
3. **Profile-driven core redistribution — numeric PASS, visual FAIL.** Five
   hundred eight editable-core vertices moved at most 0.332416 mm in the four
   measured profile-anomaly windows. Anchors, protected contacts, weights and
   all other geometry stayed exact. Total >100 folds remained 3, ring-left
   >100 remained 0, >35 ratio was 0.0433915625 and >50 was 0.0162513778. The
   matched four-view board still showed no clear anatomical improvement over
   V13e; the segmented/faceted shaft and joint flow remained.

Checkpoint 004 remains the active candidate state. No rejected trial was copied
over it and no checkpoint 005 was created.

## Exact blocker and smallest interface needing reconsideration

Of 128 ring-left edges over 35 degrees, 111 (86.7%) either touch or share a face
with the direct/anchor protection envelope; 104 (81.25%) are anchor-buffer-only
or face-adjacent to that buffer, while just 16 (12.5%) are direct-contact or
face-adjacent to direct contact. Only seven (5.47%) are fully editable core.

The accepted 682-vertex direct push-up contact set remains genuinely frozen and
does not need reconsideration. The smallest blocked interface is the **four-edge
V15 anchor-buffer position freeze around those direct contacts**. It is a
conservative modelling transition, not the accepted contact set itself. A
visually material repair now requires a separately approved experiment that may
reposition anchor-buffer-only vertices while retaining every direct protected
contact coordinate and skin row exactly, followed by the complete push-up and
hand validation. That experiment is outside the current unattended authority,
so geometry work stops here.

