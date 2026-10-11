/**
 * HGPT G1c first-party GLB TEXCOORD_0 data decoding.
 * Strict read-only binary accessor, bounded/validated before stripping the
 * optional attribute from the original single-primitive strict GLB validator.
 * Does NOT implement image textures, texture fetching, samplers, PBR or UV
 * anatomical approval. No Three.js, glTF package, network or native addon.
 */
export const HGPT_UV0_KIND='hgpt-g1c-strict-glb-uv0-v1';
const err=msg=>{throw new RangeError('GLB UV0 rejection: '+msg);};
const expect=(ok,msg)=>{if(!ok)err(msg);};
const own=(v,key)=>Object.prototype.hasOwnProperty.call(v,key);
const ALLOWED_ACCESSOR=new Set(['bufferView','byteOffset','componentType','count',
  'type','normalized','name']);
const ALLOWED_VIEW=new Set(['buffer','byteOffset','byteLength','byteStride','target','name']);
const MAX_ABS_UV=1024;

/** Source coordinates remain in glTF UV convention, with no invented Y flip. */
export function readRestrictedGlbUV0(root,bin,accessorIndex,expectedVertexCount){
  expect(root && typeof root==='object' && !Array.isArray(root) &&
    bin instanceof Uint8Array,'trusted GLB object and embedded BIN required');
  expect(Number.isSafeInteger(expectedVertexCount) && expectedVertexCount>=3 &&
    expectedVertexCount<=250000,'bounded expected vertex count required');
  expect(Number.isSafeInteger(accessorIndex) && accessorIndex>=0,
    'missing valid TEXCOORD_0 accessor');
  const a=root.accessors?.[accessorIndex];
  expect(a && typeof a==='object' && !Array.isArray(a) &&
    Object.keys(a).every(k=>ALLOWED_ACCESSOR.has(k)) &&
    !own(a,'sparse'),'unsupported UV accessor metadata or sparse accessor');
  expect(a.type==='VEC2' && a.count===expectedVertexCount,'UV0 VEC2 vertex count mismatch');
  const c=a.componentType;
  expect(c===5126||c===5121||c===5123,
    'UV0 requires FLOAT or normalized unsigned byte/short');
  if(c===5126)expect(!a.normalized,'float UV0 must not be normalized');
  else expect(a.normalized===true,'integer UV0 must be normalized');
  expect(Number.isSafeInteger(a.bufferView)&&a.bufferView>=0,
    'UV0 bufferView required');
  const v=root.bufferViews?.[a.bufferView];
  expect(v && typeof v==='object' && !Array.isArray(v) &&
    Object.keys(v).every(k=>ALLOWED_VIEW.has(k)) && v.buffer===0,
    'UV0 must use supported embedded BIN buffer view');
  const declared=root.buffers?.[0]?.byteLength;
  expect(Number.isSafeInteger(declared)&&declared>0 &&
    declared<=bin.byteLength && bin.byteLength-declared<4,
    'UV0 declared binary length invalid');
  const size=c===5126?4:c===5123?2:1;
  const byteOffset=v.byteOffset??0;
  const localOffset=a.byteOffset??0;
  const viewLength=v.byteLength;
  const bytesPerVertex=2*size;
  const stride=v.byteStride??bytesPerVertex;
  expect([byteOffset,localOffset,viewLength,stride].every(x=>
    Number.isSafeInteger(x)&&x>=0),'UV0 offsets/stride must be nonnegative integers');
  expect(stride>=bytesPerVertex && stride<=252 && stride%size===0,
    'UV0 byteStride unsupported');
  expect((byteOffset+localOffset)%size===0 && byteOffset%4===0,
    'UV0 component / buffer view alignment invalid');
  expect(viewLength>0 && byteOffset+viewLength<=declared &&
    byteOffset+viewLength<=bin.byteLength,'UV0 bufferView exceeds bounded BIN');
  const finalByte=localOffset+(a.count-1)*stride+bytesPerVertex;
  expect(finalByte<=viewLength,'UV0 accessor escapes buffer view');
  const byteView=new DataView(bin.buffer,bin.byteOffset,bin.byteLength);
  const uv=new Float32Array(a.count*2);
  for(let i=0;i<a.count;i++)for(let k=0;k<2;k++){
    const offset=byteOffset+localOffset+i*stride+k*size;
    let value;
    if(c===5126)value=byteView.getFloat32(offset,true);
    else if(c===5123)value=byteView.getUint16(offset,true)/65535;
    else value=byteView.getUint8(offset)/255;
    expect(Number.isFinite(value)&&Math.abs(value)<=MAX_ABS_UV,
      'nonfinite or extreme tiled UV coordinates');
    uv[i*2+k]=value;
  }
  return uv;
}
