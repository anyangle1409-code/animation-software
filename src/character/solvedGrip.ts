import type { Finger } from '../rig/boneNames';
import type { GripKind } from '../exercises/types';

/**
 * A grip solved against a real handle, per digit, per joint.
 *
 * The mechanism is first-party and remains available for ORIGINAL v1. The
 * standalone branch intentionally ships no character-specific solved rows until
 * an independently authored production character has been measured and
 * approved.
 */
export interface SolvedGrip {
  /** MCP / PIP / DIP per digit, including the thumb's three z rotations. */
  digits: Readonly<Record<Finger, readonly [number, number, number]>>;
  /** Thumb-base x rotation, the rig's limited opposition proxy. */
  thumbOppositionX: number;
  /** The handle radius in metres these angles were solved against. */
  radius: number;
  /** Optional correction to the character's embedded handle centre. */
  handleCentre?: { x: number; y: number; z: number };
}

/**
 * Character-specific solved grips are deliberately empty during the clean-room
 * transition. Legacy baseline measurements live only on the preserved archive
 * branch. ORIGINAL v1 may add a new row only after its own grip/contact evidence
 * is generated and approved.
 */
const SOLVED: Record<string, Partial<Record<GripKind, SolvedGrip>>> = {};

/** The solved grip for a character and grip family, or null to use the authored profile. */
export function solvedGripFor(solutionId: string | undefined, grip: GripKind): SolvedGrip | null {
  if (!solutionId) return null;
  return SOLVED[solutionId]?.[grip] ?? null;
}
