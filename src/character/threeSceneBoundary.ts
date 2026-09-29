/**
 * The single character-side Three.js compatibility boundary.
 *
 * Character parsing, rig maths, retargeting, deformation, export and
 * equipment placement stay outside this file. Until the live skin/scene
 * runtime is replaced, this adapter owns the temporary renderer objects used
 * to materialize canonical and imported characters.
 */
import {
  Bone,
  BufferAttribute,
  BufferGeometry,
  ClampToEdgeWrapping,
  Color,
  DoubleSide,
  FrontSide,
  InterleavedBufferAttribute,
  LinearFilter,
  LinearMipmapLinearFilter,
  LinearMipmapNearestFilter,
  Material,
  Matrix4,
  Mesh,
  MeshStandardMaterial,
  MirroredRepeatWrapping,
  NearestFilter,
  NearestMipmapLinearFilter,
  NearestMipmapNearestFilter,
  Object3D,
  Quaternion,
  RepeatWrapping,
  Skeleton,
  SkinnedMesh,
  SphereGeometry,
  SRGBColorSpace,
  Texture,
} from '../core/threeRuntimeBoundary';

export {
  Bone,
  BufferAttribute,
  BufferGeometry,
  ClampToEdgeWrapping,
  Color,
  DoubleSide,
  FrontSide,
  InterleavedBufferAttribute,
  LinearFilter,
  LinearMipmapLinearFilter,
  LinearMipmapNearestFilter,
  Material,
  Matrix4,
  Mesh,
  MeshStandardMaterial,
  MirroredRepeatWrapping,
  NearestFilter,
  NearestMipmapLinearFilter,
  NearestMipmapNearestFilter,
  Object3D,
  Quaternion,
  RepeatWrapping,
  Skeleton,
  SkinnedMesh,
  SphereGeometry,
  SRGBColorSpace,
  Texture,
};
