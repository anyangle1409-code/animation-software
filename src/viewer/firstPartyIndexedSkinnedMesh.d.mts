export const NATIVE_SKINNED_KIND: string;
export interface NativeFourWeightSkinMesh {
  positions: Float32Array;
  indices: Uint16Array | Uint32Array;
  jointIndices: Uint16Array;
  weights: Float32Array;
  inverseBindMatrices: Float32Array;
}
export interface NativeDeformedIndexedMesh {
  positions: Float32Array;
  normals: Float32Array;
  indices: Uint16Array | Uint32Array;
  triangleCount: number;
  skinningMode: string;
}
export function validateNativeSkinnedMesh(mesh: NativeFourWeightSkinMesh): {
  vertices:number;triangles:number;bones:number;
};
export function deformIndexedSkin(
  mesh: NativeFourWeightSkinMesh, posedWorldMatrices: Float32Array
): NativeDeformedIndexedMesh;
export function invertRigidBind(matrix:ArrayLike<number>):Float32Array;
export function makeTwoBoneSkinProbe(
  start:number[],elbow:number[],end:number[],
  options?:{radius?:number;sides?:number}
):Omit<NativeFourWeightSkinMesh,'inverseBindMatrices'>;
export interface NativeIndexedMeshRenderer {
  readonly frameCount:number;
  readonly contextLost:boolean;
  readonly kind:string;
  setSize(width:number,height:number,dpr?:number):void;
  render(mesh:NativeDeformedIndexedMesh,opts?:{
    eye?:number[];
    target?:number[];
    color?:number[];
  }):boolean;
  dispose():void;
}
export function createNativeIndexedMeshWebGL2(canvas:HTMLCanvasElement):NativeIndexedMeshRenderer;
