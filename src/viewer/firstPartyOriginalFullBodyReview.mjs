/**
 * G4p: original full-body REVIEW-ONLY glTF 2.0 GLB intake.
 *
 * Preserves the source's 67-joint tree, 4-weight body mesh, authored normals,
 * original flat baseColor and SIX sparse shoulder corrective deltas WITHOUT
 * promoting any correction to an actual pose or modifying a single source byte.
 *
 * This adapter is separate from the frozen strict single/batched GLB parsers.
 * The only change to the inherited decoder is an ephemeral GLB validation copy
 * with already individually checked material / sparse morph / identity wrapper
 * metadata removed. Source inverse binds, joint names, positions and weights
 * are verified through the inherited parser + independent WORLD REST check.
 *
 * No fetch, third-party loader, Blender, anatomical axis inference or rights
 * and production approval. Actual source model is available in the owner's
 * private Library, never stored in repository code or its CI fixtures.
 */
import {parseRestrictedSkinnedGlb}
  from './firstPartyGlbSkinnedGeometry.mjs';
import {readRestrictedGlbNormals}
  from './firstPartyGlbSourceNormals.mjs';
import {validateNativeGLBToRigBinding}
  from './firstPartyGlbRigBindingContract.mjs';
import {multiplyNativeMat4}
  from './firstPartyWebGL2SkeletonPreview.mjs';

export const HGPT_ORIGINAL_FULLBODY_REVIEW_KIND=
  'hgpt-original-fullbody-review-only-source-v1';
