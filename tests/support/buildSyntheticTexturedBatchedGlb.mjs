/** Test fixture ONLY: independently generated 2-mesh GLB with two PNGs. */
import {deflateSync} from 'node:zlib';
import {buildSyntheticBatchedGlb} from './buildSyntheticBatchedGlb.mjs';
const align=n=>(n+3)&~3;
function unpack(glb){
  const d=new DataView(glb),j=d.getUint32(12,true),b=20+j;
  return {
    root:JSON.parse(new TextDecoder().decode(new Uint8Array(glb,20,j)).trim()),
    bin:new Uint8Array(glb,b+8,d.getUint32(b,true))
  };
}
function pack(root,bin){
  const text=new TextEncoder().encode(JSON.stringify(root)),jlen=align(text.length);
  const v=new ArrayBuffer(12+8+jlen+8+bin.length),d=new DataView(v);
  d.setUint32(0,0x46546c67,true);d.setUint32(4,2,true);
  d.setUint32(8,v.byteLength,true);d.setUint32(12,jlen,true);
  d.setUint32(16,0x4e4f534a,true);
  new Uint8Array(v,20,jlen).fill(32);
  new Uint8Array(v,20,text.length).set(text);
  d.setUint32(20+jlen,bin.length,true);
  d.setUint32(24+jlen,0x004e4942,true);
  new Uint8Array(v,28+jlen).set(bin);
  return v;
}
function crc(arr){
  let c=0xffffffff;
  for(const v of arr){c^=v;for(let j=0;j<8;j++)c=(c>>>1)^((c&1)?0xedb88320:0)}
  return (c^0xffffffff)>>>0;
}
function chunk(type,body){
  const b=new Uint8Array(12+body.length),v=new DataView(b.buffer);
  v.setUint32(0,body.length,false);
  b.set(new TextEncoder().encode(type),4);
  b.set(body,8);
  v.setUint32(b.length-4,crc(b.subarray(4,b.length-4)),false);
  return b;
}
function makePng(rgb){
  if(!Array.isArray(rgb)||rgb.length!==3 ||
    !rgb.every(n=>Number.isInteger(n)&&n>=0&&n<=255))
    throw new RangeError('Test PNG needs 3 byte channels');
  const hdr=new Uint8Array(13),d=new DataView(hdr.buffer);
  d.setUint32(0,2,false);d.setUint32(4,2,false);
  hdr[8]=8;hdr[9]=6;
  const [r,g,b]=rgb;
  const raw=new Uint8Array([0,r,g,b,255,r,g,b,255,
                            0,r,g,b,255,r,g,b,255]);
  const chunks=[
    new Uint8Array([137,80,78,71,13,10,26,10]),
    chunk('IHDR',hdr),
    chunk('IDAT',new Uint8Array(deflateSync(raw))),
    chunk('IEND',new Uint8Array())];
  const bytes=new Uint8Array(chunks.reduce((n,x)=>n+x.length,0));
  let p=0;for(const c of chunks){bytes.set(c,p);p+=c.length}
  return bytes;
}

/**
 * Returns a NEW genuine small glTF 2.0 GLB including source geometry, skin,
 * exact two original embedded images, UVs and two declared baseColor materials.
 * Dev fixture only; not the original human or a production authoring routine.
 */
export function buildSyntheticTexturedBatchedGlb({
  imageRGBs=[[247,20,23],[15,244,32]],
  mutate,
}={}){
  if(!Array.isArray(imageRGBs)||imageRGBs.length!==2)
    throw new RangeError('Exactly two synthetic PNG fixtures required');
  const {root,bin:original}=unpack(buildSyntheticBatchedGlb());
  let offset=original.length;
  const newBuffers=[];
  const insert=src=>{
    const start=offset;
    newBuffers.push({start,src});
    offset+=align(src.length);
    root.bufferViews.push({buffer:0,byteOffset:start,byteLength:src.length});
    return root.bufferViews.length-1;
  };
  const uvIndices=[];
  for(let j=0;j<2;j++){
    const view=insert(new Uint8Array(
      new Float32Array([0,0,1,0,0,1]).buffer));
    root.accessors.push({bufferView:view,componentType:5126,
      count:3,type:'VEC2'});
    uvIndices.push(root.accessors.length-1);
  }
  const imageViews=imageRGBs.map(x=>insert(makePng(x)));
  for(let j=0;j<2;j++){
    root.meshes[j].primitives[0].attributes.TEXCOORD_0=uvIndices[j];
    root.meshes[j].primitives[0].material=j;
  }
  root.images=imageViews.map((view,j)=>({
    name:'original_test_png_'+j,bufferView:view,mimeType:'image/png',
  }));
  root.samplers=[{magFilter:9729,minFilter:9729,wrapS:33071,wrapT:33071}];
  root.textures=[{source:0,sampler:0},{source:1,sampler:0}];
  root.materials=[0,1].map(j=>({
    name:'project_test_matte_'+j,
    pbrMetallicRoughness:{
      baseColorFactor:[1,1,1,1],metallicFactor:0,roughnessFactor:1,
      baseColorTexture:{index:j,texCoord:0}
    }
  }));
  root.buffers[0].byteLength=offset;
  const combined=new Uint8Array(offset);
  combined.set(original);
  for(const {start,src}of newBuffers)combined.set(src,start);
  if(mutate)mutate(root,combined);
  return pack(root,combined);
}
