import type { BoneName } from '../rig/boneNames';
import type { Vec3 } from '../rig/types';
import type { EffectorLock, TechniqueRule } from '../constraints/types';
import type { EquipmentInstance, EquipmentKind } from '../equipment/types';
import type { MuscleGroupId } from '../muscles/groups';
import type { IKChainId } from '../ik/types';
import type { CameraPresetId } from '../viewer/cameraTypes';

/**
 * The complete, structured description of one exercise.
 *
 * This is the only place an exercise is described. The animation generator, the
 * technique checker, the muscle overlay, the camera and every exporter read
 * from here — nothing about an exercise is spread across UI components, and the
 * same object is what Home Gym PT will eventually consume.
 */
export interface ExerciseDefinition {
  id: string;
  name: string;
  /** Short slug used for exported animation clip names, e.g. `bicep_curl`. */
  clipName: string;
  category: ExerciseCategory;
  description?: string;

  equipment: ExerciseEquipment;

  /** Pose at the start of a repetition, and at the peak of the movement. */
  startPose: PoseSpec;
  peakPose: PoseSpec;

  phases: MovementPhase[];
  tempo: Tempo;

  /** Joints that do the work, with the range each moves through. */
  jointTargets: JointTarget[];

  hands: HandSpec;
  feet: FootSpec;

  /** Effectors held in place for the whole repetition. */
  locks: EffectorLock[];

  muscles: MuscleInvolvement;
  technique: TechniqueRule[];
  commonErrors: CommonError[];
  breathing: BreathingCue;
  camera: CameraRecommendation;
}

export type ExerciseCategory =
  | 'upper_push'
  | 'upper_pull'
  | 'arms'
  | 'legs'
  | 'core'
  | 'full_body';

export interface ExerciseEquipment {
  required: EquipmentKind[];
  /** Instances placed in the scene, with their attachments. */
  instances: EquipmentInstance[];
}

/**
 * A pose authored in degrees, optionally with IK targets. Degrees because that
 * is how a coach describes a position, and because it keeps the definition
 * readable in JSON.
 */
export interface PoseSpec {
  label: string;
  /** Bone rotations in degrees, in the bone's own frame. */
  joints: Partial<Record<BoneName, Partial<Vec3>>>;
  /** Root placement, metres and degrees. */
  root?: { position?: Partial<Vec3>; rotation?: Partial<Vec3> };
  /** World-space IK targets that override forward kinematics for a limb. */
  ik?: Partial<Record<IKChainId, PoseIKTarget>>;
}

export interface PoseIKTarget {
  target: Vec3;
  pole: Vec3;
  aim?: { direction: Vec3; forward?: Vec3 };
}

/**
 * Optional timing for one bone inside a movement phase. Values are normalised
 * to the phase: 0 is the phase start and 1 is the phase end. The bone remains at
 * the source pose until `delay`, then reaches the destination by `finish`.
 *
 * This is intentionally per bone rather than per axis. Secondary body motion —
 * a shoulder settling late in a curl, for example — should stay anatomically
 * coherent instead of moving flexion and abduction on unrelated clocks.
 */
export interface PhaseJointTiming {
  /** Normalised phase progress before this bone begins moving. Default 0. */
  delay?: number;
  /** Normalised phase progress by which this bone has arrived. Default 1. */
  finish?: number;
  /** Optional curve for this bone; defaults to the phase easing. */
  easing?: EasingKind;
}

/**
 * One segment of a repetition. Phases carry the tempo, so a 2-1-2 cadence is
 * data rather than a hard-coded curve.
 */
export interface MovementPhase {
  id: string;
  label: string;
  /** Which authored pose this phase ends at. */
  to: 'start' | 'peak';
  /** Seconds. Overrides the tempo entry of the same name when present. */
  duration?: number;
  /** How the movement accelerates through the phase. */
  easing: EasingKind;
  contraction: 'eccentric' | 'concentric' | 'isometric';
  /**
   * Per-bone timing overrides for secondary motion. Prime movers normally omit
   * this and use the phase curve unchanged.
   */
  jointTiming?: Partial<Record<BoneName, PhaseJointTiming>>;
}

export type EasingKind =
  | 'linear'
  | 'easeIn'
  | 'easeOut'
  | 'easeInOut'
  /** Resistance-training feel: decelerate into the peak, accelerate out of it. */
  | 'lift'
  /** Slow through the mid-range sticking point. */
  | 'grind'
  | 'hold';

export interface Tempo {
  /** Lowering phase, seconds. */
  eccentric: number;
  /** Pause at the stretched position, seconds. */
  pauseStretched: number;
  /** Lifting phase, seconds. */
  concentric: number;
  /** Pause at the contracted position, seconds. */
  pauseContracted: number;
}

export interface JointTarget {
  bone: BoneName;
  axis: 'x' | 'y' | 'z';
  /** Degrees at the start pose. */
  start: number;
  /** Degrees at the peak pose. */
  peak: number;
  /** Optional tighter range than the joint's anatomical limit, degrees. */
  range?: { min: number; max: number };
  role: 'prime' | 'support' | 'stabilise';
}

export interface HandSpec {
  /** Distance between the hands, metres. */
  width?: number;
  grip: GripKind;
  /** Where the palms face at the start of the movement. */
  orientation: 'neutral' | 'supinated' | 'pronated' | 'rotating';
  /** How tightly the fingers close, 0 open to 1 fully closed. */
  closure: number;
}

export type GripKind = 'none' | 'dumbbell' | 'bar' | 'floor' | 'handle' | 'rope';

export interface FootSpec {
  /** Distance between the feet, metres. */
  width: number;
  /** Toe-out angle in degrees. */
  toeOut: number;
  planted: boolean;
}

export interface MuscleInvolvement {
  primary: MuscleGroupId[];
  secondary: MuscleGroupId[];
  stabilisers: MuscleGroupId[];
}

export interface CommonError {
  id: string;
  label: string;
  description: string;
  /** Technique rule that detects this error, when one exists. */
  ruleId?: string;
  correction: string;
}

export interface BreathingCue {
  inhale: string;
  exhale: string;
  cue: string;
}

export interface CameraRecommendation {
  preset: CameraPresetId;
  /** Optional explicit camera, saved with the exercise. */
  position?: Vec3;
  target?: Vec3;
  fov?: number;
  note?: string;
}

/** Total time of one repetition. */
export const repetitionDuration = (exercise: ExerciseDefinition): number =>
  exercise.phases.reduce(
    (total, phase) => total + (phase.duration ?? tempoDuration(exercise.tempo, phase)),
    0,
  );

export function tempoDuration(tempo: Tempo, phase: MovementPhase): number {
  if (phase.contraction === 'concentric') return tempo.concentric;
  if (phase.contraction === 'eccentric') return tempo.eccentric;
  return phase.to === 'peak' ? tempo.pauseContracted : tempo.pauseStretched;
}
