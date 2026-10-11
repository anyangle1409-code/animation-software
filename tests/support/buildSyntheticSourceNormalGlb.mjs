/**
 * Project-authored, synthetic, source-space unit NORMAL glTF GLB2 fixture.
 * Deliberately no patient anatomy, purchased texture or human model.
 */
import { buildSyntheticUV0Glb } from './buildSyntheticUV0Glb.mjs';
const align4=n=>(n+3)&~3;
function split(buffer){
  const d=new DataView(buffer),length=d.getUint32(12,true),bh=20+length;
  return {
    doc:JSON.parse(new TextDecoder().decode(new Uint8Array(buffer,20,length)).trim()),
    bin:new Uint8Array(buffer,bh+8,d.getUint32(bh,true))
  };
}
function write(doc,bin){
  const json=new TextEncoder().encode(JSON.stringify(doc)),size=align4(json.length);
  const buffer=new ArrayBuffer(12+8+size+8+bin.length);
  const d=new DataView(buffer);
  d.setUint32(0,0x46546c67,true);d.setUint32(4,2,true);
  d.setUint32(8,buffer.byteLength,true);d.setUint32(12,size,true);
  d.setUint32(16,0x4e4f534a,true);
  new Uint8Array(buffer,20,size).fill(32);
  new Uint8Array(buffer,20,json.length).set(json);
  const h=20+size;d.setUint32(h,bin.length,true);d.setUint32(h+4,0x004e4942,true);
  new Uint8Array(buffer,h+8,bin.length).set(bin);
  return buffer;
}
export function buildSyntheticSourceNormalGLB({
  meshCount=2,primitivesPerMesh=1,uv=true,addSourceColors=false,mutate
}={}){
  const input=buildSyntheticUV0Glb({meshCount,primitivesPerMesh,addSourceColors});
  const {doc,bin:original}=split(input);
  let offset=original.length;
  const appended=[];
  for(let m=0;m<doc.meshes.length;m++)
    for(let p=0;p<doc.meshes[m].primitives.length;p++){
      // Deliberately different per-source mesh/part NORMAL directions;
      // all vectors exact unit length, so a mistaken constant/default normal
      // cannot masquerade as successful source parsing.
      const normal=(m+p)%2===0?[0,0,1]:[0,1,0];
      const normalData=new Float32Array([...normal,...normal,...normal]);
      const data=new Uint8Array(normalData.buffer);
      doc.bufferViews.push({buffer:0,byteOffset:offset,byteLength:data.length});
      doc.accessors.push({
        bufferView:doc.bufferViews.length-1,componentType:5126,
        count:3,type:'VEC3'
      });
      doc.meshes[m].primitives[p].attributes.NORMAL=doc.accessors.length-1;
      if(!uv)delete doc.meshes[m].primitives[p].attributes.TEXCOORD_0;
      appended.push(data);offset+=data.length;
    }
  const bin=new Uint8Array(align4(offset));
  bin.set(original);
  let pos=original.length;
  for(const section of appended){bin.set(section,pos);pos+=section.length;}
  doc.buffers[0].byteLength=bin.length;
  mutate?.(doc,bin);
  return write(doc,bin);
}
