/**
 * Deterministic, project-original two-or-more primitive / mesh GLB fixture.
 * Synthetic triangles only; no real character or third-party model data.
 */
import { buildSyntheticFirstPartyGlb } from './buildSyntheticFirstPartyGlb.mjs';
const pad=n=>(n+3)&~3;
function extract(bytes){
  const d=new DataView(bytes),jlen=d.getUint32(12,true),bh=20+jlen;
  const root=JSON.parse(new TextDecoder().decode(new Uint8Array(bytes,20,jlen)).trim());
  return {root,bin:new Uint8Array(bytes,bh+8,d.getUint32(bh,true))};
}
function pack(root,bin){
  const text=new TextEncoder().encode(JSON.stringify(root)),jlen=pad(text.byteLength);
  const size=12+8+jlen+8+bin.byteLength,buffer=new ArrayBuffer(size);
  const d=new DataView(buffer);d.setUint32(0,0x46546c67,true);d.setUint32(4,2,true);
  d.setUint32(8,size,true);d.setUint32(12,jlen,true);d.setUint32(16,0x4e4f534a,true);
  new Uint8Array(buffer,20,jlen).fill(32);
  new Uint8Array(buffer,20,text.byteLength).set(text);
  const bh=20+jlen;d.setUint32(bh,bin.byteLength,true);
  d.setUint32(bh+4,0x004e4942,true);
  new Uint8Array(buffer,bh+8,bin.byteLength).set(bin);
  return buffer;
}
export function buildSyntheticBatchedGlb({meshCount=2,primitivesPerMesh=1,allowProvisionalPilot=false,mutate}={}){
  const maxMeshes=allowProvisionalPilot?24:4;
  const maxParts=allowProvisionalPilot?24:8;
  if(!Number.isInteger(meshCount)||meshCount<1||meshCount>maxMeshes ||
    !Number.isInteger(primitivesPerMesh)||primitivesPerMesh<1||
    primitivesPerMesh>(allowProvisionalPilot?24:4)||
    meshCount*primitivesPerMesh>maxParts)
    throw new RangeError('Synthetic test fixture budget invalid');
  const original=extract(buildSyntheticFirstPartyGlb());
  const root=original.root;
  const prim=root.meshes[0].primitives[0];
  let parts=[original.bin];
  let offset=original.bin.byteLength;
  const meshes=[];
  for(let m=0;m<meshCount;m++){
    const primitives=[];
    for(let p=0;p<primitivesPerMesh;p++){
      const next=structuredClone(prim);
      if(m!==0 || p!==0){
        const coords=new Float32Array([m*1.5+p*.45,m*.25,0,
          1+m*1.5+p*.45,m*.25,0,
          m*1.5+p*.45,1+m*.25,0]);
        const src=new Uint8Array(coords.buffer);
        root.bufferViews.push({buffer:0,byteOffset:offset,byteLength:src.byteLength});
        root.accessors.push({
          bufferView:root.bufferViews.length-1,
          componentType:5126,count:3,type:'VEC3'
        });
        next.attributes.POSITION=root.accessors.length-1;
        parts.push(src);offset+=src.byteLength;
      }
      primitives.push(next);
    }
    meshes.push({name:'original_synthetic_mesh_'+m,primitives});
    if(m!==0){
      root.nodes.push({name:'synthetic_mesh_node_'+m,mesh:m,skin:0});
      root.scenes[0].nodes.push(root.nodes.length-1);
    }
  }
  root.meshes=meshes;
  const bin=new Uint8Array(pad(offset));
  let pos=0;for(const part of parts){bin.set(part,pos);pos+=part.length;}
  root.buffers[0].byteLength=bin.byteLength;
  if(mutate)mutate(root,bin);
  return pack(root,bin);
}
