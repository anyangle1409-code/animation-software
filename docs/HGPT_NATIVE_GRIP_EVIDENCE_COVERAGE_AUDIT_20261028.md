# Native grip evidence coverage and solver-guard audit — 2026-10-28

## Scope

This read-only diagnostic consumes only each hash-pinned `diagnosis.json` from native Blender run `39937882229`. It does not open a `.blend`, pose a model or change any source. It separates three questions that the earlier combined summary could blur:

1. Which authored runtime suffixes were actually trialled?
2. Which trials passed the project's `pairs <= 5` solver guard and therefore reached the hand-collapse measurement?
3. Was a grip accepted? **No.** The solver ended with `no thumb placement within the pair limit` for every model.

The value five is a pinned project solver guard. It is not an anatomical limit, population ROM statistic, contact criterion or passing-grip threshold. No hand-collapse acceptance threshold exists in this evidence.

## Evidence contract

- Source run: `39937882229`.
- W8 artifact `12495910312`, ZIP SHA256 `3be4322ba67da8b3827c96c0afdb58ffa8adb998cf8d1814aab0978a9e68d63e`, pinned `diagnosis.json` SHA256 `b1afed85ffbf247604f2fd2afce6a9e8a0b3fe0d69ab93f943e8d49d36ec5923`.
- V14 artifact `12494932817`, ZIP SHA256 `5f11a9441cf5bb1d29ba3fae72c945f59c9109a26023cea15508d3310cb774e0`, pinned `diagnosis.json` SHA256 `2f49c51a780acf3834e35ef9e9a122515d16c8bed3e069a71282cd6983dd9321`.
- R120 artifact `12495970648`, ZIP SHA256 `cf26902334a90cb3928821d797fcc88e27340a7837911a0e080b6973b5017a2f`, pinned `diagnosis.json` SHA256 `399cca503451fea4f84812e97675bdcc8c57c26aaa9c2a9c6c18b0ad2fb68e5e`.

The parser fails closed on wrong source/preservation/approval metadata, unexpected solver outcome, missing or unknown suffixes, nonfinite Euler values, boolean or negative counts, and any inconsistency between the pair guard and whether collapse was measured. Output paths are prevented from aliasing or nesting inside evidence inputs, including hardlinks and symlinks to members of an extracted evidence tree. Atomic replacement prevents output writes from following and truncating a linked destination introduced after validation.

## Verified cloud result

[Run 40751934405](https://github.com/anyangle1409-code/animation-software/actions/runs/40751934405) at published commit `418c9098b751d3bb2347384f5a8e54eb8dc7bb5b` completed SUCCESS 7/7. The localization job ran 288/288 tests and generated the audit from all three pinned diagnosis members.

| Model | Trials | Authored suffix counts | Reached pair guard | Collapse counts | Solver result |
|---|---:|---|---:|---|---|
| W8 | 263 | `l=263`, `r=0` | 1 | `24` | no placement within pair limit |
| V14 | 263 | `l=263`, `r=0` | 1 | `24` | no placement within pair limit |
| R120 | 263 | `l=263`, `r=0` | 3 | `23, 23, 24` | no placement within pair limit |

The only W8/V14 guard-reaching trial used thumb Euler `[0, 0.5235987901687622, 0]` radians and reported five pairs. R120 additionally reached the guard at `[0.2617993950843811, -0.7853981852531433, 0.2617993950843811]` and `[0, -0.5235987901687622, 0.2617993950843811]`, also with five pairs. These are finite rejected solver observations, not accepted grips.

The localization artifact `12844590847` was independently downloaded, CRC-checked and SHA256-matched at `4cc8f072064ad86739b38890c3d5c9dbdcb54a108f7ba5d795a25cfd2ffc9c17`. Embedded JSON SHA256 is `59bbc41598bb8c47bee3e1c0c500eaf2874c44852e1ecc9ea73bb82d7ef46cb4`; Markdown SHA256 is `eb7bb27699a5a0c9814a2d70580c2f607cd68b6f1aaed929397489a23bb44a25`.

No anatomical side, digit contact, object fit, grasp stability, pressure, load transfer, safe technique or reusable grip acceptance is granted. The last rendered trial is explicitly rejected solver state, not a closest or accepted grip.
