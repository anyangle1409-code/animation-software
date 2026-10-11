/** G2d original synthetic source PNG + source NORMAL/UV two-mesh fixture. */
import {deflateSync} from 'node:zlib';
import {buildSyntheticSourceNormalGLB} from './buildSyntheticSourceNormalGlb.mjs';
const align=n=>(n+3)&~3;
function crc(a){
  let x=0xffffffff;
  for(const b of a){x^=b;for(let i=0;i<8;i++)
    x=(x>>>1)^((x&1)?0xedb88320:0);}
  return (x^0xffffffff)>>>0;
}
function chunk(name,payload){
  const a=new Uint8Array(12+payload.length),v=new DataView(a.buffer);
  a.set(new TextEncoder().encode(name),4);a.set(payload,8);
  v.setUint32(0,payload.length,false);
  v.setUint32(a.length-4,crc(a.subarray(4,a.length-4)),false);
  return a;
}
function png(r,g,b){
  const ihdr=new Uint8Array(13);
  const v=new DataView(ihdr.buffer);
  v.setUint32(0,2,false);v.setUint32(4,2,false);
  ihdr[8]=8;ihdr[9]=6;
  const raw=new Uint8Array([0,r,g,b,255,r,g,b,255,
    0,r,g,b,255,r,g,b,255]);
  const items=[new Uint8Array([137,80,78,71,13,10,26,10]),
    chunk('IHDR',ihdr),chunk('IDAT',new Uint8Array(deflateSync(raw))),
    chunk('IEND',new Uint8Array())];
  const out=new Uint8Array(items.reduce((n,a)=>n+a.length,0));
  let at=0;for(const a of items){out.set(a,at);at+=a.length;}
  return out;
}
export function buildSyntheticMovingTexturedGlb(){
  const input=buildSyntheticSourceNormalGLB();
  const dv=new DataView(input),jsonLen=dv.getUint32(12,true),head=20+jsonLen;
  const root=JSON.parse(new TextDecoder().decode(new Uint8Array(input,20,jsonLen)).trim());
  const old=new Uint8Array(input,head+8,dv.getUint32(head,true));
  const source=[png(247,20,23),png(15,244,32)];
  let length=old.length;
  for(const bytes of source){
    root.bufferViews.push({buffer:0,byteOffset:length,byteLength:bytes.length});
    length+=align(bytes.length);
  }
  root.images=source.map((_,i)=>({
    name:'project_original_synthetic_'+i,
    bufferView:root.bufferViews.length-2+i,mimeType:'image/png'
  }));
  root.samplers=[{magFilter:9729,minFilter:9729,wrapS:33071,wrapT:33071}];
  root.textures=source.map((_,i)=>({source:i,sampler:0}));
  root.materials=source.map((_,i)=>({name:'synthetic_mat_'+i,
    pbrMetallicRoughness:{baseColorFactor:[1,1,1,1],
      metallicFactor:0,roughnessFactor:1,
      baseColorTexture:{index:i,texCoord:0}}}));
  for(let i=0;i<2;i++)root.meshes[i].primitives[0].material=i;
  const bin=new Uint8Array(length);bin.set(old);
  let offset=old.length;for(const bytes of source){bin.set(bytes,offset);offset+=align(bytes.length);}
  root.buffers[0].byteLength=bin.length;
  const json=new TextEncoder().encode(JSON.stringify(root)),jlen=align(json.length);
  const out=new ArrayBuffer(12+8+jlen+8+bin.length),v=new DataView(out);
  v.setUint32(0,0x46546c67,true);v.setUint32(4,2,true);
  v.setUint32(8,out.byteLength,true);v.setUint32(12,jlen,true);
  v.setUint32(16,0x4e4f534a,true);
  new Uint8Array(out,20,jlen).fill(32);
  new Uint8Array(out,20,json.length).set(json);
  const p=20+jlen;v.setUint32(p,bin.length,true);v.setUint32(p+4,0x004e4942,true);
  new Uint8Array(out,p+8,bin.length).set(bin);
  return out;
}
