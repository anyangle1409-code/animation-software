import type {
  CameraRecommendation,
  CommonError,
  ExerciseDefinition,
  MuscleInvolvement,
  Tempo,
} from '../types';
import { vec3 } from '../../rig/types';
import { bilateralJointTarget, bilateralJoints, bilateralRule } from '../mirror';
import { evenSides } from '../presets';
import { handDumbbells, heelDown, plantedStance } from '../stance';

/**
 * The hinge family.
 *
 * The fourth family, and the second below the waist. It exists to answer the
 * question the squat could not: which of the squat's rules belong to the lower
 * body, and which belong to the squat. A hinge bends the same three joints in
 * almost the opposite proportion — the hips a great deal, the knees barely, the
 * ankles not at all — so anything the two genuinely share is a lower-body
 * primitive, and anything they share only in shape is not.
 *
 * ## The trunk tips as one piece, from the floor
 *
 * A squat folds the trunk over the hips at the pelvis and the spine. A hinge
 * cannot: the pelvis allows 45° of tilt and the spine is supposed to stay
 * neutral, while the trunk has to reach 70° from vertical. So the whole body
 * pitches forward at the root — the same lever the push-up uses to lie down —
 * and the legs are solved backwards from the locked feet underneath it. Pelvis
 * and spine stay at their standing values, which is what "neutral spine" means:
 * the angle between the pelvis and the ribcage does not change, the angle
 * between the pelvis and the thighs does.
 *
 * Pitching at the root swings the hips forward, since the root sits on the
 * floor. Where the hips should be is the thing a coach actually describes — back
 * over the heels, barely lower — so the variant names that, and the root is
 * derived from it (`hingeRoot`), the same way the push-up derives its root from
 * where its toes must stay.
 *
 * ## None of the leg angles are inputs
 *
 * As in the squat, the hip and knee angles are **outputs**. The root placement
 * and the locked feet fix where the hip and ankle joints are, and the knee has
 * one place to go. The `jointTargets` for them describe the result so the
 * definition reads correctly and the technique rules have something to check;
 * `hinge.test.ts` measures that they agree with what is solved.
 *
 * Unlike the squat, the ankle is an output too. The shins' lean is a by-product
 * of the hips travelling back — 7° forward mid-descent as the knees unlock,
 * 4° back at the bottom — so an authored ankle angle cannot follow it, and a
 * foot turning with the shin tips its toes into the floor. The feet therefore
 * hold their opening orientation (`plantedStance({ flat })`) and the ankle takes
 * up whatever the shin does.
 *
 * ## What is shared with the squat, and what is not
 *
 * - **Shared:** the planted stance and the heel rule. The heel lifts for
 *   opposite reasons — a squat runs out of ankle, a hinge rocks onto the toes
 *   when the hips go back too far — but it is the same fact about the same
 *   point, so it moved to `stance.ts`.
 * - **Same shape, different intent, so not shared:** the depth rule measures the
 *   pelvis against the knee in both, but a squat must get *below* a line and a
 *   hinge must stay *above* one — the hinge's version is the rule that stops it
 *   turning into a squat. The shin rule is a squat's 45° allowance and a hinge's
 *   15°; the torso rule is a squat's ceiling and a hinge's floor.
 * - **Squat-only:** knee tracking. A knee bent 20° has nowhere to cave to, and
 *   holding it to a band written for a knee bent 113° would check nothing.
 */

export interface HingeVariant {
  id: string;
  name: string;
  clipName: string;
  description: string;
  /** Load per hand, kilograms. */
  mass?: number;
  /** Distance between the feet, metres, and how far the toes turn out. */
  stance?: { width: number; toeOut: number };
  /**
   * The bottom of the hinge: how far the body pitches forward, degrees, and
   * where the pelvis joint ends up, metres, in world space.
   *
   * The pitch and the pelvis are the inputs; the hip, knee and ankle angles
   * are what the solver returns for them, and are recorded here only so the
   * definition says what it plays. Change the placement and re-derive the angles, or leave
   * the bundle alone — `hinge.test.ts` measures that they still agree.
   */
  depth?: HingeDepth;
  tempo?: Tempo;
  muscles?: Partial<MuscleInvolvement>;
  commonErrors?: CommonError[];
  camera?: Partial<CameraRecommendation>;
}

