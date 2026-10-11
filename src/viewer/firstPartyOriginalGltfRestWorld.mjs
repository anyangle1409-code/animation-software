/**
 * G4j — derive exact glTF source WORLD REST transforms from the original
 * Blender-exported rig hierarchy, never from anatomical/side heuristics.
 *
 * Inputs: authentic same-byte GLB and a previously strict G4i-validated scene.
 * Output is DIAGNOSTIC only: Y-up/column-major GLB joint rest palettes and
 * original inverse-bind numerical residual. Native Blender Z-up/row-major
 * authored motion is explicitly NOT transformed/registered by this function.
 */
import {multiplyNativeMat4} from './firstPartyWebGL2SkeletonPreview.mjs';
import {FIRST_PARTY_SCENE_BATCH_KIND}
  from './firstPartyGlbSkinnedBatches.mjs';
export const HGPT_GLTF_REST_WORLD_KIND='hgpt-original-gltf-yup-world-rest-diagnostic-v1';
const fail=s=>{throw new RangeError('Original glTF world rest rejected: '+s)};
const need=(ok,s)=>{if(!ok)fail(s)};
const finite=n=>typeof n==='number'&&Number.isFinite(n);
const ARR=Array.isArray;
const MATRIX_TOL=1e-4;
const I=new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
const v3=(x,d)=>x===undefined?[...d]:
  ARR(x)&&x.length===3&&x.every(finite)?x:fail('invalid source vec3 TRS');
const q4=(x)=>x===undefined?[0,0,0,1]:
  ARR(x)&&x.length===4&&x.every(finite)?x:fail('invalid source quaternion TRS');
