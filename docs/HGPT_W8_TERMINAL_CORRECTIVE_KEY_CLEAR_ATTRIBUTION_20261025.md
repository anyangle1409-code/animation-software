# W8 terminal corrective-key family-clear attribution — 2026-10-25

## Purpose

The verified W8 forward benchmark resets the skeleton but leaves 14 terminal non-Basis keys active. This read-only experiment separates that corrective-key state from skeletal skinning by temporarily clearing one actually active authored family at a time while the skeleton remains reset.

It is an attribution diagnostic, not an instruction to delete or disable any corrective. It does not identify anatomical tissue, prove that skeletal weights are correct, establish neutral posture, or authorize a repair.

## Method

- Preserve the immutable W8 source SHA256 `2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c` and frozen r57 code commit `025d5f28fa7eba2064fba565b1c9b60119cdd2cb`.
- Capture the failed terminal evaluated mesh after the pinned runner's final skeletal reset.
- Partition every active non-Basis key exactly once using its existing permanent authored family prefix. Unknown or ambiguous active keys fail closed.
- For each family, set only its active terminal keys to zero in memory, update Blender, and measure frozen-topology geometry against both the benchmark reference and the observed terminal mesh.
- Restore the exact saved values after every trial and verify the full terminal evaluated mesh and skeletal signature are unchanged before continuing.
- Retain the subsequent reverse replay and all-key clear experiment as separately labelled evidence. Never save a `.blend`.

## Interpretation gates

- Status is `READ_ONLY_RUNTIME_KEY_CLEAR_ATTRIBUTION_NOT_REPAIR`.
- A family trial measures the marginal geometric effect of clearing that family in the presence of all other active terminal families. Correctives can overlap, so marginal displacements are not additive and do not assign anatomical tissue causality.
- A smaller reference residual after clearing a family does not prove that family is anatomically wrong; a corrective can compensate for another defect or encode a deliberate pose convention.
- Muscle origins, insertions, side axes and highlighting remain out of scope. Population ROM averages remain references, not hard constraints.

## Verification state

Five new behavior tests were observed RED before implementation and GREEN afterward, alongside the existing report integrity cases. Review hardening requires the selected values to remain exactly zero before and after evaluation while the skeleton and every nonselected value/mute remain fixed; every trial then restores all saved key values and mute flags in `finally` and verifies exact pose/key/evaluated-geometry restoration. The report's family partition must equal the canonical prefix-derived partition.

Run `40204767570` at commit `188fdc66aef28c45cfbde424b4820336eecc31f1` completed SUCCESS 7/7. The exact terminal partition is S1 four keys, S3 two keys, S5 four keys and S7 four keys. Trial results:

| Cleared family | Moved vs terminal | Max vs terminal | RMS vs terminal | Remaining max vs reference | Remaining RMS vs reference |
|---|---:|---:|---:|---:|---:|
| S1 | 93,118 | 28.590 mm | 7.613 mm | 56.181 mm | 9.503 mm |
| S3 | 0 | 0 mm | 0 mm | 62.314 mm | 12.930 mm |
| S5 | 53,514 | 46.298 mm | 5.202 mm | 45.486 mm | 11.313 mm |
| S7 | 98,765 | 40.656 mm | 7.702 mm | 51.097 mm | 9.655 mm |

S3 is active by value but has no evaluated geometric effect in this reset-skeleton condition. S1, S5 and S7 each have material, overlapping marginal effects; no single-family clear restores the reference. The experiment therefore supports a stale multi-family runtime-state diagnosis, not disabling or editing any family.

Pose artifact `12603526912` was independently downloaded, CRC checked and rehashed as `3017fc9851527c137ce65ddce28bbd9bf31fc80afd9dfcf3e3c12ccfe3371c3f`. It contains 71 members, 66 PNGs and no `.blend`.
