/**
 * Synthetic source-owned UV0 GLB2 data generator. No licensed textures,
 * medical assets, clinical coordinate data or third-party geometry used.
 */
import { buildSyntheticBatchedGlb } from './buildSyntheticBatchedGlb.mjs';
const align4=n=>(n+3)&~3;
function extract(data){
  const view=new DataView(data),jlen=view.getUint32(12,true),offset=20+jlen;
  const root=JSON.parse(new TextDecoder().decode(new Uint8Array(data,20,jlen)).trim());
  const bin=new Uint8Array(data,offset+8,view.getUint32(offset,true));
  return {root,bin};
}
function pack(root,bin){
  const text=new TextEncoder().encode(JSON.stringify(root));
  const jlen=align4(text.byteLength),total=12+8+jlen+8+bin.byteLength;
  const bytes=new ArrayBuffer(total),view=new DataView(bytes);
  view.setUint32(0,0x46546c67,true);view.setUint32(4,2,true);
  view.setUint32(8,total,true);view.setUint32(12,jlen,true);
  view.setUint32(16,0x4e4f534a,true);
  new Uint8Array(bytes,20,jlen).fill(32);
  new Uint8Array(bytes,20,text.byteLength).set(text);
  const b=20+jlen;
  view.setUint32(b,bin.byteLength,true);view.setUint32(b+4,0x004e4942,true);
  new Uint8Array(bytes,b+8,bin.byteLength).set(bin);
  return bytes;
}
export function buildSyntheticUV0Glb({
  meshCount=2,primitivesPerMesh=1,componentType=5126,
  addSourceColors=false,mutate
}={}){
  if(![5126,5123,5121].includes(componentType))
    throw new RangeError('UV fixture componentType outside glTF subset');
  const {root,bin:base}=extract(buildSyntheticBatchedGlb({meshCount,primitivesPerMesh}));
  const size=componentType===5126?4:componentType===5123?2:1;
  const joined=[base];let offset=base.byteLength;
  root.meshes.forEach((mesh,m)=>mesh.primitives.forEach((part,p)=>{
    const green=(m+p)%2===1;
    const uv=green ?
      [.055,.895,.095,.895,.055,.945] :
      [.895,.055,.945,.055,.895,.095];
    const bytes=new Uint8Array(align4(uv.length*size));
    const view=new DataView(bytes.buffer);
    for(let i=0;i<uv.length;i++){
      if(componentType===5126)view.setFloat32(i*size,uv[i],true);
      else if(componentType===5123)view.setUint16(i*size,Math.round(uv[i]*65535),true);
      else view.setUint8(i,Math.round(uv[i]*255));
    }
    root.bufferViews.push({buffer:0,byteOffset:offset,byteLength:uv.length*size});
    root.accessors.push({
      bufferView:root.bufferViews.length-1,componentType,
      count:3,type:'VEC2',
      ...(componentType===5126?{}:{normalized:true})
    });
    part.attributes.TEXCOORD_0=root.accessors.length-1;
    joined.push(bytes);offset+=bytes.length;
  }));
  if(addSourceColors){
    root.materials=[
      {name:'firstparty_untextured_red',pbrMetallicRoughness:{
        baseColorFactor:[.94,.25,.20,1],metallicFactor:0,roughnessFactor:1}},
      {name:'firstparty_untextured_green',pbrMetallicRoughness:{
        baseColorFactor:[.15,.84,.29,1],metallicFactor:0,roughnessFactor:1}}
    ];
    root.meshes.forEach((mesh,m)=>mesh.primitives.forEach(part=>{
      part.material=m%2;
    }));
  }
  const merged=new Uint8Array(align4(offset));
  let cursor=0;for(const chunk of joined){merged.set(chunk,cursor);cursor+=chunk.length;}
  root.buffers[0].byteLength=merged.byteLength;
  if(mutate)mutate(root,merged);
  return pack(root,merged);
}