const fail=s=>{throw new RangeError('Original full-body review GLB rejected: '+s)};
const must=(yes,s)=>{if(!yes)fail(s)};
const obj=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const array=Array.isArray;
const ID=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
const align=n=>(n+3)&~3;
const MAX_BYTES=16*1024*1024,MAX_VERTEX=250000;
const morphNames=[
  'HGPT_SHOULDER_CORR_L','HGPT_SHOULDER_CORR_R',
  'HGPT_SHOULDER_FLEX_L','HGPT_SHOULDER_FLEX_R',
  'HGPT_SHOULDER_SCAP_L','HGPT_SHOULDER_SCAP_R'
];
function unpack(buffer){
  must(buffer instanceof ArrayBuffer &&
    buffer.byteLength>=28&&buffer.byteLength<=MAX_BYTES,
    'bounded raw source GLB ArrayBuffer required');
  const v=new DataView(buffer);
  must(v.getUint32(0,true)===0x46546c67 &&
    v.getUint32(4,true)===2 &&
    v.getUint32(8,true)===buffer.byteLength,'complete glTF2 GLB header');
  const jlen=v.getUint32(12,true),bhead=20+jlen;
  must(jlen%4===0&&jlen>0&&bhead+8<=buffer.byteLength &&
    v.getUint32(16,true)===0x4e4f534a,'bounded GLB JSON chunk required');
  const blen=v.getUint32(bhead,true);
  must(blen%4===0&&v.getUint32(bhead+4,true)===0x004e4942 &&
    bhead+8+blen===buffer.byteLength,'one exact embedded BIN chunk only');
  let root;
  try{root=JSON.parse(new TextDecoder('utf-8',{fatal:true})
    .decode(new Uint8Array(buffer,20,jlen)).replace(/[ \0]+$/g,''));}
  catch{fail('GLB JSON malformed')}
  must(obj(root)&&root.asset?.version==='2.0' &&
    !root.extensionsUsed?.length&&!root.extensionsRequired?.length,
    'unsupported glTF root/extension');
  must(array(root.buffers)&&root.buffers.length===1 &&
    root.buffers[0].uri===undefined &&
    Number.isSafeInteger(root.buffers[0].byteLength)&&
    root.buffers[0].byteLength>0 &&
    blen-root.buffers[0].byteLength>=0 &&
    blen-root.buffers[0].byteLength<4,
    'GLB must contain exactly one bounded private embedded buffer');
  must(!root.images?.length&&!root.textures?.length &&
    !root.animations?.length&&!root.cameras?.length,
    'no external media, embedded animation or camera import');
  return {root,bin:new Uint8Array(buffer,bhead+8,blen)};
}
function pack(root,bin){
  const j=new TextEncoder().encode(JSON.stringify(root)),jl=align(j.length);
  const total=12+8+jl+8+bin.length;
  must(total<=MAX_BYTES,'temporary strict primitive GLB is too large');
  const b=new ArrayBuffer(total),v=new DataView(b);
  v.setUint32(0,0x46546c67,true);v.setUint32(4,2,true);
  v.setUint32(8,total,true);v.setUint32(12,jl,true);
  v.setUint32(16,0x4e4f534a,true);
  new Uint8Array(b,20,jl).fill(32);
  new Uint8Array(b,20,j.length).set(j);
  v.setUint32(20+jl,bin.length,true);
  v.setUint32(24+jl,0x004e4942,true);
  new Uint8Array(b,28+jl).set(bin);
  return b;
}
function validMatrix(m,label){
  must((array(m)||m instanceof Float32Array)&&m.length===16 &&
    Array.from(m).every(finite),'nonfinite source matrix '+label);
  must(Math.abs(m[3])+Math.abs(m[7])+Math.abs(m[11])+
    Math.abs(m[15]-1)<1e-4,'nonaffine source '+label);
  const a=[m[0],m[1],m[2]],b=[m[4],m[5],m[6]],c=[m[8],m[9],m[10]];
  const len=u=>Math.hypot(...u);
  const dot=(u,v)=>u.reduce((s,n,i)=>s+n*v[i],0);
  const cross=[a[1]*b[2]-a[2]*b[1],
    a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
  must(Math.abs(len(a)-1)<2e-4&&Math.abs(len(b)-1)<2e-4&&
    Math.abs(len(c)-1)<2e-4 &&
    Math.abs(dot(a,b))<2e-4&&Math.abs(dot(a,c))<2e-4&&
    Math.abs(dot(b,c))<2e-4&&Math.abs(dot(cross,c)-1)<3e-4,
    'nonrigid/reflected source rest '+label);
  return m;
}
function local(n,label){
  must(obj(n),'source hierarchy node must be object');
  if(n.matrix!==undefined){
    must(n.rotation===undefined&&n.scale===undefined&&
      n.translation===undefined,'node cannot combine TRS with matrix');
    return validMatrix(n.matrix,label);
  }
  const t=n.translation??[0,0,0],q=n.rotation??[0,0,0,1],
    s=n.scale??[1,1,1];
  must(array(t)&&t.length===3&&t.every(finite)&&
    array(s)&&s.length===3&&s.every(finite)&&
    array(q)&&q.length===4&&q.every(finite),
    'source joint TRS invalid '+label);
  const [x,y,z,w]=q,norm=Math.hypot(...q);
  must(Math.abs(norm-1)<.001,'source joint quaternion not unit '+label);
  const X=x/norm,Y=y/norm,Z=z/norm,W=w/norm;
  return validMatrix([
    (1-2*(Y*Y+Z*Z))*s[0],(2*(X*Y+Z*W))*s[0],(2*(X*Z-Y*W))*s[0],0,
    (2*(X*Y-Z*W))*s[1],(1-2*(X*X+Z*Z))*s[1],(2*(Y*Z+X*W))*s[1],0,
    (2*(X*Z+Y*W))*s[2],(2*(Y*Z-X*W))*s[2],(1-2*(X*X+Y*Y))*s[2],0,
    ...t,1
  ],label);
}
function originalRest(root,meshNodeIndex){
  must(array(root.scenes)&&root.scenes.length===1&&root.scene===0&&
    array(root.scenes[0].nodes)&&root.scenes[0].nodes.length===1,
    'one explicit original scene root required');
  const nodes=root.nodes,parents=Array(nodes.length).fill(-1);
  must(array(nodes)&&nodes.length>=2&&nodes.length<=256,
    'bounded original source joint hierarchy required');
  for(let i=0;i<nodes.length;i++){
    const children=nodes[i].children;
    if(children===undefined)continue;
    must(array(children)&&new Set(children).size===children.length,
      'source hierarchy duplicate children forbidden');
    for(const c of children){
      must(Number.isSafeInteger(c)&&c>=0&&c<nodes.length&&
        c!==i&&parents[c]===-1,'cyclic/duplicated source parent');
      parents[c]=i;
    }
  }
  const sceneRoot=root.scenes[0].nodes[0];
  must(parents[sceneRoot]===-1,'original source root cannot be nested');
  const mem=new Map(),active=new Set();
  function world(index){
    if(mem.has(index))return mem.get(index);
    must(!active.has(index),'cyclic original joint hierarchy');
    active.add(index);
    const own=local(nodes[index],nodes[index].name||String(index));
    const m=parents[index]===-1?new Float32Array(own):
      multiplyNativeMat4(world(parents[index]),new Float32Array(own));
    validMatrix(m,nodes[index].name||String(index));
    active.delete(index);mem.set(index,m);return m;
  }
  const skin=root.skins[0],jointIndices=skin.joints;
  must(array(jointIndices)&&jointIndices.length>=1 &&
    jointIndices.length<=128&&
    new Set(jointIndices).size===jointIndices.length,
    'unique source joint palette required');
  const names=jointIndices.map(i=>{
    must(Number.isSafeInteger(i)&&i>=0&&i<nodes.length,
      'source skin joint node index invalid');
    let j=i,seen=new Set();
    while(j!==-1){
      must(!seen.has(j),'cycle in source joint parent chain');
      seen.add(j);if(j===sceneRoot)break;j=parents[j];
    }
    must(j===sceneRoot,'source skin joint not reachable from scene');
    return nodes[i].name;
  });
  must(names.every(n=>typeof n==='string'&&n.length>0&&n.length<=80) &&
    new Set(names).size===names.length,'source joint names must be unique');
  const chain=[],seen=new Set();
  let n=meshNodeIndex;
  while(n!==sceneRoot){
    must(n!==-1&&!seen.has(n),'skinned mesh not in unique scene tree');
    seen.add(n);chain.push(n);n=parents[n];
  }
  must(chain.length>=1&&local(nodes[meshNodeIndex],'source mesh node'),
    'skinned mesh node invalid');
  for(const ni of chain.slice(1)){
    const m=local(nodes[ni],nodes[ni].name||String(ni));
    must(m.every((v,i)=>Math.abs(v-ID[i])<1e-5),
      'nonidentity source wrapper requires separate proven transform');
  }
  const meshWorld=world(meshNodeIndex);
  must(meshWorld.every((v,i)=>Math.abs(v-ID[i])<1e-5),
    'original mesh node must be same-frame identity at source rest');
  return {names,matrices:jointIndices.map(i=>new Float32Array(world(i))),
    sourceMeshNodeParent:parents[meshNodeIndex],sourceRoot:sceneRoot};
}
function accessorSparse(root,bin,index,vertexCount,label){
  const a=root.accessors?.[index],sp=a?.sparse;
  must(obj(a)&&a.count===vertexCount&&a.type==='VEC3'&&
    a.componentType===5126&&!a.normalized&&
    a.bufferView===undefined&&a.byteOffset===undefined&&
    obj(sp)&&Number.isSafeInteger(sp.count)&&sp.count>0&&
    sp.count<=vertexCount,'bounded zero-based sparse VEC3 expected '+label);
  const idx=sp.indices,vals=sp.values;
  must(obj(idx)&&obj(vals)&&
    [5121,5123,5125].includes(idx.componentType) &&
    Number.isSafeInteger(idx.bufferView)&&
    Number.isSafeInteger(vals.bufferView)&&
    (idx.byteOffset===undefined||idx.byteOffset===0)&&
    (vals.byteOffset===undefined||vals.byteOffset===0),
    'sparse source indices/deltas invalid '+label);
  const views=root.bufferViews,iv=views[idx.bufferView],vv=views[vals.bufferView];
  const size={5121:1,5123:2,5125:4}[idx.componentType];
  must(iv?.buffer===0&&vv?.buffer===0&&
    iv.byteStride===undefined&&vv.byteStride===undefined&&
    Number.isSafeInteger(iv.byteLength)&&Number.isSafeInteger(vv.byteLength)&&
    iv.byteLength>=sp.count*size&&vv.byteLength>=sp.count*12&&
    Number.isSafeInteger(iv.byteOffset)&&Number.isSafeInteger(vv.byteOffset)&&
    iv.byteOffset>=0&&vv.byteOffset>=0&&
    iv.byteOffset+iv.byteLength<=bin.length&&
    vv.byteOffset+vv.byteLength<=bin.length&&
    iv.byteOffset%size===0&&vv.byteOffset%4===0,
    'out-of-range sparse source bufferView '+label);
  const read=new DataView(bin.buffer,bin.byteOffset,bin.byteLength);
  const indices=new Uint32Array(sp.count),delta=new Float32Array(sp.count*3);
  let max=0;
  for(let i=0;i<sp.count;i++){
    const offset=iv.byteOffset+i*size;
    const j=size===1?read.getUint8(offset):
      size===2?read.getUint16(offset,true):read.getUint32(offset,true);
    must(j<vertexCount&&(i===0||j>indices[i-1]),
      'sparse source vertex indices must increase uniquely '+label);
    indices[i]=j;
    for(let k=0;k<3;k++){
      const value=read.getFloat32(vv.byteOffset+12*i+4*k,true);
      must(finite(value)&&Math.abs(value)<4,
        'nonfinite/unbounded sparse morph delta '+label);
      delta[i*3+k]=value;max=Math.max(max,Math.abs(value));
    }
  }
  return {changedVertices:sp.count,indices,delta,maxAbsDelta:max};
}
function sourceMorphs(root,bin,primitive,vertexCount){
  const targets=primitive.targets,names=root.meshes[0].extras?.targetNames;
  must(array(targets)&&targets.length===6 &&
    array(names)&&names.length===6 &&
    names.every((n,i)=>n===morphNames[i]),
    'six explicitly named original shoulder source correctives required');
  must(array(root.meshes[0].weights)&&root.meshes[0].weights.length===6 &&
    root.meshes[0].weights.every(w=>w===0),
    'source corrective weights must be zero at rest; no automatic animation');
  return Object.freeze(targets.map((t,i)=>{
    must(obj(t)&&Object.keys(t).length===2 &&
      Number.isSafeInteger(t.POSITION)&&Number.isSafeInteger(t.NORMAL) &&
      new Set(Object.keys(t)).size===2,
      'morph must have exactly source POSITION/NORMAL deltas');
    const pos=accessorSparse(root,bin,t.POSITION,vertexCount,
      morphNames[i]+'.POSITION');
    const norm=accessorSparse(root,bin,t.NORMAL,vertexCount,
      morphNames[i]+'.NORMAL');
    return Object.freeze({name:morphNames[i],
      positionChangedVertices:pos.changedVertices,
      normalChangedVertices:norm.changedVertices,
      sourcePositionDelta:pos,
      sourceNormalDelta:norm,
      restWeight:0,
      actualCorrectiveSynthesisValidated:false});
  }));
}
function material(root,p){
  must(array(root.materials)&&root.materials.length===1 &&
    p.material===0,'single explicit original body material required');
  const m=root.materials[0],pbr=m.pbrMetallicRoughness;
  must(obj(m)&&Object.keys(m).every(k=>
    ['name','doubleSided','pbrMetallicRoughness','alphaMode'].includes(k)) &&
    (m.alphaMode===undefined||m.alphaMode==='OPAQUE') &&
    typeof m.doubleSided==='boolean'&&
    obj(pbr)&&Object.keys(pbr).every(k=>
      ['baseColorFactor','metallicFactor','roughnessFactor'].includes(k)) &&
    pbr.metallicFactor===0&&finite(pbr.roughnessFactor)&&
    pbr.roughnessFactor>=0&&pbr.roughnessFactor<=1 &&
    array(pbr.baseColorFactor)&&pbr.baseColorFactor.length===4 &&
    pbr.baseColorFactor.every(x=>finite(x)&&x>=0&&x<=1)&&
    pbr.baseColorFactor[3]===1,
    'bounded original opaque untextured body material only');
  return Object.freeze({sourceBaseColor:Object.freeze(pbr.baseColorFactor.slice(0,3)),
    sourceDoubleSided:m.doubleSided,sourceRoughness:pbr.roughnessFactor,
    physicalPBRLightingImplemented:false});
}
/**
 * Use only for explicitly owner-supplied original Work review GLB files.
 * Source SHA is mandatory; it is checked BEFORE copying/splitting metadata.
 * The returned rest-source morphs are not animated or clinically approved.
 */
export async function parseOriginalFullBodyReviewGLB(input,{expectedSha256}={}){
  must(typeof expectedSha256==='string'&&/^[a-f0-9]{64}$/.test(expectedSha256),
    'caller must supply previously recorded exact source SHA-256');
  must(input instanceof ArrayBuffer,'raw original ArrayBuffer required');
  const bytes=input.slice(0);
  const digest=await globalThis.crypto.subtle.digest('SHA-256',bytes);
  const sha=Array.from(new Uint8Array(digest),x=>x.toString(16).padStart(2,'0')).join('');
  must(sha===expectedSha256,'original Work full-body GLB source SHA mismatch');
  const {root,bin}=unpack(bytes);
  must(array(root.meshes)&&root.meshes.length===1&&
    array(root.skins)&&root.skins.length===1 &&
    array(root.nodes)&&root.nodes.length<=256,
    'one original body mesh, one complete runtime skin expected');
  const primitives=root.meshes[0].primitives;
  must(array(primitives)&&primitives.length===1 &&
    (primitives[0].mode??4)===4 &&
    Number.isSafeInteger(primitives[0].indices),
    'one fully indexed TRIANGLES body expected');
  const p=primitives[0],attrib=p.attributes;
  must(obj(attrib)&&Object.keys(attrib).sort().join(',')===
    ['POSITION','NORMAL','JOINTS_0','WEIGHTS_0'].sort().join(','),
    'original full body needs only first four joint influences and source normals');
  const vertexCount=root.accessors?.[attrib.POSITION]?.count;
  must(Number.isSafeInteger(vertexCount)&&vertexCount>=3&&
    vertexCount<=MAX_VERTEX,'bounded body source vertices');
  const nodes=root.nodes,meshNodes=nodes.map((n,i)=>n.mesh===0?i:-1)
    .filter(i=>i>=0);
  must(meshNodes.length===1&&nodes[meshNodes[0]].skin===0,
    'one original skinned mesh node required');
  // Project-authoring metadata is a claim, not rights evidence. Explicitly
  // require it to remain unapproved throughout a review-only importer.
  must(nodes[meshNodes[0]].extras?.hgpt_export_production_approved===false &&
    nodes[meshNodes[0]].extras?.hgpt_production_ready===false,
    'original author must NOT label source body as production approved');
  const mat=material(root,p),morphs=sourceMorphs(root,bin,p,vertexCount),
    source=originalRest(root,meshNodes[0]);
  // Source normal accessor independently checked by the existing strict gate.
  const originalNormals=readRestrictedGlbNormals(root,bin,attrib.NORMAL,vertexCount);
  // Reuse the old proven triangle/weights/inverseBind reader, but only inside
  // a temporary validation GLB. Original bytes and original morphs untouched.
  const split=structuredClone(root);
  delete split.meshes[0].primitives[0].targets;
  delete split.meshes[0].primitives[0].material;
  delete split.meshes[0].weights;
  delete split.materials;
  for(const n of split.nodes){
    if(!array(n.children))continue;
    n.children=n.children.filter(i=>i!==meshNodes[0]);
    if(!n.children.length)delete n.children;
  }
  split.scenes[0].nodes.push(meshNodes[0]);
  const parsed=parseRestrictedSkinnedGlb(pack(split,bin));
  must(parsed.audit.vertices===vertexCount&&
    parsed.audit.bonePaletteCount===source.names.length&&
    parsed.jointNodeNames.every((n,i)=>n===source.names[i]),
    'original source bone order or original vertex count changed in validation');
  const nameMap=Object.fromEntries(source.names.map(name=>[name,name])),
    restMap=Object.fromEntries(source.names.map((name,i)=>
      [name,Array.from(source.matrices[i])]));
  const plan=validateNativeGLBToRigBinding(parsed,{
    sourceToCanonical:nameMap,
    allowedCanonicalNames:source.names,
    canonicalRestWorldByBone:restMap,
  });
  must(plan.maximumMatrixResidual<=1e-4,
    'source original joint world rest does not invert source IBM');
  return Object.freeze({
    kind:HGPT_ORIGINAL_FULLBODY_REVIEW_KIND,
    sourceSha256:sha,originalSourceBytesUnmodified:true,
    mesh:parsed.mesh,
    sourceNormals:originalNormals,
    jointNames:Object.freeze([...source.names]),
    restWorldByJointName:Object.freeze(restMap),
    sourceMaterial:mat,
    sparseCorrectives:morphs,
    vertices:vertexCount,triangles:parsed.audit.indexedTriangles,
    bones:source.names.length,
    audit:Object.freeze({
      originalSourceSHA256Verified:true,
      actualSourceJointRestAndInverseBindMatched:true,
      maximumRestInverseBindResidual:plan.maximumMatrixResidual,
      sparseCorrectiveDataValidated:true,
      sparseCorrectiveWeightsAtRestAllZero:true,
      sourceMeshWorldTransformIdentity:true,
      sourceNormalsValidated:true,
      originalSourceJointGeometryChanged:false,
      fullBodyMotionRetargeted:false,
      correctiveMorphGPUBlendImplemented:false,
      independentAnatomicalAcceptance:false,
      sourceRightsIndependentlyReviewed:false,
      productionReady:false,
    })
  });
}
