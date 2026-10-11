import test from 'node:test';
import assert from 'node:assert/strict';
import {deflateSync} from 'node:zlib';
import {buildSyntheticBatchedGlb} from './support/buildSyntheticBatchedGlb.mjs';
import {parseRestrictedBatchedSkinnedGlb as parse}
  from '../src/viewer/firstPartyGlbSkinnedBatches.mjs';
import {HGPT_EMBEDDED_PNG_KIND}
  from '../src/viewer/firstPartyEmbeddedPngSource.mjs';

const pad=x=>(x+3)&~3;
function extract(buffer){
  const dv=new DataView(buffer),n=dv.getUint32(12,true),b=20+n;
  return {root:JSON.parse(new TextDecoder().decode(
    new Uint8Array(buffer,20,n)).trim()),
    bin:new Uint8Array(buffer,b+8,dv.getUint32(b,true))};
}
function pack(root,bin){
  const text=new TextEncoder().encode(JSON.stringify(root));
  const jlen=pad(text.length),total=12+8+jlen+8+bin.length;
  const a=new ArrayBuffer(total),dv=new DataView(a);
  dv.setUint32(0,0x46546c67,true);dv.setUint32(4,2,true);
  dv.setUint32(8,total,true);dv.setUint32(12,jlen,true);
  dv.setUint32(16,0x4e4f534a,true);
  new Uint8Array(a,20,jlen).fill(32);
  new Uint8Array(a,20,text.length).set(text);
  const at=20+jlen;
  dv.setUint32(at,bin.length,true);dv.setUint32(at+4,0x004e4942,true);
  new Uint8Array(a,at+8,bin.length).set(bin);
  return a;
}
function crc(source){
  let c=0xffffffff;
  for(const v of source){
    c^=v;
    for(let k=0;k<8;k++)c=(c>>>1)^((c&1)?0xedb88320:0);
  }
  return (c^0xffffffff)>>>0;
}
function chunk(label,data){
  const tag=new TextEncoder().encode(label),a=new Uint8Array(12+data.length);
  const d=new DataView(a.buffer);d.setUint32(0,data.length,false);
  a.set(tag,4);a.set(data,8);
  d.setUint32(a.length-4,crc(a.subarray(4,a.length-4)),false);
  return a;
}
function png({width=1,height=1,colorType=6,extraChunk=null}={}){
  const header=new Uint8Array(13),d=new DataView(header.buffer);
  d.setUint32(0,width,false);d.setUint32(4,height,false);
  header[8]=8;header[9]=colorType;
  const raw=new Uint8Array(colorType===2?[0,240,160,80]:[0,240,160,80,255]);
  const chunks=[chunk('IHDR',header)];
  if(extraChunk)chunks.push(chunk(extraChunk,new Uint8Array([1,2])));
  chunks.push(chunk('IDAT',new Uint8Array(deflateSync(raw))));
  chunks.push(chunk('IEND',new Uint8Array()));
  const signature=new Uint8Array([137,80,78,71,13,10,26,10]);
  const size=8+chunks.reduce((n,x)=>n+x.length,0);
  const output=new Uint8Array(size);
  output.set(signature,0);let at=8;
  for(const c of chunks){output.set(c,at);at+=c.length}
  return output;
}
const texOpts={allowSourceFlatColors:true,allowSourceUV0:true,
  allowEmbeddedPngBaseColor:true};
