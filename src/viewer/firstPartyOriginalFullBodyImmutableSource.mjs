/**
 * Exact-byte snapshots of already SHA-verified ORIGINAL-v1 decoded buffers.
 *
 * Object.freeze(review) alone cannot freeze Float32Array / Uint16Array bytes:
 * UI callers can modify typed arrays or morph delta objects after the original
 * GLB was validated. The TRUSTED caller keeps these snapshots in a private
 * WeakMap. Never expose a snapshot from that trusted WeakMap or accept one
 * supplied by a caller as authentication.
 *
 * This module does NOT mint authenticity or approve anatomical/rights data.
 */
const fail=why=>{throw new RangeError('Original source post-validation mutation: '+why)};
const get=(root,path)=>path.reduce((p,k)=>p?.[k],root);
const typed=v=>ArrayBuffer.isView(v)&&!(v instanceof DataView)&&
  !(v.buffer instanceof SharedArrayBuffer);
function snapshotBytes(root,path){
  const src=get(root,path);
  if(!typed(src) || !Number.isSafeInteger(src.length) ||
    src.length===0 || src.byteLength===0)fail('invalid source typed array '+path.join('.'));
  const copy=new Uint8Array(src.buffer,src.byteOffset,src.byteLength).slice();
  return {path,reference:src,ctor:src.constructor,bytes:copy};
}
function snapshotArray(root,path){
  const src=get(root,path);
  if(!Array.isArray(src)||!src.every(x=>Number.isFinite(x)))
    fail('invalid original source numeric array '+path.join('.'));
  return {path,reference:src,values:src.slice()};
}
function sourcePaths(review){
  if(!review||typeof review!=='object'||!review.mesh ||
    !Array.isArray(review.jointNames)||!Array.isArray(review.sparseCorrectives)||
    !review.restWorldByJointName)
    fail('review source manifest/rig missing');
  const buffers=[
    ['mesh','positions'],['mesh','indices'],
    ['mesh','jointIndices'],['mesh','weights'],
    ['mesh','inverseBindMatrices'],['sourceNormals'],
  ];
  const values=[
    ...review.jointNames.map(name=>['restWorldByJointName',name]),
    ['sourceMaterial','sourceBaseColor'],
  ];
  const scalars=[
    ['sourceSha256'],['vertices'],['triangles'],['bones'],
    ['sourceMaterial','sourceDoubleSided'],
    ['sourceMaterial','sourceRoughness'],
  ];
  for(let i=0;i<review.sparseCorrectives.length;i++){
    const p=['sparseCorrectives',i];
    buffers.push([...p,'sourcePositionDelta','indices'],
      [...p,'sourcePositionDelta','delta'],
      [...p,'sourceNormalDelta','indices'],
      [...p,'sourceNormalDelta','delta']);
    scalars.push([...p,'name'],[...p,'restWeight'],
      [...p,'positionChangedVertices'],[...p,'normalChangedVertices'],
      [...p,'sourcePositionDelta','changedVertices'],
      [...p,'sourceNormalDelta','changedVertices'],
      [...p,'sourcePositionDelta','maxAbsDelta'],
      [...p,'sourceNormalDelta','maxAbsDelta'],
      [...p,'actualCorrectiveSynthesisValidated']);
  }
  return {buffers,values,scalars};
}
/**
 * Snapshot checked *decoding results*, not raw source bytes. A source parser
 * must first independently SHA verify the source and assert source rights
 * remain NOT approved. Captured snapshots are not authentication tokens.
 */
export function snapshotDecodedOriginalReview(review){
  const {buffers,values,scalars}=sourcePaths(review);
  return {
    review,
    mesh:review.mesh,
    sourceNormal:review.sourceNormals,
    morphs:review.sparseCorrectives,
    restWorld:review.restWorldByJointName,
    material:review.sourceMaterial,
    paths:{buffers:buffers.map(path=>snapshotBytes(review,path)),
      values:values.map(path=>snapshotArray(review,path)),
      scalars:scalars.map(path=>({path,value:get(review,path)}))},
  };
}
export function assertDecodedOriginalReviewUnmodified(review,snapshot){
  if(!snapshot||snapshot.review!==review||
    snapshot.mesh!==review?.mesh||
    snapshot.morphs!==review.sparseCorrectives ||
    snapshot.restWorld!==review.restWorldByJointName||
    snapshot.material!==review.sourceMaterial ||
    snapshot.sourceNormal!==review.sourceNormals)
    fail('source object/reference replaced after authentication');
  for(const entry of snapshot.paths.buffers){
    const current=get(review,entry.path);
    if(current!==entry.reference||!typed(current)||
      current.constructor!==entry.ctor||
      current.byteLength!==entry.bytes.byteLength)
      fail('original source typed buffer substituted '+entry.path.join('.'));
    const now=new Uint8Array(current.buffer,current.byteOffset,current.byteLength);
    for(let i=0;i<now.length;i++)
      if(now[i]!==entry.bytes[i])
        fail('original source typed buffer bytes changed '+entry.path.join('.'));
  }
  for(const entry of snapshot.paths.values){
    const current=get(review,entry.path);
    if(current!==entry.reference||!Array.isArray(current)||
      current.length!==entry.values.length||
      current.some((v,i)=>!Object.is(v,entry.values[i])))
      fail('original source numeric array changed '+entry.path.join('.'));
  }
  for(const entry of snapshot.paths.scalars)
    if(!Object.is(get(review,entry.path),entry.value))
      fail('original source metadata changed '+entry.path.join('.'));
  return true;
}
