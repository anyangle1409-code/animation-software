/**
 * G1d: bounded, read-only glTF 2.0 NORMAL accessor for an explicitly opted-in
 * first-party preview. No normal generation, tangent/PBR support, or skinning.
 * Existing source GLB strict validation still runs on every primitive.
 */
export const HGPT_SOURCE_NORMAL_KIND='hgpt-g1d-strict-glb-source-normal-v1';
const fail=message=>{throw new RangeError('GLB NORMAL rejection: '+message);};
const requireThat=(ok,message)=>{if(!ok)fail(message);};
const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
const ACCESSOR_KEYS=new Set(['bufferView','byteOffset','componentType','count',
  'type','normalized','name']);
const VIEW_KEYS=new Set(['buffer','byteOffset','byteLength','byteStride','target','name']);
const isObject=v=>v&&typeof v==='object'&&!Array.isArray(v);

/**
 * Returns original per-vertex source normals, never invented geometry.
 * Only finite unit-length FLOAT VEC3, embedded BIN and explicit vertex count.
 * glTF source-space handedness/orientation is not changed.
 */
export function readRestrictedGlbNormals(root,bin,index,vertexCount){
  requireThat(isObject(root)&&bin instanceof Uint8Array,
    'embedded GLB source required');
  requireThat(Number.isSafeInteger(vertexCount)&&vertexCount>=3&&vertexCount<=250000,
    'bounded source vertex count required');
  requireThat(Number.isSafeInteger(index)&&index>=0,
    'NORMAL accessor must be explicitly present');
  const a=root.accessors?.[index];
  requireThat(isObject(a)&&Object.keys(a).every(k=>ACCESSOR_KEYS.has(k))&&
    !own(a,'sparse'),'unknown or sparse NORMAL accessor');
  requireThat(a.type==='VEC3'&&a.componentType===5126&&
    a.count===vertexCount&&!a.normalized,
    'NORMAL must be FLOAT VEC3 matching source vertex count');
  requireThat(Number.isSafeInteger(a.bufferView)&&a.bufferView>=0,
    'NORMAL embedded bufferView required');
  const v=root.bufferViews?.[a.bufferView];
  requireThat(isObject(v)&&Object.keys(v).every(k=>VIEW_KEYS.has(k))&&
    v.buffer===0,'NORMAL requires supported embedded BIN bufferView');
  const declared=root.buffers?.[0]?.byteLength;
  requireThat(Number.isSafeInteger(declared)&&declared>0&&
    declared<=bin.byteLength&&bin.byteLength-declared<4,
    'declared BIN byte length mismatch');
  const offset=v.byteOffset??0,local=a.byteOffset??0;
  const stride=v.byteStride??12,len=v.byteLength;
  requireThat([offset,local,stride,len].every(x=>Number.isSafeInteger(x)&&x>=0),
    'invalid negative or fractional byte offsets');
  requireThat(offset%4===0&&local%4===0&&stride%4===0&&
    stride>=12&&stride<=252,
    'NORMAL float component alignment or stride unsupported');
  requireThat(len>0&&offset+len<=declared&&offset+len<=bin.byteLength,
    'NORMAL bufferView exceeds bounded BIN');
  requireThat(local+(vertexCount-1)*stride+12<=len,
    'NORMAL accessor escapes bufferView');
  const view=new DataView(bin.buffer,bin.byteOffset,bin.byteLength);
  const values=new Float32Array(vertexCount*3);
  for(let i=0;i<vertexCount;i++){
    const p=offset+local+i*stride;
    const x=view.getFloat32(p,true),y=view.getFloat32(p+4,true),
      z=view.getFloat32(p+8,true);
    requireThat(Number.isFinite(x)&&Number.isFinite(y)&&Number.isFinite(z),
      'nonfinite source normal');
    const length=Math.hypot(x,y,z);
    requireThat(length>=0.998&&length<=1.002,
      'source normal must be unit length (no zero/unnormalized vectors)');
    values.set([x,y,z],i*3);
  }
  return values;
}
