Read CURRENT_STATE.md and RIG_55_BASELINE.md first.

V6 knee seam remains the latest reviewed geometry baseline. The canonical runtime baseline is now c2372c1 / 55 bones / hgpt_canonical_v2.

Next autonomous modelling order:
1. retopologize the still-open medial-knee strips into connected anatomical loops and reshape the pointed overhang;
2. model realistic finger/thumb/palm/wrist geometry on the contact-safe topology;
3. refine skin materials;
4. if time remains, prepare shoulder/back/chest/armpit topology/geometry for the confirmed scapula structure.

Use START_CANDIDATE.bat <version> to create a fresh working copy. After editing/exporting, use FINISH_CANDIDATE.bat <version> <task>. Validation must run against validation_55 prepared from c2372c1.

Do not finalise hand weights, enable scapular rhythm, or promote production assets. Final scapula deform weighting requires an explicit character-asset binding pass and fresh neutral-equivalence proof.