function textured({pngOpts={},mutate}={}){
  const {root,bin:original}=extract(buildSyntheticBatchedGlb());
  const bytes=[];let pos=original.length;
  const append=(body)=>{
    const start=pos;
    bytes.push({start,body});
    pos+=pad(body.length);
    return {buffer:0,byteOffset:start,byteLength:body.length};
  };
  for(const mesh of root.meshes)for(const primitive of mesh.primitives){
    const uv=new Float32Array([0,0,1,0,0,1]);
    const bv=append(new Uint8Array(uv.buffer));
    root.bufferViews.push(bv);
    root.accessors.push({bufferView:root.bufferViews.length-1,
      componentType:5126,count:3,type:'VEC2'});
    primitive.attributes.TEXCOORD_0=root.accessors.length-1;
    primitive.material=0;
  }
  const imageView=append(png(pngOpts));
  root.bufferViews.push(imageView);
  root.images=[{bufferView:root.bufferViews.length-1,mimeType:'image/png'}];
  root.textures=[{source:0,sampler:0}];
  root.samplers=[{magFilter:9729,minFilter:9729,wrapS:33071,wrapT:33071}];
  root.materials=[{
    name:'project_owned_matte',
    pbrMetallicRoughness:{baseColorFactor:[.8,.7,.6,1],
      metallicFactor:0,roughnessFactor:1,baseColorTexture:{index:0,texCoord:0}},
  }];
  const combined=new Uint8Array(pos);
  combined.set(original);
  for(const {start,body}of bytes)combined.set(body,start);
  root.buffers[0].byteLength=combined.length;
  if(mutate)mutate(root,combined);
  return pack(root,combined);
}
const reject=(edit,re=/Embedded PNG rejection|GLB batch rejection/)=>{
  assert.throws(()=>parse(textured({mutate:edit}),texOpts),re);
};
test('opted-in source-only PNG texture intake preserves every mesh, UV and image bytes',()=>{
  const input=textured(),copy=new Uint8Array(input).slice();
  const result=parse(input,texOpts);
  assert.deepEqual(new Uint8Array(input),copy);
  assert.equal(result.batches.length,2);
  assert.equal(result.audit.embeddedPngBaseColorSourceValidated,true);
  assert.equal(result.audit.textureSamplingImplemented,false);
  assert.equal(result.audit.productionRuntimeReady,false);
  for(const p of result.batches){
    assert.equal(p.sourceBaseColorPng.kind,HGPT_EMBEDDED_PNG_KIND);
    assert.equal(p.sourceBaseColorPng.width,1);
    assert.equal(p.sourceBaseColorPng.height,1);
    assert.equal(p.sourceBaseColorPng.bytes[0],137);
    assert.equal(p.sourceUV0.length,6);
    assert.deepEqual(p.materialColor,[.8,.7,.6]);
    assert.deepEqual([...p.parsed.mesh.weights.slice(0,4)],[.75,.25,0,0]);
  }
  assert.equal(result.audit.clinicalAnatomyApproved,false);
});
test('inherited source GLB loader still refuses PNG images unless opted in explicitly',()=>{
  assert.throws(()=>parse(textured()),/materials refused/);
  assert.throws(()=>parse(textured(),{
    allowSourceFlatColors:true,allowSourceUV0:true
  }),/texture\/unsupported/);
  assert.throws(()=>parse(textured(),{
    allowEmbeddedPngBaseColor:true,allowSourceUV0:true
  }),/requires flat colour/);
  assert.throws(()=>parse(textured(),{
    allowEmbeddedPngBaseColor:true,allowSourceFlatColors:true
  }),/requires flat colour and UV0/);
});
test('rejects URI images, mime substitution and unreferenced texture fields',()=>{
  reject(r=>{r.images[0].uri='https://example.invalid/x.png'},/must be embedded/);
  reject(r=>{r.images[0].mimeType='image/jpeg'},/embedded PNG/);
  reject(r=>{r.textures[0].source=9},/explicit embedded image/);
  reject(r=>{r.textures[0].extensions={foo:1}},/explicit embedded image/);
  reject(r=>{r.textures.push({source:0,sampler:0})},/unused embedded/);
  reject(r=>{r.images.push({...r.images[0]})},/unused source image/);
  reject(r=>{r.samplers.push({...r.samplers[0]})},/unused source image or sampler/);
});
test('rejects unsupported sampler, UV set, unbound image and missing source UVs',()=>{
  reject(r=>{r.samplers[0].wrapS=10497},/linear clamp-to-edge/);
  reject(r=>{r.samplers[0].minFilter=9987},/linear clamp-to-edge/);
  reject(r=>{r.samplers[0].magFilter=9728},/linear clamp-to-edge/);
  reject(r=>{r.materials[0].pbrMetallicRoughness.baseColorTexture.texCoord=1},
    /baseColorTexture link/);
  reject(r=>{delete r.meshes[1].primitives[0].attributes.TEXCOORD_0},/UV0/);
  reject(r=>{delete r.materials[0].pbrMetallicRoughness.baseColorTexture},
    /unused embedded/);
  reject(r=>{r.materials[0].normalTexture={index:0}},/unsupported glTF/);
});
test('source image data cannot alias position/skin accessor or escape the declared BIN',()=>{
  reject(r=>{r.images[0].bufferView=0},/cannot alias/);
  reject(r=>{r.bufferViews[r.images[0].bufferView].byteLength=99999999},
    /outside aligned/);
  reject(r=>{r.bufferViews[r.images[0].bufferView].byteOffset=1},
    /outside aligned/);
  reject(r=>{r.images[0].bufferView=999},/outside aligned/);
});
test('valid structurally bounded PNG dimensions, signature and CRC must match',()=>{
  assert.throws(()=>parse(textured({pngOpts:{width:5000}}),texOpts),
    /dimensions exceed/);
  assert.throws(()=>parse(textured({pngOpts:{height:3000,width:3000}}),texOpts),
    /dimensions exceed/);
  assert.throws(()=>parse(textured({pngOpts:{colorType:0}}),texOpts),
    /8-bit RGB\/RGBA/);
  assert.throws(()=>parse(textured({pngOpts:{extraChunk:'tEXt'}}),texOpts),
    /unsupported PNG chunk/);
  reject((root,bin)=>{
    const view=root.bufferViews[root.images[0].bufferView];
    bin[view.byteOffset]^=1;
  },/signature/);
  reject((root,bin)=>{
    const view=root.bufferViews[root.images[0].bufferView];
    bin[view.byteOffset+8+4+13]^=1;
  },/CRC mismatch/);
});
test('bad secondary primitive cannot hide invalid source texture data',()=>{
  reject(r=>{r.meshes[1].primitives[0].mode=1},/TRIANGLES/);
  reject(r=>{r.meshes[1].primitives[0].attributes.POSITION=999},/accessor/);
});
test('all opt-in checks retain source-only no human-reality and no-network flags',()=>{
  const r=parse(textured(),texOpts);
  assert.equal(r.audit.noExternalModelCodeUsed,true);
  assert.equal(r.audit.actualOriginalHumanMeshUsed,false);
  assert.equal(r.audit.rightsAndProvenanceApproved,false);
  assert.equal(r.audit.productionRuntimeReady,false);
  assert.equal(r.audit.textureSamplingImplemented,false);
});
