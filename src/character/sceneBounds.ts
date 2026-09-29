import { HgVec3 } from '../core/linearMath';
import {
  posedLocalVertex,
  type HgDeformableMeshLike,
  type HgMatrixLike,
} from './skinningMath';

interface SceneNodeLike extends Partial<HgDeformableMeshLike> {
  readonly children: readonly SceneNodeLike[];
  readonly matrixWorld: HgMatrixLike;
  updateMatrixWorld(force: boolean): void;
}

const visit = (node: SceneNodeLike, callback: (node: SceneNodeLike) => void): void => {
  callback(node);
  for (const child of node.children) visit(child, callback);
};

/**
 * Measure a character scene without renderer bounds helpers.
 *
 * The routine evaluates authored morphs and skin weights from the current bone
 * world matrices, then applies the object's world transform. This keeps import
 * scaling independent of Three's Box3 implementation.
 */
export function measureSceneHeight(root: SceneNodeLike): number {
  root.updateMatrixWorld(true);

  let minimum = Infinity;
  let maximum = -Infinity;
  const point = new HgVec3();

  visit(root, (node) => {
    const geometry = node.geometry;
    const position = geometry?.getAttribute('position');
    if (!geometry || !position) return;

    for (let index = 0; index < position.count; index += 1) {
      posedLocalVertex(node as HgDeformableMeshLike, index, point).applyMatrix4(node.matrixWorld);
      if (!Number.isFinite(point.y)) continue;
      minimum = Math.min(minimum, point.y);
      maximum = Math.max(maximum, point.y);
    }
  });

  if (!Number.isFinite(minimum) || !Number.isFinite(maximum)) return 0.5;
  return Math.max(0.5, maximum - minimum);
}
