/**
 * Project-authored design targets for ORIGINAL v1. These values are creative
 * product dimensions, expressed independently of v3 and every imported mesh.
 *
 * Kept in a tiny dependency-free module so other first-party systems can use
 * body-relative design targets without importing the active runtime rig or the
 * complete canonical-v4 bone definition.
 */
export const HGPT_CANONICAL_V4_ORIGINAL_DIMENSIONS = {
  height: 1.82,
  shoulderBreadth: 0.43,
  hipJointBreadth: 0.184,
  upperArmLength: 0.325,
  forearmLength: 0.27,
  wristToPalmAxisEnd: 0.095,
  femurLength: 0.445,
  tibiaLength: 0.43,
  metacarpals: { index: 0.07, middle: 0.072, ring: 0.066, pinky: 0.058 },
  fingers: {
    thumb: [0.048, 0.031, 0.024],
    index: [0.045, 0.027, 0.02],
    middle: [0.049, 0.03, 0.022],
    ring: [0.046, 0.028, 0.021],
    pinky: [0.036, 0.022, 0.018],
  },
} as const;
