/**
 * Home Gym PT G1: bounded first-party MULTI-PRIMITIVE / MULTI-MESH GLB batch.
 *
 * This COMPATIBILITY ADAPTER delegates actual binary accessor validation to the
 * existing strict, separately proven one-mesh GLB parser. Every primitive is
 * converted to an independent single-primitive *in-memory GLB* and checked by
 * that original parser. The old parser's fail-closed behaviour stays unchanged.
 *
 * Supports 1 skin shared by 1..4 meshes and 2..8 TRIANGLES primitives overall,
 * each mesh attached to exactly one identity-root node in one scene. Does not
 * invent/apply hierarchy transforms, texture, morphs,
 * animations, clinical laterality, source provenance or human skin approval.
 *
 * No network calls, no Three.js, no third-party GLB or GPU modules.
 */
import { parseRestrictedSkinnedGlb, FIRST_PARTY_GLB_GATE }
  from './firstPartyGlbSkinnedGeometry.mjs';
import { readRestrictedGlbUV0 } from './firstPartyGlbUV0.mjs';
import { readRestrictedGlbNormals } from './firstPartyGlbSourceNormals.mjs';
import { readRestrictedEmbeddedPngSources }
  from './firstPartyEmbeddedPngSource.mjs';
import {checkOriginalPilotIdentityMeshAncestry,
  exposeVerifiedPilotMeshAsValidationRoot}
  from './firstPartyGlbIdentityAncestorGate.mjs';

export const FIRST_PARTY_SCENE_BATCH_KIND='hgpt-glb2-batched-skinned-primitives-v1';
const MAX_GLB=32*1024*1024;
const MAX_PARTS=8;
const MAX_MESHES=4;
const MAX_TOTAL_VERTICES=250000;
// Separate, explicit small-GLB diagnostic budget for Work's 18-mesh pilot.
// Never enlarge the ordinary production/legacy-adapter acceptance boundary.
const PILOT_MAX_GLB=1024*1024;
const PILOT_MAX_MESHES=24;
const PILOT_MAX_PARTS=24;
const align4=n=>(n+3)&~3;
const expect=(yes,message)=>{if(!yes)throw new RangeError('GLB batch rejection: '+message);};
const array=v=>Array.isArray(v);
function unpack(input){
  expect(input instanceof ArrayBuffer && input.byteLength>=28 &&
    input.byteLength<=MAX_GLB,'bounded raw GLB ArrayBuffer required');
  const dv=new DataView(input);
  expect(dv.getUint32(0,true)===0x46546c67 &&
    dv.getUint32(4,true)===2 &&
    dv.getUint32(8,true)===input.byteLength,'GLB 2 header invalid');
  const jlen=dv.getUint32(12,true),jtype=dv.getUint32(16,true);
  expect(jlen%4===0 && jtype===0x4e4f534a && jlen>0 &&
    jlen<=input.byteLength-28,'JSON chunk invalid');
  const bhead=20+jlen;
  expect(bhead+8<=input.byteLength,'GLB BIN chunk header missing');
  const blen=dv.getUint32(bhead,true),btype=dv.getUint32(bhead+4,true);
  expect(blen%4===0 && btype===0x004e4942 &&
    bhead+8+blen===input.byteLength,'exactly one embedded BIN chunk required');
  let root;
  try{
    root=JSON.parse(new TextDecoder('utf-8',{fatal:true})
      .decode(new Uint8Array(input,20,jlen)).replace(/[\u0020\u0000]+$/g,''));
  }catch{
    throw new RangeError('GLB batch rejection: invalid GLB JSON/UTF8');
  }
  expect(root && typeof root==='object' && !array(root),'GLB JSON root object expected');
  return {root,bin:new Uint8Array(input,bhead+8,blen)};
}
function pack(root,bin){
  const text=new TextEncoder().encode(JSON.stringify(root));
  const jsonLen=align4(text.length),total=12+8+jsonLen+8+bin.byteLength;
  expect(total<=MAX_GLB && bin.byteLength%4===0,'split GLB exceeds bounded size/alignment');
  const output=new ArrayBuffer(total),dv=new DataView(output);
  dv.setUint32(0,0x46546c67,true);dv.setUint32(4,2,true);
  dv.setUint32(8,total,true);dv.setUint32(12,jsonLen,true);
  dv.setUint32(16,0x4e4f534a,true);
  new Uint8Array(output,20,jsonLen).fill(0x20);
  new Uint8Array(output,20,text.length).set(text);
  const bhead=20+jsonLen;
  dv.setUint32(bhead,bin.byteLength,true);dv.setUint32(bhead+4,0x004e4942,true);
  new Uint8Array(output,bhead+8,bin.byteLength).set(bin);
  return output;
}
const sameArray=(a,b)=>a.length===b.length && a.every((value,i)=>value===b[i]);