export interface HingeDepth {
  /** Whole-body pitch at the bottom, degrees forward. */
  pitch: number;
  /** Pelvis joint position at the bottom, metres: height, and forward of the feet. */
  pelvis: { y: number; z: number };
  /** The solved hip flexion, knee flexion and ankle angle this produces, degrees. */
  hip: number;
  knee: number;
  ankle: number;
}

/**
 * Height of the pelvis joint above the root, metres: the canonical rig's
 * `pelvis` head. The root sits on the floor between the feet, so this is how far
 * the pitch swings the hips. `hinge.test.ts` holds it to the rig.
 */
export const PELVIS_HEIGHT = 0.95;

/**
 * Where to put the root so the body pitches forward by `pitch` degrees with the
 * pelvis joint landing at `pelvis`.
 *
 * The pelvis sits `PELVIS_HEIGHT` above the root in the root's own frame, and a
 * positive pitch turns up towards forward, so the pelvis lands at
 * `root + (0, H·cos θ, H·sin θ)`. Solving that for the root is the whole
 * derivation.
 */
export function hingeRoot(pitch: number, pelvis: { y: number; z: number }): { y: number; z: number } {
  const theta = (pitch * Math.PI) / 180;
  return {
    y: pelvis.y - PELVIS_HEIGHT * Math.cos(theta),
    z: pelvis.z - PELVIS_HEIGHT * Math.sin(theta),
  };
}

/**
 * To just below the knee, with the hips 17 cm behind the ankles and 5 cm lower
 * than standing. The dumbbells bottom out 48 cm off the floor, level with the
 * top of the shin.
 *
 * Solved, this is 91.7° of hip flexion, 17.6° of knee flexion and 6.9° of
 * plantarflexion, with the shins leaning back 4° — the vertical-shin hinge. On
 * the way down the knees unlock first, peaking at 22° mid-descent as the hips
 * start back, and ease to 17.6° as the hips arrive behind the heels.
 */
const DEPTH: HingeDepth = {
  pitch: 70,
  pelvis: { y: 0.9, z: -0.17 },
  hip: 92,
  knee: -18,
  ankle: -7,
};

/**
 * The arms hang from the shoulders under the load. Standing, the dumbbells rest
 * in front of the thighs, which puts the upper arm a little forward of vertical;
 * at the bottom the trunk has pitched away from the arms, and they stay hanging,
 * which reads as shoulder flexion against the trunk.
 *
 * Measured on the production character, these put the dumbbells 25 mm clear of
 * the thighs at their closest and the dumbbell path within 5 cm of vertical.
 * The upper arms rest against the sides of the chest mid-descent (1.17 mm), as
 * hanging arms do in the squat (1.36 mm) and the press (1.95 mm), and opening
 * them wider buys almost none of it back: 4° more abduction moved it 0.3 mm
 * and pushed the dumbbells a further 16 mm off the legs.
 *
 * Leading the descent with the arms was tried and swings the dumbbells 34 cm
 * out in front of the ankles; untimed, both phases trace the same path.
 */
const ARMS_TOP = bilateralJoints({
  upperarm_l: { x: 13, z: -6 },
  forearm_l: { x: 4, y: -70 },
  hand_l: { z: 4 },
});
const ARMS_BOTTOM = bilateralJoints({
  upperarm_l: { x: 56, z: -9 },
  forearm_l: { x: 4, y: -70 },
  hand_l: { z: 4 },
});

