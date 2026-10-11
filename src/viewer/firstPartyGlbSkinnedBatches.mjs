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
 * invent/apply hierarchy transforms, material, colour, UV, textures, morphs,
 * animations, clinical laterality, source provenance or human skin approval.
 *
 * No network calls, no Three.js, no third-party GLB or GPU modules.
 */
import { parseRestrictedSkinnedGlb, FIRST_PARTY_GLB_GATE }
  from './firstPartyGlbSkinnedGeometry.mjs';

export const FIRST_PARTY_SCENE_BATCH_KIND='hgpt-glb2-batched-skinned-primitives-v1';
const MAX_GLB=32*1024*1024;
const MAX_PARTS=8;
const MAX_MESHES=4;
const MAX_TOTAL_VERTICES=250000;
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
 * Strict mesh-data adapter; source read only.
 *
 * Why synthetic GLB splitting rather than a new relaxed loader? Every part
 * reuses the exact existing tested GLB accessor, weight, matrix and bounds
 * verifier; an unsupported second primitive must fail rather than be skipped.
 * This approach is a bounded correctness SPIKE, not an efficient production
 * importer: it copies the BIN per primitive and should be replaced by a
 * proven shared-buffer decoding API before large full-body assets.
 */
export function parseRestrictedBatchedSkinnedGlb(input){
  const {root,bin}=unpack(input);
  expect(array(root.scenes) && root.scenes.length===1 && root.scene===0 &&
    array(root.scenes[0].nodes),'single explicit glTF scene required');
  expect(array(root.meshes) && root.meshes.length>=1 &&
    root.meshes.length<=MAX_MESHES,'must declare 1..4 original skinned meshes');
  expect(array(root.nodes) && root.nodes.length>0 && root.nodes.length<=200,
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
      expect(roots.includes(ni),'mesh node must be a direct root of explicit scene');
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
      expect(parent.children.every(child=>!nodeMap.has(root.nodes[child].mesh)),
        'mesh node must not have a hierarchy parent');
    }
  }
  let count=0;
  for(const mesh of root.meshes){
    expect(mesh && array(mesh.primitives)&&mesh.primitives.length>=1 &&
      mesh.primitives.length<=MAX_PARTS,'each mesh needs bounded primitives');
    count+=mesh.primitives.length;
  }
  expect(count>=2 && count<=MAX_PARTS,'prototype requires 2..8 explicit total primitives');

  const batches=[];
  let totalVertices=0,totalTriangles=0,sourceNames=null,sourceInv=null;
  for(let meshIndex=0;meshIndex<root.meshes.length;meshIndex++){
    const mesh=root.meshes[meshIndex];
    for(let primitiveIndex=0;primitiveIndex<mesh.primitives.length;primitiveIndex++){
      const split=structuredClone(root);
      split.meshes=[{
        ...(mesh.name!==undefined?{name:mesh.name}:{}),
        primitives:[structuredClone(mesh.primitives[primitiveIndex])],
      }];
      const originalNodeIndex=nodeMap.get(meshIndex);
      for(let i=0;i<split.nodes.length;i++){
        const n=split.nodes[i];
        if(n.mesh!==undefined){
          if(i===originalNodeIndex)n.mesh=0;
          else {delete n.mesh;delete n.skin;}
        }
      }
      const parsed=parseRestrictedSkinnedGlb(pack(split,bin));
      expect(parsed.kind===FIRST_PARTY_GLB_GATE,'strict primitive validation failed');
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
        // Only parser-validated numeric arrays. Never claim accepted human rig.
        parsed,
      });
    }
  }
  expect(batches.length===count,'a source primitive was omitted');
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
      sharedSkinOrderNumericallyIdentical:true,
      meshRootTransformApplied:false,
      hierarchyJointWorldMatricesPhysicallyRegistered:false,
      actualOriginalHumanMeshUsed:false,
      clinicalAnatomyApproved:false,
      rightsAndProvenanceApproved:false,
      productionRuntimeReady:false,
      noExternalModelCodeUsed:true,
    }),
  };
}
