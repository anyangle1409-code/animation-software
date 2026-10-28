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

The parser fails closed on wrong source/preservation/approval metadata, unexpected solver outcome, missing or unknown suffixes, nonfinite Euler values, boolean or negative counts, and any inconsistency between the pair guard and whether collapse was measured. Output paths are prevented from aliasing or nesting inside evidence inputs.

## Current status

Synthetic regression coverage is staged. Exact phone-readable W8/V14/R120 counts and cloud artifact hashes are **PENDING** until the branch workflow completes. Existing evidence already indicates only authored suffix `l` was trialled, so bilateral trial coverage is incomplete; this must be reproduced by the new report before final verification.

No anatomical side, digit contact, object fit, grasp stability, pressure, load transfer, safe technique or reusable grip acceptance is granted. The last rendered trial is explicitly rejected solver state, not a closest or accepted grip.
