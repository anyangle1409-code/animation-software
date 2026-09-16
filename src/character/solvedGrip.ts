import type { Finger } from '../rig/boneNames';
import type { GripKind } from '../exercises/types';

/**
 * A grip solved against a real handle, per digit, per joint.
 *
 * Angles are degrees at closure 1, in the same convention `applyGrip` uses, so
 * a solved row is a drop-in replacement for the profile row it came from.
 */
export interface SolvedGrip {
  /** MCP / PIP / DIP per digit, including the thumb's three z rotations. */
  digits: Readonly<Record<Finger, readonly [number, number, number]>>;
  /** Thumb-base x rotation, the rig's limited opposition proxy. */
  thumbOppositionX: number;
  /** The handle radius in metres these angles were solved against. */
  radius: number;
  /**
   * A correction to the character's embedded handle centre, in metres, in the
   * frame `handleGripOffsets` is expressed in. x is mirrored with the hand.
   *
   * It belongs with the solved angles rather than in the asset: the two were
   * solved together and neither is right without the other. Applying it where
   * `gripOffset` is built keeps the renderer, the exporter and the diagnostics
   * on one centre by construction.
   */
  handleCentre?: { x: number; y: number; z: number };
}

/**
 * Why this is per character rather than a grip profile.
 *
 * `GRIP_PROFILES` is authored against the canonical rig, and the canonical rig
 * has to keep reaching the canonical handle — `src/equipment/grip.test.ts`
 * measures exactly that. An imported character has its own finger lengths, its
 * own knuckle placement and its own `handleGripOffsets`, so the pose that puts
 * its fingers on the bar is not the pose that puts the canonical rig's fingers
 * on the canonical bar. One angle table cannot serve both, and making the
 * profile serve the character breaks the canonical grip by 10.7 mm.
 *
 * So the canonical rig keeps the authored profile and a character may carry a
 * solved override, keyed by character and grip family. The family implies the
 * handle diameter; `radius` records which one, so a future family at a
 * different diameter is solved rather than assumed to transfer.
 */
const SOLVED: Record<string, Partial<Record<GripKind, SolvedGrip>>> = {
  // Home Gym PT male baseline, solved by close-until-contact against the real
  // 15 mm dumbbell bar: each joint advances along the authored pattern and
  // locks where that digit's own skinned surface first reaches the cylinder.
  //
  // The authored profile closes every digit to the same fraction of the same
  // pose, so the hand shuts straight through the bar — 11.48 mm over 53
  // vertices. Solved, no digit penetrates, the palm stays loaded at -1.14 mm
  // and wrap is 240 degrees.
  //
  // thumbOppositionX is positive where every profile has it negative. That is
  // not a transcription slip: the axis takes no per-side sign flip, so the
  // shared -14 drives the thumb into the handle on both hands. The thumb needed
  // no change to its flexion once the sign was right.
  homeGymPTMale: {
    dumbbell: {
      radius: 0.015,
      thumbOppositionX: 16.47,
      // 9 mm proximally, deeper into the palm. Measured, not chosen: at the
      // embedded centre every MCP locked almost immediately because the handle
      // sat against the knuckle row, so the fingers could not roll over it and
      // the index barely closed at 30.4 degrees. Moving the centre back frees
      // all four together while the palm loads from -1.14 mm to -2.54 mm.
      // 6 mm still leaves the lower fingers at the handle's side; 12 mm is no
      // better in kind and spends the thumb's clearance down to -0.19 mm.
      handleCentre: { x: 0, y: -0.009, z: 0 },
      digits: {
        index: [61.75, 95.0, 57.5],
        middle: [71.5, 83.12, 52.5],
        ring: [65.0, 71.25, 47.5],
        pinky: [35.75, 51.46, 60.0],
        thumb: [-22.0, 60.0, 60.0],
      },
    },
  },
};

/** The solved grip for a character and grip family, or null to use the profile. */
export function solvedGripFor(solutionId: string | undefined, grip: GripKind): SolvedGrip | null {
  if (!solutionId) return null;
  return SOLVED[solutionId]?.[grip] ?? null;
}
