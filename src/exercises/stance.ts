import { vec3 } from '../rig/types';
import type { Vec3 } from '../rig/types';
import type { EffectorLock, TechniqueRule } from '../constraints/types';
import type { EquipmentInstance } from '../equipment/types';
import type { FootSpec } from './types';
import { bilateralLock, bilateralRule } from './mirror';
import { plantedContact } from './presets';

/**
 * How a standing exercise meets the floor, and what it holds.
 *
 * Extracted on the same evidence rule as `presets.ts`: only what several
 * exercises already say *identically*, or say the same way with different
 * numbers. What is shared here is the *shape* of standing on two locked feet —
 * a foot spec, a pair of floor locks, and a rule that holds each foot still.
 * Every standing exercise in the library needs exactly those three, and needed
 * them before this file existed.
 *
 * ## The numbers are parameters, and finding that out was the point
 *
 * An earlier version of this file hard-coded a 32 cm stance, 6° of toe-out and a
 * 12 mm tolerance, and claimed in its own comment that the curl, the press *and*
 * the squat had settled on those independently. Two of the three had. The squat
 * stands 42 cm wide with 12° of toe-out and allows 15 mm of foot drift, and it
 * has good reasons for all three: a squat needs a wider base to descend into,
 * the toes turn out so the knees can track over them, and a foot carrying a body
 * through half a metre of vertical travel deforms more under its own load than
 * one standing still under a curl.
 *
 * So the extraction was right and the constants were not. They are arguments
 * now, with the upper-body values as defaults because that is what two of the
 * three callers want, and the squat passing its own. Sharing the shape while
 * letting the numbers differ is the whole distinction — the same one that keeps
 * the curl's 10° torso rule apart from the press's 8°.
 */

/** The feet: their spec, their floor locks and the rule that holds them still. */
export interface PlantedStance {
  feet: FootSpec;
  locks: EffectorLock[];
  technique: TechniqueRule[];
}

export interface StanceOptions {
  /** Distance between the feet, metres. */
  width?: number;
  /** Toe-out angle, degrees. */
  toeOut?: number;
  /**
   * How far a foot may drift over the repetition, metres.
   *
   * Tight enough that a sliding foot fails, loose enough that the solver's own
   * motion does not. Standing exercises hold 12 mm; a squat allows 15 mm because
   * the foot carries the whole body through its descent.
   */
  tolerance?: number;
  /**
   * Hold each foot flat — its opening orientation — as well as in place. For a
   * movement whose shin angle is solved rather than authored; see
   * `EffectorLock.holdOrientation`.
   */
  flat?: boolean;
  /**
   * Where the left knee points, as a world-space pole; the right is mirrored.
   * Unset, the solver follows the pose's own bend plane, which is right for a
   * knee that bends well (the squat) and undefined for one that barely bends: a
   * leg a few degrees from straight has no bend plane to follow, and the solver
   * picks one, twisting the shin — and a flat foot with it — by whatever it
   * picked.
   */
  kneePole?: Vec3;
}

/** A stance with both feet locked to the floor. */
export function plantedStance({
  width = 0.32,
  toeOut = 6,
  tolerance = 0.012,
  flat = false,
  kneePole,
}: StanceOptions = {}): PlantedStance {
  return {
    feet: { width, toeOut, planted: true },
    locks: [
      ...bilateralLock({
        id: 'foot_l',
        chain: 'leg_l',
        mode: 'floor',
        ...(kneePole ? { pole: kneePole } : {}),
        ...(flat ? { holdOrientation: true } : {}),
        enabled: true,
      }),
    ],
    technique: [
      ...plantedContact({
        point: { bone: 'foot_l' },
        tolerance,
        label: 'Left foot stays planted',
      }),
    ],
  };
}

/**
 * The heels stay on the floor.
 *
 * Checked apart from the foot it belongs to, because a heel lifts while the foot
 * as a whole stays exactly where it was — the floor lock holds the foot's
 * position and cannot see it tip. The squat wrote this first; the hinge needed
 * the identical rule, for the opposite reason — a squat lifts the heels by
 * running out of ankle, a hinge by rocking onto the toes as the hips travel back
 * too far — and two lower-body families saying the same thing is the evidence
 * this file extracts on.
 */
export function heelDown(tolerance = 0.025): [TechniqueRule, TechniqueRule] {
  return bilateralRule({
    kind: 'stationary',
    id: 'heel_down_l',
    label: 'Left heel stays on the floor',
    point: { bone: 'foot_l', offset: { x: 0, y: -0.04, z: 0 } },
    tolerance,
    severity: 'error',
  });
}

/**
 * One dumbbell rigidly held in each hand.
 *
 * No grip rotation is calibrated here: the implement is rigid in the hand, so
 * whatever the forearm does carries it. That is what lets a hammer curl turn its
 * dumbbells by naming a grip rather than by placing them.
 */
export function handDumbbells(mass: number): EquipmentInstance[] {
  return (['l', 'r'] as const).map((side) => ({
    id: `dumbbell_${side}`,
    kind: 'dumbbell' as const,
    label: `${side === 'l' ? 'Left' : 'Right'} dumbbell`,
    mass,
    position: vec3(0, 0, 0),
    rotation: vec3(0, 0, 0),
    visible: true,
    attachment: { mode: 'hand' as const, side, socket: 'grip' },
  }));
}
