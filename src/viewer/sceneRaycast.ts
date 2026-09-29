import { HgMat4, HgVec3 } from '../core/linearMath';

interface MatrixLike {
  readonly elements: ArrayLike<number>;
}

interface PositionAttributeLike {
  readonly count: number;
  getX(index: number): number;
  getY(index: number): number;
  getZ(index: number): number;
}

interface IndexAttributeLike {
  readonly count: number;
  getX(index: number): number;
}

interface AccessorGeometryLike {
  getAttribute(name: string): PositionAttributeLike | undefined;
  getIndex(): IndexAttributeLike | null;
}
interface PrimitiveGeometryLike {
  readonly positions: readonly number[];
  readonly indices: readonly number[];
}
type GeometryLike = AccessorGeometryLike | PrimitiveGeometryLike;

export interface HgRaycastObjectLike {
  readonly children: readonly HgRaycastObjectLike[];
  readonly matrixWorld: MatrixLike;
  readonly geometry?: GeometryLike;
  readonly isMesh?: boolean;
}

export interface HgRayCameraLike {
  readonly matrixWorld: MatrixLike;
  readonly projectionMatrixInverse: MatrixLike;
}

export interface HgSceneRay {
  origin: HgVec3;
  direction: HgVec3;
}

export interface HgSceneRayHit<T extends HgRaycastObjectLike = HgRaycastObjectLike> {
  object: T;
  distance: number;
}

export const createSceneRay = (): HgSceneRay => ({
  origin: new HgVec3(),
  direction: new HgVec3(0, 0, -1),
});

/** Build a world-space ray from browser normalised-device coordinates. */
export function setSceneRayFromCamera(
  ray: HgSceneRay,
  camera: HgRayCameraLike,
  x: number,
  y: number,
): HgSceneRay {
  ray.origin.setFromMatrixPosition(camera.matrixWorld);
  const worldPoint = new HgVec3(x, y, 0.5)
    .applyMatrix4(camera.projectionMatrixInverse)
    .applyMatrix4(camera.matrixWorld);
  ray.direction.copy(worldPoint).sub(ray.origin).normalize();
  return ray;
}

const intersectTriangle = (
  origin: HgVec3,
  direction: HgVec3,
  a: HgVec3,
  b: HgVec3,
  c: HgVec3,
): number | null => {
  const edge1 = b.clone().sub(a);
  const edge2 = c.clone().sub(a);
  const p = direction.clone().cross(edge2);
  const determinant = edge1.dot(p);
  if (Math.abs(determinant) < 1e-10) return null;

  const inverseDeterminant = 1 / determinant;
  const translated = origin.clone().sub(a);
  const u = translated.dot(p) * inverseDeterminant;
  if (u < 0 || u > 1) return null;

  const q = translated.clone().cross(edge1);
  const v = direction.dot(q) * inverseDeterminant;
  if (v < 0 || u + v > 1) return null;

  const distance = edge2.dot(q) * inverseDeterminant;
  return distance >= 0 ? distance : null;
};

const triangleVertex = (
  position: PositionAttributeLike,
  index: number,
  target: HgVec3,
): HgVec3 => target.set(
  position.getX(index),
  position.getY(index),
  position.getZ(index),
);

const positionAttribute = (geometry: GeometryLike): PositionAttributeLike | null => {
  if ('getAttribute' in geometry) return geometry.getAttribute('position') ?? null;
  if (geometry.positions.length % 3 !== 0) return null;
  return {
    count: geometry.positions.length / 3,
    getX: (index) => geometry.positions[index * 3] ?? 0,
    getY: (index) => geometry.positions[index * 3 + 1] ?? 0,
    getZ: (index) => geometry.positions[index * 3 + 2] ?? 0,
  };
};
const indexAttribute = (geometry: GeometryLike): IndexAttributeLike | null =>
  'getIndex' in geometry
    ? geometry.getIndex()
    : {
        count: geometry.indices.length,
        getX: (index) => geometry.indices[index] ?? 0,
      };

const meshDistance = (
  object: HgRaycastObjectLike,
  ray: HgSceneRay,
): number | null => {
  const geometry = object.geometry;
  if (!geometry) return null;
  const position = positionAttribute(geometry);
  if (!position || position.count < 3) return null;

  const inverseWorld = new HgMat4().copy(object.matrixWorld).invert();
  const localOrigin = ray.origin.clone().applyMatrix4(inverseWorld);
  const localPoint = ray.origin.clone().add(ray.direction).applyMatrix4(inverseWorld);
  const localDirection = localPoint.sub(localOrigin).normalize();

  const a = new HgVec3();
  const b = new HgVec3();
  const c = new HgVec3();
  const localHit = new HgVec3();
  const worldHit = new HgVec3();
  const index = indexAttribute(geometry);

  let best = Infinity;
  const triangleCount = index
    ? Math.floor(index.count / 3)
    : Math.floor(position.count / 3);

  for (let triangle = 0; triangle < triangleCount; triangle += 1) {
    const offset = triangle * 3;
    const ia = index ? Math.round(index.getX(offset)) : offset;
    const ib = index ? Math.round(index.getX(offset + 1)) : offset + 1;
    const ic = index ? Math.round(index.getX(offset + 2)) : offset + 2;

    triangleVertex(position, ia, a);
    triangleVertex(position, ib, b);
    triangleVertex(position, ic, c);
    const localDistance = intersectTriangle(localOrigin, localDirection, a, b, c);
    if (localDistance === null) continue;

    localHit.copy(localDirection).multiplyScalar(localDistance).add(localOrigin);
    worldHit.copy(localHit).applyMatrix4(object.matrixWorld);
    const worldDistance = worldHit.distanceTo(ray.origin);
    if (worldDistance < best) best = worldDistance;
  }

  return Number.isFinite(best) ? best : null;
};

const visit = (
  object: HgRaycastObjectLike,
  ray: HgSceneRay,
  hits: HgSceneRayHit[],
): void => {
  if (object.isMesh && object.geometry) {
    const distance = meshDistance(object, ray);
    if (distance !== null) hits.push({ object, distance });
  }
  for (const child of object.children) visit(child, ray, hits);
};

/**
 * Intersect project-created triangle meshes and return nearest-first hits.
 *
 * The live interactive scene only registers mesh handles or groups containing
 * mesh handles, so character surfaces and renderer-specific ray helpers are
 * deliberately outside this routine.
 */
export function intersectSceneMeshes(
  roots: readonly HgRaycastObjectLike[],
  ray: HgSceneRay,
): HgSceneRayHit[] {
  const hits: HgSceneRayHit[] = [];
  for (const root of roots) visit(root, ray, hits);
  hits.sort((left, right) => left.distance - right.distance);
  return hits;
}
