import { HgQuat, HgVec3 } from '../core/linearMath';
import type { HgRay } from './transformGizmoMath';
import { hgAxisTranslationDelta, hgSignedRotationAngle } from './transformGizmoMath';

export type HgTransformMode = 'translate' | 'rotate';

export interface HgTransformResult {
  position: HgVec3;
  quaternion: HgQuat;
}

/** One immutable drag baseline, evaluated from pointer rays in world space. */
export class HgTransformDrag {
  private readonly pivot: HgVec3;
  private readonly startPosition: HgVec3;
  private readonly startQuaternion: HgQuat;

  constructor(
    private readonly mode: HgTransformMode,
    private readonly axis: HgVec3,
    private readonly startRay: HgRay,
    startPosition: HgVec3,
    startQuaternion: HgQuat,
  ) {
    this.pivot = startPosition.clone();
    this.startPosition = startPosition.clone();
    this.startQuaternion = startQuaternion.clone();
  }

  update(currentRay: HgRay): HgTransformResult | null {
    if (this.mode === 'translate') {
      const delta = hgAxisTranslationDelta(
        this.startRay,
        currentRay,
        this.pivot,
        this.axis,
      );
      if (delta === null) return null;
      return {
        position: this.startPosition.clone().addScaledVector(this.axis, delta),
        quaternion: this.startQuaternion.clone(),
      };
    }

    const angle = hgSignedRotationAngle(
      this.startRay,
      currentRay,
      this.pivot,
      this.axis,
    );
    if (angle === null) return null;
    return {
      position: this.startPosition.clone(),
      quaternion: new HgQuat()
        .setFromAxisAngle(this.axis, angle)
        .multiply(this.startQuaternion)
        .normalize(),
    };
  }
}