export function hingeFamily(variant: HingeVariant): ExerciseDefinition {
  const depth = variant.depth ?? DEPTH;
  const root = hingeRoot(depth.pitch, depth.pelvis);
  const stance = plantedStance({
    width: variant.stance?.width ?? 0.3,
    toeOut: variant.stance?.toeOut ?? 5,
    // The feet carry the whole body pitching over them, as in the squat.
    tolerance: 0.015,
    // The shins lean forward mid-descent and come back to vertical at the
    // bottom, as a by-product of the hips travelling back; a foot riding along
    // with them would tip its toes into the floor.
    flat: true,
    // Straight ahead of the knee. A knee bent 2° standing has no bend plane of
    // its own to follow.
    kneePole: vec3(-0.04, 0.5, 1.5),
  });

  return {
    id: variant.id,
    name: variant.name,
    clipName: variant.clipName,
    category: 'legs',
    description: variant.description,

    equipment: { required: ['dumbbell'], instances: handDumbbells(variant.mass ?? 16) },

    startPose: {
      label: 'Standing tall',
      joints: {
        ...ARMS_TOP,
        spine_01: { x: 0 },
        spine_02: { x: 0 },
        spine_03: { x: 0 },
        neck: { x: 0 },
      },
    },

    peakPose: {
      label: 'Hinged',
      joints: {
        ...ARMS_BOTTOM,
        // The spine keeps its standing shape; the neck lifts the head only as
        // far as keeping it in line with the back, eyes on the floor ahead.
        spine_01: { x: 0 },
        spine_02: { x: 0 },
        spine_03: { x: 2 },
        neck: { x: -12 },
        head: { x: -6 },
      },
      root: { position: { y: root.y, z: root.z }, rotation: { x: depth.pitch } },
    },

    jointTargets: [
      ...bilateralJointTarget({
        bone: 'thigh_l', axis: 'x', start: 0, peak: depth.hip, role: 'prime',
        range: { min: -5, max: 110 },
      }),
      // Soft, not locked, and not a squat: the knee unlocks and stays there.
      ...bilateralJointTarget({
        bone: 'shin_l', axis: 'x', start: -2, peak: depth.knee, role: 'stabilise',
        range: { min: -35, max: 0 },
      }),
      ...bilateralJointTarget({
        bone: 'foot_l', axis: 'x', start: 0, peak: depth.ankle, role: 'stabilise',
      }),
    ],

    phases: [
      { id: 'eccentric', label: 'Hinge back', to: 'peak', easing: 'lift', contraction: 'eccentric' },
      { id: 'bottom', label: 'Stretch', to: 'peak', easing: 'hold', contraction: 'isometric' },
      { id: 'concentric', label: 'Drive the hips through', to: 'start', easing: 'lift', contraction: 'concentric' },
      { id: 'top', label: 'Stand tall', to: 'start', easing: 'hold', contraction: 'isometric' },
    ],

    // Slow on the way down, where the hamstrings lengthen under load.
    tempo: variant.tempo ?? { eccentric: 2.5, pauseStretched: 0.4, concentric: 1.6, pauseContracted: 0.5 },

    // 0.49 m apart as measured: the dumbbells ride the front-outside of the
    // thighs, which is what the 6-9° of abduction that clears the chest costs.
    hands: { grip: 'dumbbell', orientation: 'pronated', closure: 0.85, width: 0.49 },
    feet: stance.feet,
    locks: stance.locks,
    // The body tips about its hips, so the hips travel in a straight line from
    // standing to the bottom, back and barely down, as a coach describes them.
    rootPivot: vec3(0, PELVIS_HEIGHT, 0),

    muscles: {
      primary: ['hamstrings', 'gluteus'],
      secondary: ['erector_lower', 'erector_mid'],
      stabilisers: [
        'forearm_flexors',
        'trapezius_upper',
        'rectus_abdominis',
        'obliques',
        'quadriceps',
        'hip_adductors',
      ],
      ...variant.muscles,
    },

    technique: [
      ...stance.technique,
      ...heelDown(),
      {
        kind: 'jointAngle',
        id: 'neutral_spine',
        label: 'Lower back stays neutral, not rounded',
        bone: 'spine_01',
        axis: 'x',
        min: -4,
        max: 8,
        severity: 'error',
      },
      {
        kind: 'jointAngle',
        id: 'upper_back_flat',
        label: 'Upper back stays flat, not hunched',
        bone: 'spine_03',
        axis: 'x',
        min: -4,
        max: 8,
        severity: 'error',
      },
      {
        kind: 'segmentAngle',
        id: 'hinge_depth',
        label: 'Torso hinges well forward at the bottom',
        bone: 'spine_02',
        reference: 'vertical',
        min: 55,
        max: 85,
        phases: ['bottom'],
        severity: 'error',
      },
      // The rule that keeps a hinge a hinge. A squat must take the hips below
      // this line; a hinge must keep them above it.
      {
        kind: 'relativePosition',
        id: 'hips_high',
        label: 'Hips stay high, well above the knees',
        point: { bone: 'pelvis' },
        relativeTo: { bone: 'shin_l' },
        axis: 'y',
        min: 0.3,
        severity: 'error',
      },
      {
        kind: 'relativePosition',
        id: 'hips_back',
        label: 'Hips travel back behind the heels',
        point: { bone: 'pelvis' },
        relativeTo: { bone: 'foot_l' },
        axis: 'z',
        // 15.5 cm behind the ankles at the bottom.
        max: -0.1,
        phases: ['bottom'],
        severity: 'error',
      },
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'soft_knee_l',
        label: 'Left knee stays soft: unlocked, but not squatting',
        bone: 'shin_l',
        axis: 'x',
        min: -30,
        max: -1,
        severity: 'error',
      }),
      ...bilateralRule({
        kind: 'segmentAngle',
        id: 'shin_vertical_l',
        label: 'Left shin stays close to vertical',
        bone: 'shin_l',
        reference: 'vertical',
        max: 15,
      }),
      // The load stays over the feet: the dumbbells travel down the legs rather
      // than swinging out in front, where they would pull the back round.
      ...bilateralRule({
        kind: 'relativePosition',
        id: 'dumbbells_close_l',
        label: 'Left dumbbell stays close to the legs',
        point: { bone: 'hand_l', along: 1 },
        relativeTo: { bone: 'foot_l' },
        axis: 'z',
        // Fingertips 14-19 cm ahead of the ankle through the whole repetition:
        // over the front of the foot, which is where a handle held in front of
        // the thighs has to be. 3 cm of drift beyond that fails.
        min: -0.05,
        max: 0.22,
        severity: 'error',
      }),
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'arms_straight_l',
        label: 'Left arm stays long, not rowing',
        bone: 'forearm_l',
        axis: 'x',
        max: 15,
      }),
      evenSides({
        id: 'dumbbells_aligned',
        label: 'Both dumbbells stay level with one another',
        point: { bone: 'hand_l', along: 1 },
        tolerance: 0.03,
      }),
    ],

    commonErrors: [
      {
        id: 'rounding',
        label: 'Rounding the back',
        description: 'The lower back flexes to reach further instead of the hips travelling back.',
        ruleId: 'neutral_spine',
        correction: 'Stop where the hamstrings run out of length, before the back starts to round.',
      },
      {
        id: 'squatting',
        label: 'Turning it into a squat',
        description: 'The knees bend and the hips drop, so the thighs take the work off the hamstrings.',
        ruleId: 'hips_high',
        correction: 'Keep the knees soft and still; push the hips back rather than down.',
      },
      {
        id: 'bar_drift',
        label: 'Letting the weights drift forward',
        description: 'The dumbbells swing away from the legs and drag the trunk forward.',
        ruleId: 'dumbbells_close_l',
        correction: 'Keep the dumbbells brushing the thighs all the way down and up.',
      },
      {
        id: 'shallow_hinge',
        label: 'Hinging too little',
        description: 'Stopping with the torso nearly upright, so the hamstrings never lengthen.',
        ruleId: 'hinge_depth',
        correction: 'Push the hips back until the torso is well forward and the hamstrings are stretched.',
      },
      {
        id: 'toes_rocking',
        label: 'Rocking onto the toes',
        description: 'Weight shifts forward and the heels lift as the weights descend.',
        ruleId: 'heel_down_l',
        correction: 'Keep the weight through the middle of the foot and the heels down.',
      },
      ...(variant.commonErrors ?? []),
    ],

    breathing: {
      inhale: 'eccentric',
      exhale: 'concentric',
      cue: 'Breathe in and brace before hinging back, out as the hips come through.',
    },

    camera: {
      preset: 'right',
      position: vec3(2.8, 1.0, 0.6),
      target: vec3(0, 0.8, 0.05),
      fov: 40,
      note: 'Side view shows the hips travelling back, the flat back and the dumbbell path together.',
      ...variant.camera,
    },
  };
}
