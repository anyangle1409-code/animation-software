import { describe, expect, it } from 'vitest';
import { canonicalSkeleton } from './skeleton';
import { SKELETON_ID } from '../export/json';

/**
 * STRUCTURALLY FROZEN — the canonical skeleton, `hgpt_canonical_v3`.
 *
 * Final skin weights are painted against this hierarchy and these rest
 * positions, and every exported file names this skeleton. So both are held
 * here exactly: which bones exist, what each hangs from, and where each one
 * rests. Joint limits are not frozen — they can be tuned without touching a
 * weight — and neither is any motion: the scapulae and the palm stay at rest
 * until a rhythm or cupping is authored, which changes no bone.
 *
 * If this test fails, the rig's structure changed. That is not a test to
 * update in passing: it needs a new skeleton id, a migration for exported
 * files, a re-check of every weight, and `docs/CANONICAL_SKELETON_FREEZE.md`.
 */
const HIERARCHY: [string, string | null][] = [
  ['root', null],
  ['pelvis', 'root'],
  ['spine_01', 'pelvis'],
  ['spine_02', 'spine_01'],
  ['spine_03', 'spine_02'],
  ['neck', 'spine_03'],
  ['head', 'neck'],
  ['clavicle_l', 'spine_03'],
  ['scapula_l', 'clavicle_l'],
  ['upperarm_l', 'scapula_l'],
  ['forearm_l', 'upperarm_l'],
  ['hand_l', 'forearm_l'],
  ['thigh_l', 'pelvis'],
  ['shin_l', 'thigh_l'],
  ['foot_l', 'shin_l'],
  ['toe_l', 'foot_l'],
  ['thumb_01_l', 'hand_l'],
  ['thumb_02_l', 'thumb_01_l'],
  ['thumb_03_l', 'thumb_02_l'],
  ['metacarpal_index_l', 'hand_l'],
  ['index_01_l', 'metacarpal_index_l'],
  ['index_02_l', 'index_01_l'],
  ['index_03_l', 'index_02_l'],
  ['metacarpal_middle_l', 'hand_l'],
  ['middle_01_l', 'metacarpal_middle_l'],
  ['middle_02_l', 'middle_01_l'],
  ['middle_03_l', 'middle_02_l'],
  ['metacarpal_ring_l', 'hand_l'],
  ['ring_01_l', 'metacarpal_ring_l'],
  ['ring_02_l', 'ring_01_l'],
  ['ring_03_l', 'ring_02_l'],
  ['metacarpal_pinky_l', 'hand_l'],
  ['pinky_01_l', 'metacarpal_pinky_l'],
  ['pinky_02_l', 'pinky_01_l'],
  ['pinky_03_l', 'pinky_02_l'],
  ['clavicle_r', 'spine_03'],
  ['scapula_r', 'clavicle_r'],
  ['upperarm_r', 'scapula_r'],
  ['forearm_r', 'upperarm_r'],
  ['hand_r', 'forearm_r'],
  ['thigh_r', 'pelvis'],
  ['shin_r', 'thigh_r'],
  ['foot_r', 'shin_r'],
  ['toe_r', 'foot_r'],
  ['thumb_01_r', 'hand_r'],
  ['thumb_02_r', 'thumb_01_r'],
  ['thumb_03_r', 'thumb_02_r'],
  ['metacarpal_index_r', 'hand_r'],
  ['index_01_r', 'metacarpal_index_r'],
  ['index_02_r', 'index_01_r'],
  ['index_03_r', 'index_02_r'],
  ['metacarpal_middle_r', 'hand_r'],
  ['middle_01_r', 'metacarpal_middle_r'],
  ['middle_02_r', 'middle_01_r'],
  ['middle_03_r', 'middle_02_r'],
  ['metacarpal_ring_r', 'hand_r'],
  ['ring_01_r', 'metacarpal_ring_r'],
  ['ring_02_r', 'ring_01_r'],
  ['ring_03_r', 'ring_02_r'],
  ['metacarpal_pinky_r', 'hand_r'],
  ['pinky_01_r', 'metacarpal_pinky_r'],
  ['pinky_02_r', 'pinky_01_r'],
  ['pinky_03_r', 'pinky_02_r'],
];

