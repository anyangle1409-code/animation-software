# Exercise-to-Muscle Movement Contract

Status: experimental authoring contract; not physiology, medical advice or production approval. `PT_MODEL_VERSION` remains `1.0`.

## Purpose

An exercise animation selects a versioned exercise ID and phase. The compiler returns two independent instruction sets:

1. joint target envelopes for the skeletal animation; and
2. muscle rules keyed by permanent anatomical IDs, including role, expected path-length direction, visual activation estimate, deformation mode and skin response.

This prevents every new animation from rebuilding muscle logic by hand. It also prevents skeletal position from being treated as muscle activation. A fixed pose can have low or high activation depending on load and intent; an actively lengthening muscle can be highly activated during an eccentric phase.

## Permanent naming convention

| Entity | Pattern | Example |
| --- | --- | --- |
| Muscle or functional head | `hgpt.muscle.<anatomical_name_or_head>.<L|R>` | `hgpt.muscle.biceps_brachii_long.L` |
| Joint | `hgpt.joint.<joint>.<L|R>` | `hgpt.joint.elbow.L` |
| Exercise | `hgpt.exercise.<exercise>.<variant>.v<major>` | `hgpt.exercise.shoulder_press.bilateral.v1` |
| Interaction | `hgpt.interaction.<relation>.<L|R>` | `hgpt.interaction.rotator_cuff_centring.L` |
| Skin mask | `hgpt.skinmask.<muscle_or_region>.<L|R>` | `hgpt.skinmask.deltoid_middle.L` |

Rules:

- IDs are lowercase ASCII, underscore-separated within a segment and case-sensitive at the side suffix.
- `L` and `R` always mean anatomical left and right. They do not imply Blender/runtime suffixes. The existing F-SIDE-001 mapping must be resolved explicitly.
- Once published, an ID is never reassigned. Renames add a deprecated alias that points to the same semantic structure; deletion leaves a tombstone.
- A broad muscle and each functional head/bundle receive different IDs whenever they need different attachments, path, activation or deformation. Current aggregated seeds such as `thenar_group` remain marked as aggregates until expanded; they cannot masquerade as individually modelled muscles.
- Exercise major versions change only when phase meaning or required outputs become incompatible. Minor data corrections retain the ID and record provenance in Git history.

## Muscle identity contract

Every record in `registry_seed.json` contains:

- permanent ID, side, anatomical name/head and immutability flag;
- origin and insertion descriptions plus unresolved reviewed landmark IDs;
- joints crossed and neighbouring/interaction IDs;
- depth and layering state;
- path and wrapping state;
- contraction behavior: evaluated attachment-path length plus a separate explicit activation channel;
- skin influence permission and mask;
- reference, confidence and license state;
- actual rig binding, which remains `null` until Blender landmark review.

The coarse registry currently has 120 bilateral semantic records. This does not mean every human muscle or every anatomical sub-bundle is modelled. New muscles/heads follow the same ID contract before any geometry is created.

## Exercise contract fields

Each phase declares:

- `joint_targets`: start/end angle envelopes and coordinate names. `activation_driver` must be `false`.
- `muscles[].role`: agonist, synergist, antagonist or stabilizer for this phase.
- `length_change`: shortening, lengthening, near-isometric or variable. This describes the expected reviewed muscle-path trend, not contraction type inferred from pose.
- `activation_estimate`: a normalized 0–1 visual authoring range whose source is `exercise_phase_rule`.
- `deformation`: how reviewed path length and activation feed a muscle proxy/corrective.
- `skin_response`: a named region mask and capped blend, or no direct transfer for deep tissue.

The 0–1 values rank visual emphasis within this animation. They are not EMG percentages, force, torque, recruitment, injury risk or a clinical prescription. Load, tempo, variation, fatigue and individual anatomy can change real activation. The caller supplies an `activation_scale`; this changes activation output without changing joint targets.

## Included examples

| Exercise ID | Phases | Principal rules |
| --- | --- | --- |
| `hgpt.exercise.biceps_curl.bilateral.v1` | setup, concentric, top_hold, eccentric | Biceps heads/brachialis/brachioradialis flex; triceps is antagonist; supinated forearm is specified in setup. |
| `hgpt.exercise.shoulder_press.bilateral.v1` | rack, press, overhead_hold, lower | Deltoid heads and triceps press; trapezius/serratus coordinate scapular motion; cuff stabilizes. No fixed universal scapulohumeral ratio. |
| `hgpt.exercise.squat.bodyweight.v1` | stand, descent, bottom_hold, ascent | Quadriceps/glute max/adductor magnus produce extension; glute med and lower-leg groups stabilize; multi-joint rectus femoris/hamstrings may have variable path behavior. |

Angle ranges are authoring envelopes that Claude must reconcile with the validated skeleton, movement benchmark and exercise variant. They are not universal prescriptions.

## Working example for Claude

Validate the complete registry and exercise library:

```bash
python -m unittest discover -s experiments/anatomical_muscles/tests -v
```

Compile the midpoint of a curl concentric phase with 80% of the contract's visual activation range:

```bash
python -m experiments.anatomical_muscles.compile_exercise \
  --exercise hgpt.exercise.biceps_curl.bilateral.v1 \
  --phase concentric \
  --progress 0.5 \
  --activation-scale 0.8 \
  --out /tmp/curl_concentric_mid.json
```

Claude then:

1. resolves each `muscle_id` to the reviewed Blender collection/object and actual binding;
2. animates the returned joint envelopes using the exercise-specific movement profile;
3. measures actual attachment-path length rather than trusting the declared length state;
4. applies the explicit visual activation independently;
5. sends only reviewed superficial/cage deltas through the named skin mask and cap;
6. compares actual path direction with `length_change` and fails the phase when they disagree;
7. renders and benchmarks the whole trajectory before saving a new experimental suffix.

To create another exercise, copy the schema in `exercise_contracts.json`, select existing immutable muscle IDs, define phase-specific joint targets and roles, cite sources, then run the validator. Do not duplicate Blender muscle objects or invent new IDs inside an animation file.

## Evidence and limits

The examples use the project muscle research plus experimental/review literature on elbow flexor angle effects, deltoid activity during shoulder press, overhead-press variation, independently represented scapular motion and squat biomechanics. These sources guide qualitative selection and cautions. Their cohort measurements are not copied as universal activation values.

Exact attachment coordinates, path wrapping, path-length signs, skin masks and deformation caps remain native-Blender tasks. No exercise contract is accepted until it resolves against the actual rig and passes the movement, collision, volume, topology and visual comparison gates.
