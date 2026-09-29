import type { HgPrimitiveGeometryData } from './primitiveGeometry';
import { HgObject3D } from './sceneGraph';

export type HgRgba = [number, number, number, number];
export type HgPrimitiveShading = 'lit' | 'flat';

const channel = (value: string): number => Number.parseInt(value, 16) / 255;

/** Convert CSS-style #rgb / #rrggbb colours into renderer-neutral linear inputs. */
export function hgRgbaFromHex(hex: string, alpha = 1): HgRgba {
  if (!Number.isFinite(alpha) || alpha < 0 || alpha > 1) {
    throw new Error('Mesh alpha must be between 0 and 1');
  }
  const value = hex.trim();
  if (/^#[0-9a-f]{3}$/i.test(value)) {
    return [
      channel(value[1] + value[1]),
      channel(value[2] + value[2]),
      channel(value[3] + value[3]),
      alpha,
    ];
  }
  if (/^#[0-9a-f]{6}$/i.test(value)) {
    return [
      channel(value.slice(1, 3)),
      channel(value.slice(3, 5)),
      channel(value.slice(5, 7)),
      alpha,
    ];
  }
  throw new Error('Mesh colour must be #rgb or #rrggbb');
}

export class HgPrimitiveMaterial {
  readonly colour: HgRgba;

  constructor(
    colour: string | readonly [number, number, number, number],
    public shading: HgPrimitiveShading = 'lit',
  ) {
    this.colour = typeof colour === 'string'
      ? hgRgbaFromHex(colour)
      : [colour[0], colour[1], colour[2], colour[3]];
  }

  setColour(colour: string | readonly [number, number, number, number]): this {
    const next = typeof colour === 'string'
      ? hgRgbaFromHex(colour, this.colour[3])
      : [colour[0], colour[1], colour[2], colour[3]] as HgRgba;
    this.colour[0] = next[0];
    this.colour[1] = next[1];
    this.colour[2] = next[2];
    this.colour[3] = next[3];
    return this;
  }

  setOpacity(alpha: number): this {
    if (!Number.isFinite(alpha) || alpha < 0 || alpha > 1) {
      throw new Error('Mesh alpha must be between 0 and 1');
    }
    this.colour[3] = alpha;
    return this;
  }
}

/** Project-owned non-skinned scene mesh. GPU resources belong to the renderer. */
export class HgPrimitiveMesh extends HgObject3D {
  override readonly type = 'PrimitiveMesh';

  constructor(
    public geometry: HgPrimitiveGeometryData,
    public material: HgPrimitiveMaterial,
  ) {
    super();
  }
}