const sq=x=>x*x;
function unpack(bytes){
  need(bytes instanceof ArrayBuffer && bytes.byteLength>=28 &&
    bytes.byteLength<=1024*1024,'bounded actual original shoulder pilot GLB required');
  const v=new DataView(bytes);
  need(v.getUint32(0,true)===0x46546c67 &&
    v.getUint32(4,true)===2 &&
    v.getUint32(8,true)===bytes.byteLength,'complete GLB 2 header required');
  const len=v.getUint32(12,true);
  need(len>0&&len%4===0&&v.getUint32(16,true)===0x4e4f534a &&
    len+28<=bytes.byteLength,'GLB JSON chunk must be exact and bounded');
  let src;
  try{src=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(
      new Uint8Array(bytes,20,len)).replace(/[ \0]+$/g,''));}
  catch{fail('source GLB JSON invalid')}
  need(src && ARR(src.nodes) && src.nodes.length<=200 &&
    ARR(src.skins)&&src.skins.length===1 &&
    ARR(src.scenes)&&src.scenes.length===1&&
    src.scene===0&&ARR(src.scenes[0].nodes),'one bounded original source rig/scene required');
  return src;
}
function validateRigid(m,name){
  need((m instanceof Float32Array||ARR(m))&&m.length===16 &&
    Array.from(m).every(finite),'source world/local mat4 nonfinite '+name);
  for(const j of [3,7,11])need(Math.abs(m[j])<MATRIX_TOL,
    'source matrix nonaffine '+name);
  need(Math.abs(m[15]-1)<MATRIX_TOL,'source matrix homogeneous scale unsupported '+name);
  const ax=[m[0],m[1],m[2]],ay=[m[4],m[5],m[6]],az=[m[8],m[9],m[10]];
  const len=u=>Math.hypot(...u),dot=(u,v)=>u.reduce((n,a,i)=>n+a*v[i],0);
  need(Math.abs(len(ax)-1)<MATRIX_TOL &&
    Math.abs(len(ay)-1)<MATRIX_TOL &&
    Math.abs(len(az)-1)<MATRIX_TOL &&
    Math.abs(dot(ax,ay))<MATRIX_TOL &&
    Math.abs(dot(ax,az))<MATRIX_TOL &&
    Math.abs(dot(ay,az))<MATRIX_TOL,
    'nonrigid scale/shear in source joint '+name);
  const cross=[
    ax[1]*ay[2]-ax[2]*ay[1],
    ax[2]*ay[0]-ax[0]*ay[2],
    ax[0]*ay[1]-ax[1]*ay[0]
  ];
  need(Math.abs(dot(cross,az)-1)<MATRIX_TOL,
    'reflected/inverted source joint basis '+name);
  return m;
}
function local(node,name){
  need(node&&typeof node==='object'&&!ARR(node),'source node object required '+name);
  if(node.matrix!==undefined){
    need(node.translation===undefined&&node.rotation===undefined&&
      node.scale===undefined,'source glTF matrix cannot coexist with TRS');
    need(ARR(node.matrix)&&node.matrix.length===16,
      'source 4×4 matrix required');
    return validateRigid(new Float32Array(node.matrix),name);
  }
  const [tx,ty,tz]=v3(node.translation,[0,0,0]);
  const [sx,sy,sz]=v3(node.scale,[1,1,1]);
  const [x,y,z,w]=q4(node.rotation);
  const norm=x*x+y*y+z*z+w*w;
  need(Math.abs(norm-1)<=1e-3,'source quaternion not unit length '+name);
  const f=1/Math.sqrt(norm),X=x*f,Y=y*f,Z=z*f,W=w*f;
  const m=new Float32Array([
    (1-2*(sq(Y)+sq(Z)))*sx,(2*(X*Y+Z*W))*sx,
      (2*(X*Z-Y*W))*sx,0,
    (2*(X*Y-Z*W))*sy,(1-2*(sq(X)+sq(Z)))*sy,
      (2*(Y*Z+X*W))*sy,0,
    (2*(X*Z+Y*W))*sz,(2*(Y*Z-X*W))*sz,
      (1-2*(sq(X)+sq(Y)))*sz,0,
    tx,ty,tz,1
  ]);
  return validateRigid(m,name);
}
function matrixResidual(a,b){
  const product=multiplyNativeMat4(a,b);
  return product.reduce((v,n,i)=>Math.max(v,Math.abs(n-I[i])),0);
}
export function deriveOriginalSourceGLTFRestWorld(glb,sourceScene){
  need(sourceScene?.kind===FIRST_PARTY_SCENE_BATCH_KIND &&
    sourceScene.audit?.sourceGeometryDecoded===true &&
    sourceScene.audit?.provisionalLargeSceneDiagnosticOnly===true &&
    ARR(sourceScene.batches)&&sourceScene.batches.length>=2 &&
    sourceScene.batches.length<=24 &&
    sourceScene.batches[0]?.parsed?.mesh?.inverseBindMatrices instanceof Float32Array,
    'strict verified first-party G4i pilot scene required');
  const root=unpack(glb),nodes=root.nodes,skin=root.skins[0],
    indices=skin.joints;
  need(ARR(indices)&&indices.length>=1&&indices.length<=128 &&
    indices.every(i=>Number.isSafeInteger(i)&&i>=0&&i<nodes.length) &&
    new Set(indices).size===indices.length,
    'unique original source skin joints required');
  const jointNames=indices.map(i=>nodes[i].name);
  need(jointNames.every(s=>typeof s==='string'&&s.length>0&&s.length<=80) &&
    new Set(jointNames).size===jointNames.length &&
    jointNames.every((name,i)=>name===sourceScene.jointNodeNames[i]),
    'original glTF joint order must match independently decoded scene');
  const parent=Array(nodes.length).fill(-1);
  for(let i=0;i<nodes.length;i++){
    const children=nodes[i].children;
    if(children===undefined)continue;
    need(ARR(children),'source children must be array');
    for(const child of children){
      need(Number.isSafeInteger(child)&&child>=0&&child<nodes.length &&
        child!==i && parent[child]===-1,
        'invalid source node parent graph/duplicate');
      parent[child]=i;
    }
  }
  const roots=root.scenes[0].nodes;
  need(roots.length>0&&roots.every(r=>parent[r]===-1),
    'scene root cannot be a child');
  const memo=new Map(),active=new Set();
  function world(i){
    if(memo.has(i))return memo.get(i);
    need(!active.has(i),'source graph cycle');
    active.add(i);
    const here=local(nodes[i],nodes[i]?.name||String(i));
    const result=parent[i]===-1?here:
      multiplyNativeMat4(world(parent[i]),here);
    active.delete(i);
    validateRigid(result,nodes[i]?.name||String(i));
    memo.set(i,result);return result;
  }
  const matrices=indices.map(i=>new Float32Array(world(i)));
  const inv=sourceScene.batches[0].parsed.mesh.inverseBindMatrices;
  need(inv.length===indices.length*16,'exact inverse bind palette size required');
  const residuals=indices.map((i,j)=>matrixResidual(
    matrices[j],inv.subarray(j*16,j*16+16)));
  const worst=Math.max(...residuals);
  need(worst<=MATRIX_TOL,
    'original glTF joint world rest does not numerically invert source inverse bind');
  const restWorldBySourceBone=Object.freeze(Object.fromEntries(
    jointNames.map((name,i)=>[name,Object.freeze([...matrices[i]])])));
  return Object.freeze({
    kind:HGPT_GLTF_REST_WORLD_KIND,
    frame:'glTF_Y_UP_RIGHT_HANDED_METRES_COLUMN_MAJOR',
    orderedSourceJointNames:Object.freeze([...jointNames]),
    sourceWorldRestByName:restWorldBySourceBone,
    maximumWorldInverseBindResidual:worst,
    sourceJointCount:jointNames.length,
    sourceGLBSourceJointHierarchyPreserved:true,
    nativeWorkZUpRowMajorPoseFramesIndependentlyRegistered:false,
    arbitraryHumanExerciseMotionApproved:false,
    productionReady:false,
  });
}
