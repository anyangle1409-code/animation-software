import type { BoneName } from '../rig/boneNames';
import type { Axis } from '../rig/types';
import type { HandSpec } from '../exercises/types';
import type { CameraPresetId } from '../viewer/cameraTypes';
import type { PointRef } from '../constraints/types';

export type ReferenceFamilyId = 'curl' | 'overhead_press' | 'squat' | 'lunge' | 'hinge' | 'row' | 'vertical_pull' | 'horizontal_press' | 'raise';
export type ReferenceScale = 'standingHeight' | 'shoulderWidth' | 'armLength' | 'torsoLength';
/** A reference landmark: shorthand bone name or the technique engine's full PointRef. */
export type ReferencePoint = BoneName | PointRef;
export type ReferenceStatus = 'draft' | 'certified';
export type ReferenceCheckStatus = 'pass' | 'fail' | 'skip';
export type ReferenceSeverity = 'error' | 'warning';

export interface NumericEnvelope {
  min?: number;
  max?: number;
}

interface ReferenceCheckBase {
  id: string;
  label: string;
  severity?: ReferenceSeverity;
  /** Restrict this check to samples whose generated clip phase id is listed. */
  phases?: string[];
}

/** A bone-local Euler angle, measured in degrees from the generated clip. */
export interface JointEnvelopeCheck extends ReferenceCheckBase {
  kind: 'jointEnvelope';
  bone: BoneName;
  axis: Axis;
  envelope: NumericEnvelope;
}

/** Peak-to-peak excursion of one bone-local Euler axis over the selected samples. */
export interface JointExcursionCheck extends ReferenceCheckBase {
  kind: 'jointExcursion';
  bone: BoneName;
  axis: Axis;
  envelope: NumericEnvelope;
}

/** Root Euler angle, in degrees. */
export interface RootEnvelopeCheck extends ReferenceCheckBase {
  kind: 'rootEnvelope';
  axis: Axis;
  envelope: NumericEnvelope;
}

/** Root world position on one axis, optionally normalized by body size. */
export interface RootPositionEnvelopeCheck extends ReferenceCheckBase {
  kind: 'rootPositionEnvelope';
  axis: Axis;
  envelope: NumericEnvelope;
  normalizeBy?: ReferenceScale;
}

/** World landmark position relative to another joint. */
export interface RelativeLandmarkEnvelopeCheck extends ReferenceCheckBase {
  kind: 'relativeLandmarkEnvelope';
  point: ReferencePoint;
  relativeTo: ReferencePoint;
  axis: Axis;
  envelope: NumericEnvelope;
  normalizeBy?: ReferenceScale;
}

/** Angle of a bone segment to a world axis. Zero means aligned. */
export interface SegmentAngleEnvelopeCheck extends ReferenceCheckBase {
  kind: 'segmentAngleEnvelope';
  bone: BoneName;
  worldAxis: Axis;
  envelope: NumericEnvelope;
}

/** Maximum world-space drift from the first selected sample. */
export interface LandmarkStationaryCheck extends ReferenceCheckBase {
  kind: 'landmarkStationary';
  bone: ReferencePoint;
  tolerance: number;
  normalizeBy?: ReferenceScale;
}

/** Distance between two landmarks, optionally on one world axis. */
export interface LandmarkDistanceEnvelopeCheck extends ReferenceCheckBase {
  kind: 'landmarkDistanceEnvelope';
  from: ReferencePoint;
  to: ReferencePoint;
  axis?: Axis;
  envelope: NumericEnvelope;
  normalizeBy?: ReferenceScale;
}

/**
 * Left/right rotational agreement. Flexion (x) keeps its sign under mirroring;
 * axial rotation (y) and ab/adduction (z) reverse their sign.
 */
export interface BilateralSymmetryCheck extends ReferenceCheckBase {
  kind: 'bilateralSymmetry';
  left: BoneName;
  right: BoneName;
  axis: Axis;
  toleranceDeg: number;
}

/** The semantic phase order expected from a movement family. */
export interface PhaseOrderCheck extends ReferenceCheckBase {
  kind: 'phaseOrder';
  order: string[];
}

/**
 * A world-space landmark should move monotonically through one phase. This is
 * useful for attached equipment too: a dumbbell rigidly held by the hand should
 * not reverse direction mid-concentric or mid-eccentric.
 */
export interface LandmarkMonotonicCheck extends ReferenceCheckBase {
  kind: 'landmarkMonotonic';
  bone: ReferencePoint;
  axis: Axis;
  phase: string;
  direction: 'increasing' | 'decreasing';
  /** Maximum tolerated backwards step between adjacent samples, metres. */
  tolerance: number;
}

export type ReferenceCheckSpec =
  | JointEnvelopeCheck
  | JointExcursionCheck
  | RootEnvelopeCheck
  | RootPositionEnvelopeCheck
  | RelativeLandmarkEnvelopeCheck
  | SegmentAngleEnvelopeCheck
  | LandmarkStationaryCheck
  | LandmarkDistanceEnvelopeCheck
  | BilateralSymmetryCheck
  | PhaseOrderCheck
  | LandmarkMonotonicCheck;

export interface ReferenceApplicability {
  handOrientation?: HandSpec['orientation'];
  support?: 'standing' | 'seated' | 'incline' | 'hanging' | 'floor';
}

export interface ReferenceReviewView {
  id: string;
  label: string;
  preset: CameraPresetId;
  /** Optional semantic crop target for a future local capture renderer. */
  target?: 'full_body' | 'upper_body' | 'hands' | 'shoulders' | 'feet';
}

export interface ReferenceSpec {
  schemaVersion: 1;
  id: string;
  referenceVersion: number;
  family: ReferenceFamilyId;
  status: ReferenceStatus;
  applicability: ReferenceApplicability;
  /**
   * Human-readable source-of-truth note. These values must be reviewed
   * independently; they must not be populated by reading the family builder at
   * runtime.
   */
  provenance: string;
  /** Family-owned review evidence to capture locally. */
  reviewViews?: ReferenceReviewView[];
  checks: ReferenceCheckSpec[];
}

export interface ReferenceCheckResult {
  id: string;
  label: string;
  kind: ReferenceCheckSpec['kind'];
  severity: ReferenceSeverity;
  status: ReferenceCheckStatus;
  detail: string;
  /** Worst/deciding measurement in the check's own units. */
  measured?: number;
  expected?: string;
  worstTime?: number;
}

export interface ReferenceReport {
  referenceId: string;
  referenceVersion: number;
  exerciseId: string;
  passed: boolean;
  checks: ReferenceCheckResult[];
  failed: string[];
  skipped: string[];
  samples: number;
}
