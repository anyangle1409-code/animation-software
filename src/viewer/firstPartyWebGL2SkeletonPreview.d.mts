import type { BoneName } from '../rig/boneNames';
export const NATIVE_RENDERER_KIND: string;
export function nativeLookAt(
  eye: number[], target: number[], up?: number[]
): Float32Array;
export function nativePerspective(
  fov: number, aspect: number, near: number, far: number
): Float32Array;
export function multiplyNativeMat4(
  a: ArrayLike<number>, b: ArrayLike<number>
): Float32Array;
export function clipPoint(
  matrix: ArrayLike<number>, point: ArrayLike<number>
): number[];
export function packBoneSegments(
  rig: { readonly names: BoneName[]; has(name: string): name is BoneName },
  evaluation: {
    head(name: BoneName): { x:number; y:number; z:number };
    tail(name: BoneName): { x:number; y:number; z:number };
  },
  names?: BoneName[],
): Float32Array;
export interface NativeWebGL2BoneRenderer {
  readonly kind: string;
  readonly frameCount: number;
  readonly contextLost: boolean;
  setSize(width:number,height:number,devicePixelRatio?:number):void;
  render(segments:Float32Array,opts?: {
    eye?:number[];
    target?:number[];
    color?:number[];
  }):boolean;
  dispose():void;
}
export function createFirstPartyWebGL2BoneRenderer(
  canvas: HTMLCanvasElement
): NativeWebGL2BoneRenderer;
