/**
 * G4h — source-faithful glTF scene ancestor check for Work's pilot-only
 * nested mesh nodes. Reads, does NOT rewrite/recenter/move source joints.
 *
 * No arbitrary hierarchy flattening: the only supported transformation is
 * detachment of a skinned mesh node from a chain of **identity** grouping
 * nodes in an ephemeral per-primitive validation copy. Bone hierarchies remain
 * exactly as source. Nonidentity ancestors, DAGs, cycles and duplicated
 * source scene parents must fail closed until independently proven.
 */
export const HGPT_ORIGINAL_IDENTITY_ANCESTOR_GATE=
  'hgpt-original-identity-scene-wrapper-pilot-v1';

const fail=reason=>{throw new RangeError('Original identity ancestor rejected: '+reason)};
const need=(yes,reason)=>{if(!yes)fail(reason)};
const rec=o=>o!==null&&typeof o==='object'&&!Array.isArray(o);
const eq=(arr,expectation)=>Array.isArray(arr)&&arr.length===expectation.length&&
  arr.every((v,i)=>Number.isFinite(v)&&Math.abs(v-expectation[i])<=1e-6);
function isIdentityGroup(node){
  if(!rec(node)||node.mesh!==undefined||node.skin!==undefined)return false;
  if(Object.keys(node).some(k=>!['name','children','matrix','translation',
    'rotation','scale'].includes(k)))return false;
  if(node.matrix!==undefined && (
    node.translation!==undefined||node.rotation!==undefined||
    node.scale!==undefined))return false;
  if(node.matrix!==undefined && !eq(node.matrix,
    [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]))return false;
  if(node.translation!==undefined&&!eq(node.translation,[0,0,0]))return false;
  if(node.rotation!==undefined&&!eq(node.rotation,[0,0,0,1]))return false;
  if(node.scale!==undefined&&!eq(node.scale,[1,1,1]))return false;
  return node.name===undefined||
    (typeof node.name==='string'&&node.name.length<=80);
}

/**
 * @param {object} gltf GlTF source JSON; unchanged.
 * @param {number[]} sceneRoots Exact original active scene root node indices.
 * @param {Map<number,number>} meshToNode Unique skinned source mesh->node.
 * @returns {object} Verified grouped mesh node list and parent map.
 */
export function checkOriginalPilotIdentityMeshAncestry(
  gltf,sceneRoots,meshToNode
){
  need(rec(gltf)&&Array.isArray(gltf.nodes)&&gltf.nodes.length<=200 &&
    Array.isArray(sceneRoots)&&meshToNode instanceof Map,
    'bounded source node graph and mapped mesh nodes required');
  const nodes=gltf.nodes,parent=new Int32Array(nodes.length).fill(-1);
  const scenes=new Set(sceneRoots),meshNodes=new Set(meshToNode.values());
  need(sceneRoots.length>0&&sceneRoots.length===scenes.size &&
    sceneRoots.every(i=>Number.isSafeInteger(i)&&i>=0&&i<nodes.length),
    'unique source scene roots required');
  for(let ni=0;ni<nodes.length;ni++){
    const node=nodes[ni];
    need(rec(node),'every source node must be an object');
    if(node.children===undefined)continue;
    need(Array.isArray(node.children)&&node.children.length>=1 &&
      node.children.length<=200,'bounded nonempty child node list required');
    const used=new Set();
    for(const child of node.children){
      need(Number.isSafeInteger(child)&&child>=0&&child<nodes.length &&
        child!==ni&&!used.has(child),'invalid, self-parenting or duplicate child');
      used.add(child);
      need(parent[child]===-1,'source graph cannot have a joint/mesh with multiple parents');
      parent[child]=ni;
    }
  }
  for(const root of sceneRoots)
    need(parent[root]===-1,'scene root must not be a nested child');
  const results=[];
  for(const [meshIndex,nodeIndex]of meshToNode){
    need(Number.isSafeInteger(nodeIndex)&&nodeIndex>=0&&nodeIndex<nodes.length &&
      meshNodes.has(nodeIndex),'unique mapped source mesh node required');
    const seen=new Set(),ancestors=[];
    let n=nodeIndex;
    while(parent[n]!==-1){
      need(!seen.has(n),'cyclic mesh ancestor chain not permitted');
      seen.add(n);
      const p=parent[n];
      need(!meshNodes.has(p),'skinned mesh cannot have a mesh ancestor');
      need(isIdentityGroup(nodes[p]),
        'nonidentity or unsupported source ancestor for '+(nodes[nodeIndex].name||meshIndex));
      ancestors.push(p);n=p;
    }
    need(scenes.has(n),'source skinned mesh must be reachable from active scene roots');
    // Even if direct root, keep ordinary G4f access parity.
    results.push({meshIndex,nodeIndex,ancestorIndices:ancestors,
      identityAncestorPromotionRequired:ancestors.length>0});
  }
  need(results.length===meshToNode.size,
    'every mapped source mesh must have independently validated ancestry');
  return Object.freeze({
    kind:HGPT_ORIGINAL_IDENTITY_ANCESTOR_GATE,
    sourceMeshAncestors:Object.freeze(results.map(r=>Object.freeze(r))),
    descendantParentIndices:parent,
    sourceNodeCount:nodes.length,
    anyIdentityGroupPromotion:results.some(r=>r.ancestorIndices.length>0),
    sourceBoneHierarchyChanged:false,
    nonidentitySceneTransformApplied:false,
    clinicalAnatomyApproved:false,
  });
}

/** Validation-copy only; never call on original source object. */
export function exposeVerifiedPilotMeshAsValidationRoot(
  split,originalMeshNodeIndex,verifiedGraph
){
  need(rec(split)&&Array.isArray(split.nodes)&&
    verifiedGraph?.kind===HGPT_ORIGINAL_IDENTITY_ANCESTOR_GATE,
    'only a strictly validated source pilot can detach identity wrappers');
  const entry=verifiedGraph.sourceMeshAncestors.find(
    x=>x.nodeIndex===originalMeshNodeIndex);
  need(Boolean(entry),'mesh node was not checked against original source ancestors');
  if(!entry.identityAncestorPromotionRequired)return false;
  for(const node of split.nodes){
    if(!Array.isArray(node.children))continue;
    if(node.children.includes(originalMeshNodeIndex)){
      node.children=node.children.filter(i=>i!==originalMeshNodeIndex);
      if(node.children.length===0)delete node.children;
    }
  }
  need(Array.isArray(split.scenes)&&Array.isArray(split.scenes[split.scene]?.nodes),
    'validation-copy scene invalid');
  need(!split.scenes[split.scene].nodes.includes(originalMeshNodeIndex),
    'original nested mesh node unexpectedly already root');
  split.scenes[split.scene].nodes.push(originalMeshNodeIndex);
  return true;
}
