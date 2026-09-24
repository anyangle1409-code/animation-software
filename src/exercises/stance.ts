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
  /**
   * Hold the feet flat at exactly the stance's toe-out, and aim each knee out
   * along its foot. For a movement whose knees bend deeply over planted feet —
   * the squat.
   *
   * The foot is pinned outright (`flatFootAim`) rather than held from the
   * opening frame, and the pole lies straight out along the foot, 2 m ahead and
   * 1.5 m up, so the knee bends in the plane the foot points along. What twist
   * the ankle's ±10° cannot take as the knee bends, the shin does, as a real
   * tibia rotates on a bent knee (`solveGoals`). Takes precedence over `flat`
   * and `kneePole`.
   */
  kneesOverToes?: boolean;
}

/** A stance with both feet locked to the floor. */
export function plantedStance({
  width = 0.32,
  toeOut = 6,
  tolerance = 0.012,
  flat = false,
  kneePole,
  kneesOverToes = false,
}: StanceOptions = {}): PlantedStance {
  const turn = (toeOut * Math.PI) / 180;
  const alongFoot = vec3(-width / 2 - 2 * Math.sin(turn), 1.5, 2 * Math.cos(turn));
  return {
    feet: { width, toeOut, planted: true },
    locks: [
      ...bilateralLock({
        id: 'foot_l',
        chain: 'leg_l',
        mode: 'floor',
        ...(kneesOverToes
          ? { pole: alongFoot, aim: flatFootAim(toeOut) }
          : {
              ...(kneePole ? { pole: kneePole } : {}),
              ...(flat ? { holdOrientation: true } : {}),
            }),
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
 * Which way a flat left foot points, turned out by `toeOut` degrees — or up on
 * the ball of the foot, heel raised by `heelRaise` degrees: the
 * canonical foot bone at rest runs from the ankle (8 cm up) down to the ball of
 * the foot (2.5 cm up, 14 cm ahead), and its +Z faces up and forward. This is a
 * foot flat on the floor as the rig stands, which is what a lock's `aim` needs
 * when the opening frame cannot supply it — a movement that starts seated or
 * bent over. `stance.test.ts` holds it to the rig.
 */
export function flatFootAim(toeOut: number, heelRaise = 0): { direction: Vec3; forward: Vec3 } {
  const length = Math.hypot(0.055, 0.14);
  const turn = (-toeOut * Math.PI) / 180;
  const raise = (heelRaise * Math.PI) / 180;
  // Heel raised: the foot pitches down about its own cross axis before it turns out.
  const pitch = (y: number, z: number) => [y * Math.cos(raise) - z * Math.sin(raise), y * Math.sin(raise) + z * Math.cos(raise)];
  // `+ 0` keeps a straight foot's x at 0 rather than -0, so it mirrors to itself.
  const along = ([y, z]: number[]) => vec3(z * Math.sin(turn) + 0, y, z * Math.cos(turn));
  return {
    direction: along(pitch(-0.055 / length, 0.14 / length)),
    forward: along(pitch(0.14 / length, 0.055 / length)),
  };
}

/** Length of the foot bone, ankle to the ball of the foot, metres. */
export const FOOT_LENGTH = Math.hypot(0.055, 0.14);

/** Height of the ball of the foot above the floor, metres: the canonical `foot_l` tail. */
export const BALL_HEIGHT = 0.025;

/** Ankle height, metres, of a foot flat on the floor: the canonical `foot_l` head. */
export const ANKLE_HEIGHT = 0.08;

export interface SeatedStanceOptions {
  /** Distance between the ankles, metres. */
  width: number;
  /** Toe-out, degrees. */
  toeOut: number;
  /** How far in front of the hips the ankles are planted, metres. */
  forward: number;
}

/**
 * Sitting with both feet flat on the floor in front.
 *
 * A seated repetition opens seated, and a floor lock takes its anchor from the
 * opening frame — wherever the authored leg angles happen to put the feet. So
 * the feet are placed outright, position and orientation, and the legs are
 * solved to them from the first frame, the way the row pins its standing feet.
 * Toe-out is carried by the pinned orientation, not by the ankle.
 */
export function seatedStance({ width, toeOut, forward }: SeatedStanceOptions): PlantedStance {
  const left = vec3(-width / 2, ANKLE_HEIGHT, forward);
  return {
    feet: { width, toeOut, planted: true },
    locks: [
      ...bilateralLock({
        id: 'foot_l',
        chain: 'leg_l',
        mode: 'floor',
        position: left,
        aim: flatFootAim(toeOut),
        enabled: true,
      }),
    ],
    technique: [
      ...plantedContact({
        point: { bone: 'foot_l' },
        tolerance: 0.012,
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
