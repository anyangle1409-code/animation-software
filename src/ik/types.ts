import type { BoneName } from '../rig/boneNames';
import type { Vec3 } from '../rig/types';

/** A three-joint chain solved analytically: hip/knee/ankle, shoulder/elbow/wrist. */
export interface IKChain {
  id: IKChainId;
  label: string;
  /** Upper bone — the one whose head is the chain's anchor. */
  root: BoneName;
  /** Middle bone — the hinge (elbow or knee). */
  mid: BoneName;
  /** End bone, whose *head* is the effector the target positions. */
  end: BoneName;
  /** Where the pole target sits by default, relative to the chain's rest plane. */
  poleLabel: string;
}

export type IKChainId = 'arm_l' | 'arm_r' | 'leg_l' | 'leg_r';

export interface IKGoal {
  chain: IKChainId;
  enabled: boolean;
  /** World-space position for the chain's end effector. */
  target: Vec3;
  /** World-space pole position; controls which way the elbow or knee points. */
  pole: Vec3;
  /**
   * Optional world-space orientation for the end bone (hand or foot), given as
   * the direction its +Y axis should point and its forward reference. Used to
   * keep a hand aligned to a bar, or a foot flat on the floor.
   */
  endAim?: { direction: Vec3; forward?: Vec3 };
  /**
   * Stand the end bone on its tail instead of its head: `anchor` is where the
   * ball of the foot must be, and the heel's height is solved so the ankle
   * holds `ankle` degrees. See `EffectorLock.onBall`.
   */
  ball?: { anchor: Vec3; ankle: number; toeOut: number };
}

export interface IKResult {
  chain: IKChainId;
  /** Distance in metres between the effector and its target after solving. */
  error: number;
  /** False when joint limits or bone lengths stopped the chain reaching. */
  reached: boolean;
  /** True when the target was outside the chain's physical reach. */
  overExtended: boolean;
}
