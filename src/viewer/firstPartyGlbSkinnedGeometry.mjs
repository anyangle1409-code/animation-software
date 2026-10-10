/**
 * First-party STRICT bounded glTF 2.0 GLB geometry-only decoder.
 *
 * Not a complete glTF implementation: rejects/records unsupported features.
 * Does not execute, fetch, embed or redistribute assets, textures, code,
 * CT source meshes, external URIs or scripts.
 *
 * Output is a skin-ready geometry/skin data package for *separately proven*
 * rig-node mapping and first-party CPU/GPU skinning. No implicit anatomical
 * identity, right/left match, patient scaling, or production asset approval.
 */
import { validateNativeSkinnedMesh } from './firstPartyIndexedSkinnedMesh.mjs';

export const FIRST_PARTY_GLB_GATE = 'hgpt-strict-glb2-skinned-geometry-v1';
const MAGIC=0x46546c67,JSON_CHUNK=0x4e4f534a,BIN_CHUNK=0x004e4942;
const MAX_BYTES=32*1024*1024;
const MAX_VERTICES=250000;
const COMPONENTS={5121:1,5123:2,5125:4,5126:4};
const TUPLE_SIZE={SCALAR:1,VEC3:3,VEC4:4,MAT4:16};
const typesOK=values=>values.every(Number.isFinite);
function expect(test,message){if(!test)throw new RangeError('GLB rejection: '+message);}
function readGLB(input){
  expect(input instanceof ArrayBuffer,'raw ArrayBuffer required');
  expect(input.byteLength>=28 && input.byteLength<=MAX_BYTES,'GLB length exceeds prototype source limit');
  const view=new DataView(input);
  expect(view.getUint32(0,true)===MAGIC,'GLB magic');
  expect(view.getUint32(4,true)===2,'GLB 2.0 only');
  expect(view.getUint32(8,true)===input.byteLength,'header file size mismatch');
  let pos=12,chunks=[];
  while(pos<input.byteLength){
    expect(pos+8<=input.byteLength,'incomplete chunk header');
    const length=view.getUint32(pos,true),type=view.getUint32(pos+4,true);
    pos+=8;
    expect(length%4===0 && length<=MAX_BYTES && pos+length<=input.byteLength,'bad chunk length or alignment');
    chunks.push({type,start:pos,length});
    pos+=length;
  }
  expect(pos===input.byteLength,'trailing bytes');
  expect(chunks.length===2 && chunks[0].type===JSON_CHUNK && chunks[1].type===BIN_CHUNK,
    'exactly JSON then embedded binary chunk required; no trailing extensions');
  const decoder=new TextDecoder('utf-8',{fatal:true});
  const jsonString=decoder.decode(new Uint8Array(input,chunks[0].start,chunks[0].length))
    .replace(/[\u0020\u0000]+$/g,'');
  let gltf;
  try{gltf=JSON.parse(jsonString);}catch{throw new RangeError('GLB rejection: invalid UTF8 JSON chunk');}
  expect(gltf && typeof gltf==='object' && !Array.isArray(gltf),'JSON root object');
  return {gltf,view,binary:chunks[1]};
}
function identityNode(node){
  // No mesh-node/root correction implemented. No silent transform loss.
  const m=node.matrix;
  if(m){
    expect(Array.isArray(m)&&m.length===16,'invalid node 4x4');
    const identity=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
    return m.every((v,i)=>Number.isFinite(v)&&Math.abs(v-identity[i])<1e-6);
  }
  for(const [key,identity] of [
    ['translation',[0,0,0]],['rotation',[0,0,0,1]],['scale',[1,1,1]]
  ]){
    if(node[key] && (!Array.isArray(node[key]) || node[key].length!==identity.length ||
        !node[key].every((v,i)=>Number.isFinite(v)&&Math.abs(v-identity[i])<1e-6)))return false;
  }
  return true;
}
function readAccessor(root,view,binary,index,expectedType,componentAllow,requiredNormalized){
  const accessors=root.accessors||[],views=root.bufferViews||[];
  const a=accessors[index];
  expect(a && typeof a==='object' && !a.sparse,'accessor absent or sparse accessors unsupported');
  expect(a.type===expectedType,'attribute accessor type '+expectedType);
  expect(componentAllow.includes(a.componentType),'attribute component type unsupported');
  const compSize=COMPONENTS[a.componentType],tuple=TUPLE_SIZE[a.type];
  expect(Number.isSafeInteger(a.count)&&a.count>0&&a.count<=MAX_VERTICES*3,'bad accessor count');
  if(requiredNormalized===true)expect(a.componentType===5126 || a.normalized===true,
    'integer skin weights must declare normalized true');
  if(requiredNormalized===false)expect(!a.normalized,'normalized joint index or mesh index forbidden');
  expect(Number.isSafeInteger(a.bufferView)&&a.bufferView>=0,'no external/sparse accessor data');
  const bv=views[a.bufferView];
  expect(bv && bv.buffer===0,'embedded buffer 0 only');
  const bvOffset=bv.byteOffset??0,aOffset=a.byteOffset??0;
  expect(Number.isSafeInteger(bvOffset)&&bvOffset>=0&&Number.isSafeInteger(aOffset)&&aOffset>=0,
    'bad buffer/accessor offset');
  expect(Number.isSafeInteger(bv.byteLength)&&bv.byteLength>0,'bad buffer view length');
  const byteWidth=compSize*tuple;
  const stride=bv.byteStride??byteWidth;
  expect(Number.isSafeInteger(stride)&&stride>=byteWidth && stride<=252 && stride%compSize===0,
    'bad glTF byte stride');
  expect((bvOffset+aOffset)%compSize===0,'unaligned accessor');
  const end=aOffset+(a.count-1)*stride+byteWidth;
  expect(end<=bv.byteLength,'accessor escapes bufferView');
  expect(bvOffset+bv.byteLength<=root.buffers[0].byteLength,'bufferView exceeds declared BIN bytes');
  expect(bvOffset+bv.byteLength<=binary.length,'bufferView exceeds physical BIN bytes');
  const result=new Array(a.count*tuple);
  for(let i=0;i<a.count;i++)for(let k=0;k<tuple;k++){
    const offset=binary.start+bvOffset+aOffset+i*stride+k*compSize;
    let value;
    switch(a.componentType){
      case 5121:value=view.getUint8(offset);break;
      case 5123:value=view.getUint16(offset,true);break;
      case 5125:value=view.getUint32(offset,true);break;
      case 5126:value=view.getFloat32(offset,true);break;
      default:throw new Error('Unknown glTF component type');
    }
    if(a.componentType===5121&&a.normalized)value/=255;
    if(a.componentType===5123&&a.normalized)value/=65535;
    expect(Number.isFinite(value),'nonfinite glTF attribute');
    result[i*tuple+k]=value;
  }
  return {values:result,count:a.count,componentType:a.componentType};
}
export function parseRestrictedSkinnedGlb(input){
  const {gltf,view,binary}=readGLB(input);
  expect(gltf.asset?.version==='2.0','asset.version must be 2.0');
  expect(!gltf.extensionsRequired?.length && !gltf.extensionsUsed?.length,
    'extensions require independent implementation');
  expect(Array.isArray(gltf.buffers)&&gltf.buffers.length===1,'exactly one embedded BIN buffer');
  expect(!gltf.buffers[0].uri,'external/encoded buffer URI forbidden');
  expect(Number.isSafeInteger(gltf.buffers[0].byteLength)&&gltf.buffers[0].byteLength>0,
    'invalid embedded binary declared length');
  expect(binary.length>=gltf.buffers[0].byteLength &&
    binary.length-gltf.buffers[0].byteLength<4,'GLB BIN padding/length mismatch');
  expect(Array.isArray(gltf.meshes)&&gltf.meshes.length===1,'one mesh only');
  expect(Array.isArray(gltf.skins)&&gltf.skins.length===1,'one skin only');
  expect(Array.isArray(gltf.nodes)&&gltf.nodes.length>0&&gltf.nodes.length<=200,
    'node label count outside prototype range');
  expect(!gltf.images?.length && !gltf.textures?.length &&
    !gltf.animations?.length && !gltf.cameras?.length,
    'texture, animation, image and camera loading unsupported');
  const primitive=gltf.meshes[0]?.primitives;
  expect(Array.isArray(primitive)&&primitive.length===1,'single skinned primitive only');
  const p=primitive[0];
  expect((p.mode??4)===4,'TRIANGLES primitive only');
  expect(!p.targets?.length && p.indices!==undefined,'no morphs or unindexed primitives');
  expect(p.material===undefined,'material/textures not yet production-supported');
  const a=p.attributes;
  expect(a && ['POSITION','JOINTS_0','WEIGHTS_0'].every(k=>Number.isInteger(a[k])),
    'POSITION, JOINTS_0, WEIGHTS_0 are compulsory');
  const attrNames=Object.keys(a);
  expect(attrNames.every(k=>['POSITION','JOINTS_0','WEIGHTS_0','NORMAL'].includes(k)),
    'unhandled secondary influences, UVs, tangents, morph targets require new parser stage');
  const skin=gltf.skins[0];
  expect(Array.isArray(skin.joints)&&skin.joints.length>0&&skin.joints.length<=128,
    'explicit 1..128 skin joints required');
  expect(new Set(skin.joints).size===skin.joints.length,'duplicate palette nodes');
  expect(skin.joints.every(i=>Number.isSafeInteger(i)&&i>=0&&i<gltf.nodes.length),
    'bad bone node index');
  expect(Number.isSafeInteger(skin.inverseBindMatrices),'no inverse bind palette; no automatic bind assumptions');
  const meshes=gltf.nodes.map((n,i)=>({node:n,index:i})).filter(({node})=>node?.mesh===0);
  expect(meshes.length===1 && meshes[0].node.skin===0,'one explicit skinned mesh node');
  expect(identityNode(meshes[0].node),'nonidentity mesh root requires independent scene transforms');
  expect(!gltf.nodes.some(n=>Array.isArray(n.children)&&n.children.includes(meshes[0].index)),
    'mesh node is nested in a transformed parent');
  const namedJoints=skin.joints.map(i=>gltf.nodes[i].name);
  expect(namedJoints.every(n=>typeof n==='string'&&n.length>0&&n.length<=80),
    'explicit unique joint node names required for future canonical mapping');
  expect(new Set(namedJoints).size===namedJoints.length,'ambiguous duplicate joint names');
  const positions=readAccessor(gltf,view,binary,a.POSITION,'VEC3',[5126],false);
  const joints=readAccessor(gltf,view,binary,a.JOINTS_0,'VEC4',[5121,5123],false);
  const weights=readAccessor(gltf,view,binary,a.WEIGHTS_0,'VEC4',[5121,5123,5126],true);
  const faces=readAccessor(gltf,view,binary,p.indices,'SCALAR',[5121,5123,5125],false);
  const inv=readAccessor(gltf,view,binary,skin.inverseBindMatrices,'MAT4',[5126],false);
  expect(positions.count===joints.count && positions.count===weights.count,
    'per-vertex position/skin attribute count mismatch');
  expect(inv.count===skin.joints.length,'inverse bind count != skin bone palette count');
  expect(faces.count%3===0 && faces.count>=3,'indexed triangles required');
  let ignoredSourceNormals=false;
  if(a.NORMAL!==undefined){
    const normal=readAccessor(gltf,view,binary,a.NORMAL,'VEC3',[5126],false);
    expect(normal.count===positions.count,'normal count mismatch');
    ignoredSourceNormals=true;
  }
  const mesh={
    positions:new Float32Array(positions.values),
    indices:new (faces.componentType===5125?Uint32Array:Uint16Array)(faces.values),
    jointIndices:new Uint16Array(joints.values),
    weights:new Float32Array(weights.values),
    inverseBindMatrices:new Float32Array(inv.values),
  };
  const validation=validateNativeSkinnedMesh(mesh);
  expect(validation.vertices===positions.count && validation.triangles===faces.count/3,
    'source mesh skinning validation mismatch');
  const rejectedScaleOrPoseAssumptions={
    canonicalBoneMappingVerified:false,
    glTF_jointNodePoseToOriginalRigVerified:false,
    physicalSkeletonToHumanStatureRegistered:false,
    sourceProvenanceOrRedistributionApproved:false,
    sourceSkinningAppearanceValidated:false,
    originalFullBodyCharacterLoaded:false,
    allOriginalRuntimeDependenciesRemoved:false,
    productionReady:false,
  };
  return {
    kind:FIRST_PARTY_GLB_GATE,
    mesh,
    jointNodeNames:namedJoints,
    jointNodeIndices:[...skin.joints],
    audit:{
      loadedGeometryOnly:true,
      sourceFormat:'glTF 2.0 embedded GLB one mesh/primitive/skin',
      ignoredSourceNormalsAndRecomputeOnDeformation:ignoredSourceNormals,
      ignoredMaterials:false,
      sourceIsAutomaticallyApprovedAsFirstParty:false,
      vertices:validation.vertices,
      indexedTriangles:validation.triangles,
      bonePaletteCount:validation.bones,
      strictUnsupportedContentRejected:true,
      ...rejectedScaleOrPoseAssumptions,
    }
  };
}
