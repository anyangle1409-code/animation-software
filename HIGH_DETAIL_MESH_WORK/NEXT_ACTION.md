# Next action: V10 hand anatomy visual review

V8 is the accepted body/knee geometry baseline. V9 is rejected/experimental.
V10 is a separate, mechanically validated hand-retopology review candidate
derived from V8. None is promoted to production.

Show the matched V8/V10 open-hand, equipment-free closed-fist, and exercise
comparison boards in `renders_v10_hand_retopology/`. The full-size PNGs are
there too. Ask for visual acceptance of V10 anatomy before any curl-grip refit.
The remaining visible issues are faceted fingertips/joint bands, a thumb-web
seam in some views, and a segmented wrist transition.

If V10 is rejected, keep all candidates and make V11 candidate-side anatomy
changes only. Preserve the 682 protected floor-contact original vertices,
V8's non-hand geometry, frozen `hgpt_canonical_v3` hierarchy, runtime
`614033b`, UV/weight compatibility, equipment and exercises. Re-run the
same guard suite and matched pose reviews. Do not touch production files,
`bundled.ts`, references or grip mechanics.
