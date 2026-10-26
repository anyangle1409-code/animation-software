# W8 terminal corrective-key mute-state audit — 2026-10-26

## Question

The native terminal family-clear experiment found that both S3_125 keys have value `1.0` but clearing the family changes zero evaluated vertices. Existing static rules confirm S3_125 is deliberately driven at high elevation, while existing stored-delta summaries do not cover these two endpoint keys. The next safe discriminator is the actual Blender `mute` state of every nonzero terminal key.

## Method and boundaries

- Extend each already-recorded active terminal key row with Blender's read-only boolean `mute` property.
- Require an actual boolean in both summary construction and report validation; missing or numeric substitutes fail closed.
- Keep the existing family-clear condition/restoration guards, reverse replay and explicit-clear experiment unchanged.
- Do not toggle mutes, edit a key, save a `.blend`, or infer anatomy from the result.

A muted key with a nonzero numeric value explains why the driver state can appear active without evaluated geometric contribution. An unmuted key with no family-clear effect instead requires a later stored-delta/relative-key or dependency investigation. Neither outcome authorizes changing the source.

## Verification state

The new missing/nonboolean mute regression was observed RED before implementation and GREEN afterward. Focused22/22, full265/265 diagnostic tests and7/7 replay guards pass locally. Native key mute values and artifact evidence are pending.