/**
 * Preview ONLY: one untextured OPAQUE glTF base colour. This does not implement
 * glTF metallic/roughness PBR, texture sampling, alpha blend or tone mapping.
 * Every source material, including unused entries, must have a permitted
 * shape; no unknown nested fields, links or extensions may be silently lost.
 */
const own=(value,key)=>Object.prototype.hasOwnProperty.call(value,key);
function flatOpaqueMaterial(source,primitive,used,pngTextures,usedTextureIndices,allowProvisionalPilot=false){
  if(primitive.material===undefined)
    return {color:Object.freeze([.74,.8,.92]),sourceMaterialIndex:null,sourcePng:null,
      sourceDoubleSided:false,sourceRoughness:1};
  const mats=source.materials;
  expect(array(mats)&&Number.isSafeInteger(primitive.material) &&
    primitive.material>=0&&primitive.material<mats.length,
    'invalid material index');
  const material=mats[primitive.material];
  expect(material && typeof material==='object' && !array(material),
    'material object invalid');
  const allowed=new Set(['name','pbrMetallicRoughness','alphaMode','doubleSided']);
  expect(Object.keys(material).every(key=>allowed.has(key)),'unsupported glTF material field');
  expect(!own(material,'alphaMode') || material.alphaMode==='OPAQUE',
    'only OPAQUE material supported');
  expect(material.doubleSided===undefined ||
    typeof material.doubleSided==='boolean',
    'doubleSided must be explicitly boolean when present');
  expect(allowProvisionalPilot || material.doubleSided!==true,
    'two-sided material shader parity not proven');
  expect(material.name===undefined ||
    (typeof material.name==='string'&&material.name.length<=80),
    'material name invalid');
  const pbr=material.pbrMetallicRoughness;
  expect(pbr && typeof pbr==='object' && !array(pbr),
    'explicit flat non-metallic material required');
  const allowedPbr=new Set(['baseColorFactor','metallicFactor','roughnessFactor',
    ...(pngTextures?['baseColorTexture']:[])]);
  expect(Object.keys(pbr).every(key=>allowedPbr.has(key)),
    'texture/unsupported PBR material feature rejected');
  // Strict default retains old matte-only contract. The separate original
  // Work pilot may carry a finite nonmetallic roughness (e.g. 0.4), which is
  // recorded, never silently treated as correct PBR lighting.
  expect(pbr.metallicFactor===0 &&
    (pbr.roughnessFactor===undefined ||
      (allowProvisionalPilot ?
        Number.isFinite(pbr.roughnessFactor)&&
        pbr.roughnessFactor>=0&&pbr.roughnessFactor<=1 :
        pbr.roughnessFactor===1)),
    'source metallic/roughness outside supported preview contract');
  const factor=pbr.baseColorFactor;
  expect(array(factor)&&factor.length===4 &&
    factor.every(v=>Number.isFinite(v)&&v>=0&&v<=1) &&
    factor[3]===1,'opaque finite baseColorFactor RGBA required');
  let sourcePng=null;
  if(pbr.baseColorTexture!==undefined){
    const link=pbr.baseColorTexture;
    expect(pngTextures && link && typeof link==='object' && !array(link) &&
      Object.keys(link).every(k=>['index','texCoord'].includes(k)) &&
      Number.isSafeInteger(link.index)&&link.index>=0&&
      link.index<pngTextures.length &&
      (link.texCoord===undefined||link.texCoord===0),
      'unsupported baseColorTexture link/UV set');
    sourcePng=pngTextures[link.index];
    usedTextureIndices.add(link.index);
  }
  used.add(primitive.material);
  return {color:Object.freeze([...factor.slice(0,3)]),
    sourceMaterialIndex:primitive.material,sourcePng,
    sourceDoubleSided:material.doubleSided===true,
    sourceRoughness:pbr.roughnessFactor??1};
}


