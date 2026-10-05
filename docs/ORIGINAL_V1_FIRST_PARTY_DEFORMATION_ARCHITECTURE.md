# ORIGINAL v1 first-party deformation architecture

## Purpose

The final character must not depend on exercise-specific deformation patches.

The production target is a deterministic deformation stack in which the same
canonical joint/attachment state produces the same human-like surface response
regardless of whether that state came from a shoulder press, pull-up, row, lunge,
or a future exercise that does not yet exist.

This document is subordinate to the live candidate evidence and
`docs/ORIGINAL_V1_HUMAN_BODY_MASTER_PLAN.md`, and works with
`docs/ORIGINAL_V1_ANATOMICAL_COUPLING_CONTRACT.md`.

The machine-readable authority is
`ORIGINAL_V1_FIRST_PARTY_DEFORMATION_ARCHITECTURE.json`.

## Core architecture

### 0. Canonical kinematics

The locked canonical rig supplies joint transforms. A skin correction is never
allowed to hide a true skeletal-motion error.

### 1. Evidence-selected base skinning

Use the exact saved Blender skinning mode as the starting reference.

Do **not** assume that ordinary linear blend skinning is good enough, and do not
assume that dual-quaternion/preserve-volume skinning is automatically better.

Linear skinning is known to lose volume and create collapsing/candy-wrapper
artifacts. Dual-quaternion approaches improve some of those problems but can
introduce bulging artifacts of their own. Therefore the project must compare
base skinning modes on the **same mesh, weights, rig and poses** and choose using
whole-body evidence rather than theory alone.

The read-only tool
`scripts/audit_original_v1_skinning_mode_blender.py`
records what the current candidate actually uses.

### 2. Multi-anchor anatomical coupling

Base skinning then feeds the anatomical coupling layer.

This is the layer that enforces the user's non-negotiable requirement:

> if an arm, leg, hand, foot, neck or trunk segment moves, every anatomically
> connected skin/muscle path that should respond must respond, while rooted
> tissue must remain rooted.

Examples:

- pectoral chest-side anchors remain rooted while the humeral insertion follows
  the arm;
- posterior axillary/lat-teres support spans trunk/scapular and humeral sides;
- deltoid spans shoulder girdle and humerus;
- rectus femoris depends on hip **and** knee state;
- hamstrings depend on hip **and** knee state;
- gastrocnemius/Achilles depends on knee **and** ankle state;
- finger/palm surface follows the tendon/attachment chain rather than isolated
  hinge cylinders.

The coupling layer is generic by anatomical system. It is never selected by an
exercise name.

### 3. Generic pose-space corrective layer

Once base skinning and shared-tissue ownership are plausible, residual anatomy
can be corrected by generic joint-state-driven basis fields.

Drivers are quantities such as:

- humerothoracic elevation;
- plane of elevation;
- scapular relative rotation;
- elbow flexion and forearm rotation;
- hip plus knee state for biarticular thigh systems;
- knee plus ankle state for gastrocnemius/Achilles;
- wrist/forearm state and declared grip/contact state.

A runtime corrective must **not** branch on "shoulder_press", "pull_up",
"lunge", or any other exercise identity.

The interpolation must be deterministic, continuous, bounded and tested at
intermediate and return states. Endpoint correctness is not sufficient.

### 4. Contact/load-aware local response

Once the quasi-static body foundation is proven, local contact response may be
added for:

- palm/equipment;
- palm/floor;
- foot/floor;
- toe/forefoot;
- heel/forefoot during plantarflexion.

Contact response cannot move the skeleton or distort an upstream tissue chain to
hide a contact error.

### 5. Optional secondary soft-tissue dynamics

Jiggle/inertial secondary motion is a separate later concern.

It is not required to repair bad quasi-static anatomy. If the product does not
need visible secondary dynamics, the body may be frozen without this layer once
all quasi-static human deformation requirements are satisfied.

## No exercise-specific deformation

The runtime deformation input is limited to:

- canonical bone transforms;
- relative attachment transforms;
- joint angles derived from those transforms;
- project-owned coupling parameters;
- project-owned contact/load state;
- optional motion derivatives for an explicitly implemented secondary-dynamics
  layer.

Exercise name/id is a forbidden deformation input.

This is crucial for the eventual Home Gym PT goal: a new exercise should inherit
already-proven human anatomy because it is built from known joint states, rather
than requiring another bespoke mesh patch.

## Base-skinning A/B decision

Before changing the skinning basis globally, compare the current saved mode
against Blender preserve-volume/DQ on isolated copies using:

- the exact same source candidate;
- exact same rig;
- exact same weights;
- exact same stress/movement poses;
- same corrective state;
- same cameras.

Evaluate at minimum:

- shoulder/axilla elevation arc;
- elbow flexion and forearm rotation;
- loaded wrist extension;
- deep squat/lunge;
- ankle/foot stress;
- whole-body numerical regression;
- real-human visual evidence.

No global switch is accepted because one shoulder image improves.

## Production parity

The final Blender result is only a reference if the standalone first-party
runtime can reproduce it.

Production freeze is blocked by any Blender-only deformation mechanism that
cannot be represented using independently authored runtime data and code.

The final parity packet must bind:

- canonical rig;
- base-skinning semantics;
- coupling data;
- corrective basis fields;
- driver definitions;
- contact/load facts;
- exact model/runtime hashes;
- surface comparisons across mandatory movement samples.

## Current execution order

1. audit the exact r95 skinning mode;
2. run the shoulder-layer diagnostic;
3. run pose-to-connected-tissue scope mapping;
4. declare the first four shoulder/chest coupling zones;
5. audit their weight ownership;
6. create a new candidate and repair weights/support first;
7. prove the weights-only elevation arc;
8. fit only generic joint-state residual correctives;
9. run the full visual/numeric/contact/regression matrix;
10. populate coupling evidence;
11. close only candidate-bound verified defect rows.

No cosmetic Phase 5 work should precede that foundation.
