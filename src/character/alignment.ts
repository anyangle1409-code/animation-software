import { Euler, Matrix4, Quaternion, Vector3 } from 'three';
import type { Bone } from 'three';

/**
 * A reviewer's correction to one character bone: a rotation in the bone's own
 * frame (degrees) and a move in its parent's frame (centimetres).
 *
 * Corrections sit on top of whatever drives the character — the retarget
 * transfer or the canonical bind — so they can be tried on a playing animation
 * and removed without touching the model file. A correction moves the bone,
 * and therefore everything skinned to it and every bone below it.
 */
export interface BoneCorrection {
  rx: number;
  ry: number;
  rz: number;
  tx: number;
  ty: number;
  tz: number;
}

export type BoneCorrections = Record<string, BoneCorrection>;

export const ZERO_CORRECTION: BoneCorrection = { rx: 0, ry: 0, rz: 0, tx: 0, ty: 0, tz: 0 };

export const isZeroCorrection = (c: BoneCorrection | undefined): boolean =>
  !c || (c.rx === 0 && c.ry === 0 && c.rz === 0 && c.tx === 0 && c.ty === 0 && c.tz === 0);

const DEG = Math.PI / 180;
const CM = 0.01;

interface Applied {
  offset: Vector3;
  rotation: Quaternion;
  /** The bone's local transform as this function left it. */
  position: Vector3;
  quaternion: Quaternion;
  matrix: Matrix4;
}

/**
 * Applies corrections to a set of bones, once per frame, after the driver.
 *
 * Driven bones are rewritten by the driver every frame, but bones it does not
 * drive (helpers, unmapped bones, unanimated positions) keep last frame's
 * transform — so a correction applied naively would accumulate. Each bone
 * remembers exactly what was left on it; if the driver has not touched it
 * since, the previous correction is taken off before the new one goes on.
 */
export class BoneCorrector {
  private applied = new Map<Bone, Applied>();
  private euler = new Euler();
  private q = new Quaternion();
  private inv = new Quaternion();
  private p = new Vector3();
  private s = new Vector3();

  apply(bones: Iterable<Bone>, corrections: BoneCorrections, root?: { updateMatrixWorld: (force?: boolean) => void }): void {
    let touched = false;
    for (const bone of bones) {
      const correction = corrections[bone.name];
      const previous = this.applied.get(bone);
      if (isZeroCorrection(correction) && !previous) continue;
      touched = true;

      if (bone.matrixAutoUpdate) {
        if (previous && bone.position.equals(previous.position)) bone.position.sub(previous.offset);
        if (previous && bone.quaternion.equals(previous.quaternion)) {
          bone.quaternion.multiply(this.inv.copy(previous.rotation).invert());
        }
      } else if (previous && bone.matrix.equals(previous.matrix)) {
        bone.matrix.decompose(this.p, this.q, this.s);
        this.p.sub(previous.offset);
        this.q.multiply(this.inv.copy(previous.rotation).invert());
        bone.matrix.compose(this.p, this.q, this.s);
      }

      if (isZeroCorrection(correction)) {
        if (bone.matrixAutoUpdate) bone.updateMatrix();
        this.applied.delete(bone);
        continue;
      }
      const c = correction!;
      const offset = new Vector3(c.tx * CM, c.ty * CM, c.tz * CM);
      const rotation = new Quaternion().setFromEuler(this.euler.set(c.rx * DEG, c.ry * DEG, c.rz * DEG, 'XYZ'));
      if (bone.matrixAutoUpdate) {
        bone.position.add(offset);
        bone.quaternion.multiply(rotation);
        bone.updateMatrix();
      } else {
        bone.matrix.decompose(this.p, this.q, this.s);
        this.p.add(offset);
        this.q.multiply(rotation);
        bone.matrix.compose(this.p, this.q, this.s);
      }
      this.applied.set(bone, {
        offset,
        rotation,
        position: bone.position.clone(),
        quaternion: bone.quaternion.clone(),
        matrix: bone.matrix.clone(),
      });
    }
    if (touched) root?.updateMatrixWorld(true);
  }

  /** Forget what was applied (the bones are about to be rebuilt). */
  reset(): void {
    this.applied.clear();
  }
}

/** Corrections as shareable text: only bones that actually carry one. */
export function serializeCorrections(corrections: BoneCorrections): string {
  const out: BoneCorrections = {};
  for (const [name, c] of Object.entries(corrections)) if (!isZeroCorrection(c)) out[name] = c;
  return JSON.stringify(out, null, 1);
}

/** Parses shared corrections, rejecting anything that is not finite numbers per bone. */
export function parseCorrections(text: string): BoneCorrections {
  const raw = JSON.parse(text) as unknown;
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) throw new Error('Expected an object of bone corrections.');
  const out: BoneCorrections = {};
  for (const [name, value] of Object.entries(raw as Record<string, unknown>)) {
    const v = (value ?? {}) as Record<string, unknown>;
    const c = { ...ZERO_CORRECTION };
    for (const key of Object.keys(ZERO_CORRECTION) as (keyof BoneCorrection)[]) {
      const n = v[key] ?? 0;
      if (typeof n !== 'number' || !Number.isFinite(n)) throw new Error(`Bone "${name}": ${key} is not a number.`);
      c[key] = n;
    }
    out[name] = c;
  }
  return out;
}
