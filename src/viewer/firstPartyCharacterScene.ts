import { HgVec3 } from '../core/linearMath';
import {
  HgCharacterMesh,
  type HgCharacterBaseTexture,
} from '../core/sceneCharacter';
import type { HgPrimitiveGeometryData } from '../core/primitiveGeometry';
import { hgRgbaFromHex } from '../core/sceneMesh';
import type { HgDeformableMeshLike } from '../character/skinningMath';
import { posedLocalVertex } from '../character/skinningMath';


export interface HgRenderableCharacterMesh extends HgDeformableMeshLike {
  readonly name: string;
  readonly geometry: HgDeformableMeshLike['geometry'] & {
    getIndex(): { readonly count: number; getX(index: number): number } | null;
    getAttribute(name: string): {
      readonly count: number;
      getX(index: number): number;
      getY(index: number): number;
      getZ(index: number): number;
    } | undefined;
  };
  readonly skeleton: {
    readonly bones: ReadonlyArray<{
      readonly matrixWorld: { readonly elements: ArrayLike<number> };
      updateWorldMatrix(updateParents: boolean, updateChildren: boolean): void;
    }>;
    readonly boneInverses: readonly { readonly elements: ArrayLike<number> }[];
  };
  readonly material:
    | {
        color?: { r: number; g: number; b: number };
        opacity?: number;
        map?: {
          image?: unknown;
          flipY?: boolean;
          wrapS?: 33071 | 33648 | 10497;
          wrapT?: 33071 | 33648 | 10497;
          magFilter?: 9728 | 9729 | null;
          minFilter?: 9728 | 9729 | 9984 | 9985 | 9986 | 9987 | null;
        } | null;
      }
    | Array<{
        color?: { r: number; g: number; b: number };
        opacity?: number;
        map?: {
          image?: unknown;
          flipY?: boolean;
          wrapS?: 33071 | 33648 | 10497;
          wrapT?: 33071 | 33648 | 10497;
          magFilter?: 9728 | 9729 | null;
          minFilter?: 9728 | 9729 | 9984 | 9985 | 9986 | 9987 | null;
        } | null;
      }>;
  readonly matrixWorld: { readonly elements: ArrayLike<number> };
  updateWorldMatrix(updateParents: boolean, updateChildren: boolean): void;
}

export interface HgPosedCharacterGeometry extends HgPrimitiveGeometryData {
  colours?: number[];
}

const component = (
  attribute: { getX(i: number): number; getY(i: number): number; getZ(i: number): number } | undefined,
  index: number,
): [number, number, number] | null => attribute
  ? [attribute.getX(index), attribute.getY(index), attribute.getZ(index)]
  : null;

/**
 * Snapshot one first-party skinned mesh into renderer-ready posed geometry.
 *
 * Positions include current morph targets and skinning. Normals are recomputed
 * from the posed triangles so lighting follows the deformation without relying
 * on renderer-specific skin-normal code. UVs and vertex colours retain the
 * authored per-vertex data for the texture/colour WebGL stage.
 */
