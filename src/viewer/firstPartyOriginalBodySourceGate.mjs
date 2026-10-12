/** G4q: exact Work PR81 original human GLB fingerprint and review-only feature gate.
 * This is a preflight, NOT a model renderer, exercise solver or rights approval.
 * Runs before separate independently verified strict original accessor decode.
 * Legacy two-plus-primitive importer and production PT-App remain untouched.
 */
export const ORIGINAL_BODY_GLBSHA256=
  'd267dac344affb5d52c7155f8d0254794e818a8eab3ad54f7f263694f36c390d';
export async function verifyOriginalBodySourcePreflight(bytes,{reviewOnly=false}={}){
  const reject=s=>{throw new RangeError('G4q source preflight: '+s)};
  if(!reviewOnly)reject('explicit review-only opt-in required');
  if(!(bytes instanceof ArrayBuffer)||bytes.byteLength!==1495720)
    reject('complete Work PR81 original GLB bytes required');
  if(!globalThis.crypto?.subtle)reject('WebCrypto digest required');
  const hash=await crypto.subtle.digest('SHA-256',bytes);
  const actual=Array.from(new Uint8Array(hash),x=>x.toString(16).padStart(2,'0')).join('');
  if(actual!==ORIGINAL_BODY_GLBSHA256)reject('original source SHA-256 mismatch');
  const dv=new DataView(bytes),jl=dv.getUint32(12,true),bo=20+jl;
  if(dv.getUint32(0,true)!==0x46546c67||dv.getUint32(4,true)!==2||
     dv.getUint32(8,true)!==bytes.byteLength||dv.getUint32(16,true)!==0x4e4f534a||
     jl%4!==0||bo+8>bytes.byteLength||dv.getUint32(bo+4,true)!==0x004e4942||
     bo+8+dv.getUint32(bo,true)!==bytes.byteLength)
    reject('bounded glTF2 JSON+BIN structure required');
  const g=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(new Uint8Array(bytes,20,jl)).trim());
  const m=g.meshes?.[0],p=m?.primitives?.[0],skin=g.skins?.[0],nodes=g.nodes;
  if(g.scene!==0||g.scenes?.length!==1||g.scenes[0].nodes?.length!==1||
     g.scenes[0].nodes[0]!==68||g.meshes?.length!==1||m.primitives?.length!==1||
     skin?.joints?.length!==67||new Set(skin.joints).size!==67||
     g.skins?.length!==1||!Array.isArray(nodes)||nodes.length!==69||
     nodes[67]?.skin!==0||nodes[67]?.mesh!==0||
     JSON.stringify(nodes[68].children)!=='[67,66]'||
     nodes[67].extras?.hgpt_export_production_approved!==false||
     m.weights?.length!==6||!m.weights.every(x=>x===0)||
     p.targets?.length!==6||!p.targets.every(x=>x.POSITION!==undefined&&x.NORMAL!==undefined)||
     g.animations?.length||g.extensionsRequired?.length)
    reject('actual original body 67-joint zero-morph review profile required');
  if(p.attributes?.POSITION===undefined||p.attributes?.JOINTS_0===undefined||
     p.attributes?.WEIGHTS_0===undefined||p.attributes?.NORMAL===undefined||
     g.accessors?.[p.attributes.POSITION]?.count!==17946||
     g.accessors?.[p.indices]?.count!==107664||
     g.materials?.[p.material]?.doubleSided!==true)
    reject('original indexed skin, normals and material features required');
  return Object.freeze({sourceSha256:actual,originalVertices:17946,
    originalTriangles:35888,originalRuntimeJoints:67,
    zeroWeightedSparseCorrectiveMorphTargets:6,
    preflightOnly:true,sourceHumanMotionValidated:false,
    sourceRightsIndependentlyApproved:false,productionApproved:false});
}