/** Rest head and tail, metres, to the micrometre. */
const REST: Record<string, [number, number, number, number, number, number]> = {
  "root": [0, 0, 0, 0, 0.2, 0],
  "pelvis": [0, 0.95, 0, 0, 1.03, 0],
  "spine_01": [0, 1.03, 0, 0, 1.15, 0],
  "spine_02": [0, 1.15, 0, 0, 1.27, 0],
  "spine_03": [0, 1.27, 0, 0, 1.42, 0],
  "neck": [0, 1.42, 0, 0, 1.52, 0],
  "head": [0, 1.52, 0, 0, 1.75, 0],
  "clavicle_l": [-0.02, 1.42, 0.012, -0.20367, 1.44, -0.035],
  "scapula_l": [-0.20367, 1.44, -0.035, -0.09, 1.25, -0.15],
  "upperarm_l": [-0.20367, 1.44, -0.035, -0.20367, 1.14, -0.035],
  "forearm_l": [-0.20367, 1.14, -0.035, -0.20367, 0.88, -0.035],
  "hand_l": [-0.20367, 0.88, -0.035, -0.20367, 0.79, -0.035],
  "thigh_l": [-0.09, 0.92, 0, -0.082, 0.5, 0],
  "shin_l": [-0.082, 0.5, 0, -0.082, 0.08, 0],
  "foot_l": [-0.082, 0.08, 0, -0.082, 0.025, 0.14],
  "toe_l": [-0.082, 0.025, 0.14, -0.082, 0.02, 0.21],
  "thumb_01_l": [-0.19667, 0.852, -0.013, -0.194148, 0.821731, 0.016008],
  "thumb_02_l": [-0.194148, 0.821731, 0.016008, -0.192226, 0.798669, 0.038109],
  "thumb_03_l": [-0.192226, 0.798669, 0.038109, -0.190784, 0.781373, 0.054684],
  "metacarpal_index_l": [-0.20467, 0.854077, -0.018625, -0.20467, 0.789, -0.003],
  "index_01_l": [-0.20467, 0.789, -0.003, -0.20509, 0.74701, -0.00216],
  "index_02_l": [-0.20509, 0.74701, -0.00216, -0.20535, 0.721017, -0.00164],
  "index_03_l": [-0.20535, 0.721017, -0.00164, -0.20555, 0.701022, -0.00124],
  "metacarpal_middle_l": [-0.20567, 0.851768, -0.029125, -0.20567, 0.788, -0.024],
  "middle_01_l": [-0.20567, 0.788, -0.024, -0.20567, 0.742, -0.024],
  "middle_02_l": [-0.20567, 0.742, -0.024, -0.20567, 0.714, -0.024],
  "middle_03_l": [-0.20567, 0.714, -0.024, -0.20567, 0.693, -0.024],
  "metacarpal_ring_l": [-0.20467, 0.844842, -0.039625, -0.20467, 0.789, -0.045],
  "ring_01_l": [-0.20467, 0.789, -0.045, -0.20446, 0.747005, -0.04563],
  "ring_02_l": [-0.20446, 0.747005, -0.04563, -0.20433, 0.721008, -0.04602],
  "ring_03_l": [-0.20433, 0.721008, -0.04602, -0.20423, 0.701011, -0.04632],
  "metacarpal_pinky_l": [-0.20167, 0.841846, -0.049625, -0.20167, 0.792, -0.065],
  "pinky_01_l": [-0.20167, 0.792, -0.065, -0.20133, 0.758017, -0.066019],
  "pinky_02_l": [-0.20133, 0.758017, -0.066019, -0.20112, 0.737027, -0.066649],
  "pinky_03_l": [-0.20112, 0.737027, -0.066649, -0.20095, 0.720036, -0.067159],
  "clavicle_r": [0.02, 1.42, 0.012, 0.20367, 1.44, -0.035],
  "scapula_r": [0.20367, 1.44, -0.035, 0.09, 1.25, -0.15],
  "upperarm_r": [0.20367, 1.44, -0.035, 0.20367, 1.14, -0.035],
  "forearm_r": [0.20367, 1.14, -0.035, 0.20367, 0.88, -0.035],
  "hand_r": [0.20367, 0.88, -0.035, 0.20367, 0.79, -0.035],
  "thigh_r": [0.09, 0.92, 0, 0.082, 0.5, 0],
  "shin_r": [0.082, 0.5, 0, 0.082, 0.08, 0],
  "foot_r": [0.082, 0.08, 0, 0.082, 0.025, 0.14],
  "toe_r": [0.082, 0.025, 0.14, 0.082, 0.02, 0.21],
  "thumb_01_r": [0.19667, 0.852, -0.013, 0.194148, 0.821731, 0.016008],
  "thumb_02_r": [0.194148, 0.821731, 0.016008, 0.192226, 0.798669, 0.038109],
  "thumb_03_r": [0.192226, 0.798669, 0.038109, 0.190784, 0.781373, 0.054684],
  "metacarpal_index_r": [0.20467, 0.854077, -0.018625, 0.20467, 0.789, -0.003],
  "index_01_r": [0.20467, 0.789, -0.003, 0.20509, 0.74701, -0.00216],
  "index_02_r": [0.20509, 0.74701, -0.00216, 0.20535, 0.721017, -0.00164],
  "index_03_r": [0.20535, 0.721017, -0.00164, 0.20555, 0.701022, -0.00124],
  "metacarpal_middle_r": [0.20567, 0.851768, -0.029125, 0.20567, 0.788, -0.024],
  "middle_01_r": [0.20567, 0.788, -0.024, 0.20567, 0.742, -0.024],
  "middle_02_r": [0.20567, 0.742, -0.024, 0.20567, 0.714, -0.024],
  "middle_03_r": [0.20567, 0.714, -0.024, 0.20567, 0.693, -0.024],
  "metacarpal_ring_r": [0.20467, 0.844842, -0.039625, 0.20467, 0.789, -0.045],
  "ring_01_r": [0.20467, 0.789, -0.045, 0.20446, 0.747005, -0.04563],
  "ring_02_r": [0.20446, 0.747005, -0.04563, 0.20433, 0.721008, -0.04602],
  "ring_03_r": [0.20433, 0.721008, -0.04602, 0.20423, 0.701011, -0.04632],
  "metacarpal_pinky_r": [0.20167, 0.841846, -0.049625, 0.20167, 0.792, -0.065],
  "pinky_01_r": [0.20167, 0.792, -0.065, 0.20133, 0.758017, -0.066019],
  "pinky_02_r": [0.20133, 0.758017, -0.066019, 0.20112, 0.737027, -0.066649],
  "pinky_03_r": [0.20112, 0.737027, -0.066649, 0.20095, 0.720036, -0.067159],
};

describe('the frozen canonical skeleton', () => {
  it('is hgpt_canonical_v3', () => {
    expect(SKELETON_ID).toBe('hgpt_canonical_v3');
  });

  it('has exactly the frozen hierarchy: 63 bones, each under its frozen parent', () => {
    expect(canonicalSkeleton.bones.map((bone) => [bone.name, bone.parent])).toEqual(HIERARCHY);
    expect(HIERARCHY).toHaveLength(63);
  });

  it('rests every bone exactly where it was frozen', () => {
    for (const bone of canonicalSkeleton.bones) {
      const [hx, hy, hz, tx, ty, tz] = REST[bone.name];
      const head = bone.restHead;
      const tail = bone.restTail;
      for (const [actual, frozen, label] of [
        [head.x, hx, 'head x'], [head.y, hy, 'head y'], [head.z, hz, 'head z'],
        [tail.x, tx, 'tail x'], [tail.y, ty, 'tail y'], [tail.z, tz, 'tail z'],
      ] as const) {
        expect(Math.abs(actual - frozen), `${bone.name} ${label}`).toBeLessThan(1e-6);
      }
    }
  });
});