export function posedCharacterGeometry(
  mesh: HgRenderableCharacterMesh,
): HgPosedCharacterGeometry {
  mesh.updateWorldMatrix(true, false);
  for (const bone of mesh.skeleton.bones) bone.updateWorldMatrix(true, false);

  const position = mesh.geometry.getAttribute('position');
  if (!position) throw new Error('Skinned character mesh has no position attribute');

  const uv = mesh.geometry.getAttribute('uv');
  const colour = mesh.geometry.getAttribute('color');
  const index = mesh.geometry.getIndex();
  const indices = index
    ? Array.from({ length: index.count }, (_, offset) => Math.round(index.getX(offset)))
    : Array.from({ length: position.count }, (_, offset) => offset);

  const positions = new Array<number>(position.count * 3);
  const uvs = new Array<number>(position.count * 2).fill(0);
  const colours = colour ? new Array<number>(position.count * 3) : undefined;
  const point = new HgVec3();

  for (let vertex = 0; vertex < position.count; vertex += 1) {
    posedLocalVertex(mesh, vertex, point);
    const p = vertex * 3;
    positions[p] = point.x;
    positions[p + 1] = point.y;
    positions[p + 2] = point.z;

    if (uv) {
      const t = vertex * 2;
      uvs[t] = uv.getX(vertex);
      uvs[t + 1] = uv.getY(vertex);
    }
    if (colours) {
      const value = component(colour, vertex)!;
      colours[p] = value[0];
      colours[p + 1] = value[1];
      colours[p + 2] = value[2];
    }
  }

  const normals = new Array<number>(position.count * 3).fill(0);
  const a = new HgVec3();
  const b = new HgVec3();
  const c = new HgVec3();
  const ab = new HgVec3();
  const ac = new HgVec3();
  const face = new HgVec3();

  const read = (vertex: number, target: HgVec3) => {
    const offset = vertex * 3;
    return target.set(
      positions[offset],
      positions[offset + 1],
      positions[offset + 2],
    );
  };

  for (let offset = 0; offset + 2 < indices.length; offset += 3) {
    const ia = indices[offset];
    const ib = indices[offset + 1];
    const ic = indices[offset + 2];
    read(ia, a); read(ib, b); read(ic, c);
    ab.copy(b).sub(a);
    ac.copy(c).sub(a);
    face.crossVectors(ab, ac);
    for (const vertex of [ia, ib, ic]) {
      const start = vertex * 3;
      normals[start] += face.x;
      normals[start + 1] += face.y;
      normals[start + 2] += face.z;
    }
  }

  for (let vertex = 0; vertex < position.count; vertex += 1) {
    const offset = vertex * 3;
    point.set(normals[offset], normals[offset + 1], normals[offset + 2]);
    if (point.lengthSq() > 1e-20) point.normalize();
    normals[offset] = point.x;
    normals[offset + 1] = point.y;
    normals[offset + 2] = point.z;
  }

  return {
    positions,
    normals,
    uvs,
    indices,
    ...(colours ? { colours } : {}),
  };
}


const materialColour = (mesh: HgRenderableCharacterMesh): [number, number, number, number] => {
  const material = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
  const colour = material?.color;
  return colour
    ? [colour.r, colour.g, colour.b, material?.opacity ?? 1]
    : hgRgbaFromHex('#ffffff');
};

const materialBaseTexture = (
  mesh: HgRenderableCharacterMesh,
): HgCharacterBaseTexture | null => {
  const material = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
  const image = material?.map?.image;
  if (!image || (typeof image !== 'object' && typeof image !== 'function')) return null;
  return {
    image: image as TexImageSource,
    flipY: material?.map?.flipY ?? false,
    wrapS: material?.map?.wrapS,
    wrapT: material?.map?.wrapT,
    magFilter: material?.map?.magFilter,
    minFilter: material?.map?.minFilter,
  };
};

/** Build one renderer-neutral posed character scene node. */
export function createHgCharacterMesh(mesh: HgRenderableCharacterMesh): HgCharacterMesh {
  mesh.updateWorldMatrix(true, false);
  const result = new HgCharacterMesh(
    posedCharacterGeometry(mesh),
    materialColour(mesh),
    materialBaseTexture(mesh),
  );
  result.name = mesh.name;
  result.matrixAutoUpdate = false;
  result.matrix.copy(mesh.matrixWorld);
  result.matrixWorldNeedsUpdate = true;
  return result;
}

/** Refresh a character scene node after bones/morphs/material opacity change. */
export function updateHgCharacterMesh(
  target: HgCharacterMesh,
  mesh: HgRenderableCharacterMesh,
): void {
  mesh.updateWorldMatrix(true, false);
  target.geometry = posedCharacterGeometry(mesh);
  target.matrix.copy(mesh.matrixWorld);
  target.matrixWorldNeedsUpdate = true;
  const colour = materialColour(mesh);
  target.baseColour[0] = colour[0];
  target.baseColour[1] = colour[1];
  target.baseColour[2] = colour[2];
  target.baseColour[3] = colour[3];
  target.baseTexture = materialBaseTexture(mesh);
}
