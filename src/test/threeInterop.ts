import type {
  BufferAttribute,
  InterleavedBufferAttribute,
  Matrix4,
  Object3D,
} from 'three';

export const asThreeMatrix = (
  value: { readonly elements: ArrayLike<number> },
): Matrix4 => value as unknown as Matrix4;

export const asThreeObject = <T>(value: T): Object3D =>
  value as unknown as Object3D;

export const asThreeAttribute = (
  value: {
    readonly count: number;
    getX(index: number): number;
    getY(index: number): number;
    getZ(index: number): number;
  },
): BufferAttribute | InterleavedBufferAttribute =>
  value as unknown as BufferAttribute | InterleavedBufferAttribute;
