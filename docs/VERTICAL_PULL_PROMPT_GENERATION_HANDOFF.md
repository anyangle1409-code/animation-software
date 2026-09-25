# Vertical-pull prompt-generation handoff

## Branch

`work/prompt-generation-vertical-pull-latest-20260925`

Layered on:
- latest-source hinge/RDL branch
- latest-source bent-over-row branch

The original source snapshot was:
`47187360b5d631d438a6b33b284ad06732e244cb`

The live source branch is unchanged.

## Added here

Strict pull-up generation through the existing `verticalPullFamily()`.

Supported example:

```
Create a strict pull-up with controlled tempo.
```

The adapter:
- uses existing `verticalPullFamily()` unchanged;
- uses library reference `pull_up`;
- uses bodyweight plus the family's fixed squat-rack bar;
- defaults to the family's pronated overhand grip and fixed grip width;
- uses new intent support `hanging`;
- accepts existing tempo profiles;
- adds no correction lever.

## Explicit refusals

Rather than guessing, it rejects:
- chin-up / underhand variants;
- neutral-grip pull-up;
- kipping pull-up;
- assisted pull-up;
- weighted pull-up;
- wide/close/narrow grip changes;
- behind-the-neck pull-up;
- lat pulldown.

## Why this is a useful generator proof

This family is mechanically different from the standing families:
- both hands are locked to fixed equipment sockets;
- the feet are not planted;
- the body moves relative to a fixed bar;
- full hang, chin clearance and anti-kip technique are already validated by the family.

The generator adapter adds no new biomechanics.

## Validation

CI on this isolated branch must pass:
1. typecheck;
2. focused parser/generator tests;
3. build;
4. full suite.

Do not weaken existing pull-up grip/contact/IK rules to make generation pass.
