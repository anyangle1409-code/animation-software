import type { BoneName } from '../rig/boneNames';
import type { IKChainId } from '../ik/types';
import type { Vec3 } from '../rig/types';

/** A point on the body: a bone, optionally offset along or away from it. */
export interface PointRef {
  bone: BoneName;
  /** 0 = the bone's head (its joint), 1 = its tail. Defaults to 0. */
  along?: number;
  /** Extra offset in the bone's local frame, metres. */
  offset?: Vec3;
}

export type ReferenceDirection = 'vertical' | 'forward' | 'lateral';

/**
 * Technique rules are data, not code. They live on the exercise definition,
 * are shown in the editor, and are evaluated against every frame of the
 * generated animation so bad form is reported rather than silently exported.
 */
export type TechniqueRule =
  | {
      kind: 'jointAngle';
      id: string;
      label: string;
      severity?: Severity;
      bone: BoneName;
      axis: 'x' | 'y' | 'z';
      /** Degrees. */
      min?: number;
      max?: number;
      phases?: string[];
    }
  | {
      kind: 'segmentAngle';
      id: string;
      label: string;
      severity?: Severity;
      /** Angle of this bone's direction against a world reference, in degrees. */
      bone: BoneName;
      reference: ReferenceDirection;
      min?: number;
      max?: number;
      phases?: string[];
    }
  | {
      kind: 'stationary';
      id: string;
      label: string;
      severity?: Severity;
      point: PointRef;
      /** Maximum drift from the point's position at the start of the clip, metres. */
      tolerance: number;
      phases?: string[];
    }
  | {
      kind: 'distance';
      id: string;
      label: string;
      severity?: Severity;
      from: PointRef;
      to: PointRef;
      /** Metres. */
      min?: number;
      max?: number;
      /** Measure only along one world axis instead of true distance. */
      axis?: 'x' | 'y' | 'z';
      phases?: string[];
    }
  | {
      kind: 'relativePosition';
      id: string;
      label: string;
      severity?: Severity;
      point: PointRef;
      relativeTo: PointRef;
      axis: 'x' | 'y' | 'z';
      /** Metres, signed, in world axes. */
      min?: number;
      max?: number;
      phases?: string[];
    }
  | {
      kind: 'symmetry';
      id: string;
      label: string;
      severity?: Severity;
      /** Left/right points that should mirror one another. */
      left: PointRef;
      right: PointRef;
      tolerance: number;
      phases?: string[];
    }
  | {
      kind: 'alignment';
      id: string;
      label: string;
      severity?: Severity;
      /** Three points that should stay on one line — head, hips, ankles. */
      points: [PointRef, PointRef, PointRef];
      /** Maximum perpendicular deviation of the middle point, metres. */
      tolerance: number;
      phases?: string[];
    };

export type Severity = 'error' | 'warning';

export interface RuleViolation {
  ruleId: string;
  label: string;
  severity: Severity;
  /** Human-readable explanation, e.g. "Torso leaning 18° (limit 10°)". */
  message: string;
  /** How far outside the rule, in the rule's own units. */
  amount: number;
  time: number;
}

/**
 * How an effector is held in place. Locks are resolved into IK goals before
 * solving, which is what stops feet sliding and keeps hands on a bar.
 */
export interface EffectorLock {
  id: string;
  chain: IKChainId;
  mode: LockMode;
  /** Fixed world position, for `world` and `floor` locks. */
  position?: Vec3;
  /** Equipment instance and socket, for `equipment` locks. */
  equipmentId?: string;
  socket?: string;
  /** Where the elbow or knee should point. */
  pole?: Vec3;
  /** Orientation for the hand or foot while locked. */
  aim?: { direction: Vec3; forward?: Vec3 };
  enabled: boolean;
}

export type LockMode =
  /** Hold the effector at a fixed world point. */
  | 'world'
  /** Hold it on the floor plane at its starting X/Z. */
  | 'floor'
  /** Rigidly follow an equipment socket. */
  | 'equipment';