/**
 * Strict mesh-data adapter; source read only.
 *
 * Why synthetic GLB splitting rather than a new relaxed loader? Every part
 * reuses the exact existing tested GLB accessor, weight, matrix and bounds
 * verifier; an unsupported second primitive must fail rather than be skipped.
 * This approach is a bounded correctness SPIKE, not an efficient production
 * importer: it copies the BIN per primitive and should be replaced by a
 * proven shared-buffer decoding API before large full-body assets.
 */
export function parseRestrictedBatchedSkinnedGlb(input,{allowSourceFlatColors=false,allowSourceUV0=false,allowSourceNormals=false,allowEmbeddedPngBaseColor=false,allowProvisionalPilot=false}={}){
  expect(typeof allowProvisionalPilot==='boolean','pilot diagnostic opt-in must be boolean');
  if(allowProvisionalPilot)
    expect(input instanceof ArrayBuffer && input.byteLength<=PILOT_MAX_GLB,
      'pilot diagnostic must be a small original GLB (at most 1 MiB)');
  const {root,bin}=unpack(input);
  expect(!allowProvisionalPilot || !allowEmbeddedPngBaseColor,
    'pilot diagnostic does not yet accept embedded textures');
  expect(typeof allowSourceFlatColors==='boolean','flat material mode must be explicit boolean');
  expect(typeof allowSourceUV0==='boolean','UV0 opt-in must be explicit boolean');
  expect(typeof allowSourceNormals==='boolean','source normal opt-in must be explicit boolean');
  expect(typeof allowEmbeddedPngBaseColor==='boolean','PNG opt-in must be boolean');
  expect(!allowEmbeddedPngBaseColor || (allowSourceFlatColors && allowSourceUV0),
    'embedded PNG opt-in requires flat colour and UV0 source validation');
  const pngTextures=allowEmbeddedPngBaseColor ?
    readRestrictedEmbeddedPngSources(root,bin) : null;
  if(root.materials!==undefined){
    expect(array(root.materials) && root.materials.length<=(allowProvisionalPilot?PILOT_MAX_PARTS:8),
      'material count over original preview limits');
    expect(allowSourceFlatColors || root.materials.length===0,
      'materials refused unless strict opaque baseColor opt-in is enabled');
  }
  expect(array(root.scenes) && root.scenes.length===1 && root.scene===0 &&
    array(root.scenes[0].nodes),'single explicit glTF scene required');
  expect(array(root.meshes) && root.meshes.length>=1 &&
    root.meshes.length<=(allowProvisionalPilot?PILOT_MAX_MESHES:MAX_MESHES),
    'must declare bounded original skinned meshes (1..4 normal; 1..24 diagnostic)');
  expect(array(root.nodes) && root.nodes.length>0 &&
    root.nodes.length<=200,
    'bounded node list required');
  expect(array(root.skins) && root.skins.length===1,
    'one explicit shared skin required');
  const roots=root.scenes[0].nodes;
  expect(roots.every(n=>Number.isSafeInteger(n)&&n>=0&&n<root.nodes.length) &&
    new Set(roots).size===roots.length,'scene root nodes invalid or duplicated');
  const nodeMap=new Map();
  for(let ni=0;ni<root.nodes.length;ni++){
    const node=root.nodes[ni];
    expect(node && typeof node==='object' && !array(node),'invalid GLB node');
    if(node.mesh!==undefined){
      expect(Number.isSafeInteger(node.mesh)&&node.mesh>=0&&
        node.mesh<root.meshes.length,'unknown mesh index in node');
      expect(node.skin===0,'all mesh nodes must use the same explicit skin');
      expect(!nodeMap.has(node.mesh),'instanced/duplicated mesh node unsupported');
      expect(allowProvisionalPilot || roots.includes(ni),
        'mesh node must be a direct root of explicit scene');
      nodeMap.set(node.mesh,ni);
    } else {
      expect(node.skin===undefined,'skin assigned to non-mesh node');
    }
  }
  expect(nodeMap.size===root.meshes.length,'every mesh needs exactly one root node');
  for(const parent of root.nodes){
    if(parent.children!==undefined){
      expect(array(parent.children) &&
        parent.children.every(child=>Number.isSafeInteger(child) &&
          child>=0 && child<root.nodes.length),'invalid node child pointer');
      expect(allowProvisionalPilot ||
        parent.children.every(child=>!nodeMap.has(root.nodes[child].mesh)),
        'mesh node must not have a hierarchy parent');
    }
  }
  // Work's GLB glTF 2 exporter groups ordinary SKINNED mesh nodes beneath
  // a scene wrapper. Only an identity ancestor hierarchy is supported here;
  // original Work joint hierarchy and mesh bytes remain unchanged.
  const pilotAncestry=allowProvisionalPilot ?
    checkOriginalPilotIdentityMeshAncestry(root,roots,nodeMap) : null;
  let count=0;
  for(const mesh of root.meshes){
    expect(mesh && array(mesh.primitives)&&mesh.primitives.length>=1 &&
      mesh.primitives.length<=(allowProvisionalPilot?PILOT_MAX_PARTS:MAX_PARTS),
      'each mesh needs bounded primitives');
    count+=mesh.primitives.length;
  }
  expect(count>=2 && count<=(allowProvisionalPilot?PILOT_MAX_PARTS:MAX_PARTS),
    'prototype requires 2..8 regular or 2..24 diagnostic primitives');

  const batches=[];
  const materialUsed=new Set(),usedPngTextureIndices=new Set();
  let totalVertices=0,totalTriangles=0,sourceNames=null,sourceInv=null;
  for(let meshIndex=0;meshIndex<root.meshes.length;meshIndex++){
    const mesh=root.meshes[meshIndex];
    for(let primitiveIndex=0;primitiveIndex<mesh.primitives.length;primitiveIndex++){
      const originalPrimitive=mesh.primitives[primitiveIndex];
      const attributes=originalPrimitive.attributes;
      const material=allowSourceFlatColors ?
        flatOpaqueMaterial(root,originalPrimitive,materialUsed,pngTextures,
          usedPngTextureIndices,allowProvisionalPilot) :
        {color:Object.freeze([.74,.8,.92]),sourceMaterialIndex:null,
          sourcePng:null,sourceDoubleSided:false,sourceRoughness:1};
      // Untextured original Work surfaces legitimately may lack TEXCOORD_0.
      // Do not fabricate source UV. A textured source always requires UV0.
      const missingPilotUV=allowProvisionalPilot && allowSourceUV0 &&
        attributes?.TEXCOORD_0===undefined && material.sourcePng===null;
      const uv0=allowSourceUV0 && !missingPilotUV ?
        readRestrictedGlbUV0(root,bin,attributes?.TEXCOORD_0,
          root.accessors?.[attributes?.POSITION]?.count) : null;
      const normal=allowSourceNormals ?
        readRestrictedGlbNormals(root,bin,attributes?.NORMAL,
          root.accessors?.[attributes?.POSITION]?.count) : null;
      if(material.sourcePng)
        expect(allowSourceUV0 && uv0 && uv0.length>0,
          'baseColorTexture requires validated source UV0');
      const split=structuredClone(root);
      split.meshes=[{
        ...(mesh.name!==undefined?{name:mesh.name}:{}),
        primitives:[structuredClone(mesh.primitives[primitiveIndex])],
      }];
      // Source material is separately strictly checked ABOVE, then removed
      // from this temporary single-primitive GLB because the immutable legacy
      // accessor parser deliberately refuses any material source reference.
      // Unsupported images, textures, extensions and anatomy stay unaltered
      // and are still forbidden by that original strict parser.
      if(allowSourceFlatColors){
        delete split.meshes[0].primitives[0].material;
        delete split.materials;
      }
      if(allowEmbeddedPngBaseColor){
        // Only remove after readRestrictedEmbeddedPngSources strictly checked
        // all PNG bytes, declared images, source textures and samplers.
        delete split.images;
        delete split.textures;
        delete split.samplers;
      }
      if(allowSourceUV0)delete split.meshes[0].primitives[0].attributes.TEXCOORD_0;
      // The inherited strict parser only COUNT-checks source NORMAL before
      // discarding it. When opt-in, this independent reader enforces finite
      // near-unit vectors and exact binary bounds before any primitive emits.
      // Strict geometry, indices and skin are STILL checked by inherited parser.
      const originalNodeIndex=nodeMap.get(meshIndex);
      for(let i=0;i<split.nodes.length;i++){
        const n=split.nodes[i];
        if(n.mesh!==undefined){
          if(i===originalNodeIndex)n.mesh=0;
          else {delete n.mesh;delete n.skin;}
        }
      }
      if(pilotAncestry)
        exposeVerifiedPilotMeshAsValidationRoot(split,originalNodeIndex,pilotAncestry);
      const parsed=parseRestrictedSkinnedGlb(pack(split,bin));
      expect(parsed.kind===FIRST_PARTY_GLB_GATE,'strict primitive validation failed');
      if(allowSourceUV0 && uv0!==null)
        expect(uv0.length===parsed.audit.vertices*2,
          'source UV0 vertex count disagrees with validated positions');
      if(allowSourceUV0 && uv0===null)
        expect(missingPilotUV,'source UV0 missing outside explicit diagnostic pilot');
      if(allowSourceNormals)
        expect(normal.length===parsed.audit.vertices*3,
          'validated source normal/position vertex counts disagree');
      if(sourceNames===null){
        sourceNames=[...parsed.jointNodeNames];
        sourceInv=parsed.mesh.inverseBindMatrices;
      } else {
        expect(sameArray(sourceNames,parsed.jointNodeNames) &&
          sameArray(sourceInv,parsed.mesh.inverseBindMatrices),
          'skin palette order or inverse rest binds differ between meshes');
      }
      totalVertices+=parsed.audit.vertices;
      totalTriangles+=parsed.audit.indexedTriangles;
      expect(totalVertices<=MAX_TOTAL_VERTICES,'aggregate vertex budget exceeded');
      batches.push({
        meshIndex,primitiveIndex,sourceMeshNodeIndex:originalNodeIndex,
        sourceMeshName:typeof mesh.name==='string'?mesh.name:null,
        materialColor:material.color,
        sourceMaterialIndex:material.sourceMaterialIndex,
        sourceBaseColorPng:material.sourcePng,
        sourceDoubleSided:material.sourceDoubleSided,
        sourceRoughness:material.sourceRoughness,
        sourcePBRLightingActuallyImplemented:false,
        sourceUV0:uv0,
        sourceNormals:normal,
        // Only parser-validated numeric arrays. Never claim accepted human rig.
        parsed,
      });
    }
  }
  expect(batches.length===count,'a source primitive was omitted');
  if(allowSourceFlatColors && root.materials){
    expect(materialUsed.size===root.materials.length,
      'unused or unvalidated source material rejected');
  }
  if(pngTextures)
    expect(usedPngTextureIndices.size===pngTextures.length,
      'unused embedded source PNG texture forbidden');
  return {
    kind:FIRST_PARTY_SCENE_BATCH_KIND,
    batches,
    jointNodeNames:Object.freeze([...sourceNames]),
    sourceSkinJointIndices:Object.freeze([...batches[0].parsed.jointNodeIndices]),
    audit:Object.freeze({
      sourceGeometryDecoded:true,
      numberOfMeshes:root.meshes.length,
      numberOfPrimitives:count,
      decodedVertices:totalVertices,
      indexedTriangles:totalTriangles,
      allPrimitivesPassExistingStrictLoader:true,
      flatOpaqueSourceColorsValidated:allowSourceFlatColors,
      sourceUV0CoordinatesValidated:allowSourceUV0,
      embeddedPngBaseColorSourceValidated:allowEmbeddedPngBaseColor,
      originalUnitLengthSourceNormalsValidated:allowSourceNormals,
      sourceNormalsGPUSkinned:false,
      textureSamplingImplemented:false,
      metallicRoughnessPBRImplemented:false,
      sharedSkinOrderNumericallyIdentical:true,
      meshRootTransformApplied:false,
      hierarchyJointWorldMatricesPhysicallyRegistered:false,
      actualOriginalHumanMeshUsed:false,
      clinicalAnatomyApproved:false,
      rightsAndProvenanceApproved:false,
      productionRuntimeReady:false,
      provisionalLargeSceneDiagnosticOnly:allowProvisionalPilot,
      verifiedIdentityGroupSourceMeshAncestry:
        allowProvisionalPilot&&pilotAncestry?.anyIdentityGroupPromotion===true,
      pilotSourceTwoSidedAndRoughnessMetadataPreserved:allowProvisionalPilot,
      originalUV0NeverFabricated:true,
      sourceBoneHierarchyChanged:false,
      noExternalModelCodeUsed:true,
    }),
  };
}
