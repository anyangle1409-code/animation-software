import { HgObject3D } from './sceneGraph';
import type { HgRgba } from './sceneMesh';

export interface HgCharacterGeometryData {
  readonly positions: readonly number[];
  readonly normals: readonly number[];
  readonly indices: readonly number[];
  readonly uvs?: readonly number[];
  readonly colours?: readonly number[];
}

export interface HgCharacterBaseTexture {
  /** Browser-native decoded image; no renderer-vendor texture object crosses here. */
  readonly image: TexImageSource;
  readonly flipY: boolean;
  readonly wrapS?: 33071 | 33648 | 10497;
  readonly wrapT?: 33071 | 33648 | 10497;
  readonly magFilter?: 9728 | 9729 | null;
  readonly minFilter?: 9728 | 9729 | 9984 | 9985 | 9986 | 9987 | null;
}

/**
 * Renderer-neutral posed character surface.
 *
 * Geometry is already morphed/skinned into mesh-local positions; the scene
 * node contributes only its world transform and base material colour.
 */
export class HgCharacterMesh extends HgObject3D {
  override readonly type = 'CharacterMesh';

  constructor(
    public geometry: HgCharacterGeometryData,
    public readonly baseColour: HgRgba = [1, 1, 1, 1],
    public baseTexture: HgCharacterBaseTexture | null = null,
  ) {
    super();
  }
}
