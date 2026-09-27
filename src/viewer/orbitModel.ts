import { clamp } from '../core/math';
import { HgVec3 } from '../core/linearMath';

export interface HgOrbitConfig {
  minDistance: number;
  maxDistance: number;
  minPolarAngle: number;
  maxPolarAngle: number;
  damping: number;
  rotateSpeed: number;
}

export interface HgOrbitSnapshot {
  position: HgVec3;
  target: HgVec3;
  distance: number;
  yaw: number;
  polar: number;
}

const DEFAULT: HgOrbitConfig = {
  minDistance: 0.6,
  maxDistance: 12,
  minPolarAngle: 0.01,
  maxPolarAngle: Math.PI - 0.01,
  damping: 0.12,
  rotateSpeed: 1,
};

/**
 * Renderer-independent orbit state.
 *
 * +Y is up. yaw=0 is +Z. polar is measured down from +Y.
 * The adapter owns pointer events and writes the returned camera position.
 */
export class HgOrbitModel {
  readonly target = new HgVec3();
  readonly config: HgOrbitConfig;

  private yaw = 0;
  private polar = Math.PI / 2;
  private distance = 3;
  private goalYaw = 0;
  private goalPolar = Math.PI / 2;
  private goalDistance = 3;

  constructor(
    position: HgVec3,
    target: HgVec3,
    config: Partial<HgOrbitConfig> = {},
  ) {
    this.config = { ...DEFAULT, ...config };
    this.sync(position, target);
  }

  sync(position: HgVec3, target: HgVec3): this {
    this.target.copy(target);
    const offset = position.clone().sub(target);
    const rawDistance = offset.length();
    const distance = clamp(
      rawDistance > 1e-12 ? rawDistance : this.config.minDistance,
      this.config.minDistance,
      this.config.maxDistance,
    );

    this.distance = this.goalDistance = distance;
    this.yaw = this.goalYaw = Math.atan2(offset.x, offset.z);
    this.polar = this.goalPolar = clamp(
      rawDistance > 1e-12
        ? Math.acos(clamp(offset.y / rawDistance, -1, 1))
        : Math.PI / 2,
      this.config.minPolarAngle,
      this.config.maxPolarAngle,
    );
    return this;
  }

  setTarget(target: HgVec3): this {
    this.target.copy(target);
    return this;
  }

  rotatePixels(deltaX: number, deltaY: number, viewportHeight: number): this {
    if (!Number.isFinite(viewportHeight) || viewportHeight <= 0) return this;
    const radiansPerPixel =
      (Math.PI * 2 * this.config.rotateSpeed) / viewportHeight;
    this.goalYaw -= deltaX * radiansPerPixel;
    this.goalPolar = clamp(
      this.goalPolar - deltaY * radiansPerPixel,
      this.config.minPolarAngle,
      this.config.maxPolarAngle,
    );
    return this;
  }

  /** factor > 1 zooms out; factor < 1 zooms in. */
  zoomByFactor(factor: number): this {
    if (!Number.isFinite(factor) || factor <= 0) return this;
    this.goalDistance = clamp(
      this.goalDistance * factor,
      this.config.minDistance,
      this.config.maxDistance,
    );
    return this;
  }

  step(deltaSeconds: number): HgOrbitSnapshot {
    const damping = clamp(this.config.damping, 0, 1);
    const frames = Math.max(0, deltaSeconds) * 60;
    const blend =
      damping >= 1 ? 1 : damping <= 0 ? 1 : 1 - Math.pow(1 - damping, frames);

    this.yaw += (this.goalYaw - this.yaw) * blend;
    this.polar += (this.goalPolar - this.polar) * blend;
    this.distance += (this.goalDistance - this.distance) * blend;

    return this.snapshot();
  }

  snapshot(): HgOrbitSnapshot {
    const sinPolar = Math.sin(this.polar);
    const position = new HgVec3(
      this.target.x + this.distance * sinPolar * Math.sin(this.yaw),
      this.target.y + this.distance * Math.cos(this.polar),
      this.target.z + this.distance * sinPolar * Math.cos(this.yaw),
    );

    return {
      position,
      target: this.target.clone(),
      distance: this.distance,
      yaw: this.yaw,
      polar: this.polar,
    };
  }

  goal(): Pick<HgOrbitSnapshot, 'distance' | 'yaw' | 'polar'> {
    return {
      distance: this.goalDistance,
      yaw: this.goalYaw,
      polar: this.goalPolar,
    };
  }
}
