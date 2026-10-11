#!/usr/bin/env node
/**
 * G4g: diagnostic audit of ACTUAL project-authored Work shoulder pilot artifact.
 * It does not alter/repack source GLB, silently convert W1 native pose matrices,
 * or claim actual human/physiological/release acceptance.
 *
 * Usage:
 *   node scripts/audit-original-work-shoulder-pilot.mjs <extracted-artifact-dir>
 *
 * Artifact pinned to W1 PR #68, CI run 38153765790, artifact 11706909894.
 * Never commit/publish this original GLB. Only audit JSON is retained.
 */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync,readdirSync,mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import {parseRestrictedBatchedSkinnedGlb}
  from '../src/viewer/firstPartyGlbSkinnedBatches.mjs';

const ARTIFACT_SOURCE={
  workflowRun:38153765790,artifactId:11706909894,
  uploadHead:'79e0a1c53776b0a77eeb9e288c47cf6ed704b661',
  candidate:'PROVISIONAL_FUNCTIONAL_SHOULDER_v1',
  glb:'PROVISIONAL_FUNCTIONAL_SHOULDER_v1.glb',
  glbSha256:'fda9c5e653044988fd1e5c58fe352f074071c4be008eceba702bbbef96a4ea5f',
  sourceRecordSha256:'99500d94e06c66ca489bdaccc0345446f98794946254c5e592d9449696f396c1',
};
const digest=bytes=>createHash('sha256').update(bytes).digest('hex');
function readStructuredGLB(bytes){
  assert.ok(bytes.length>=28&&bytes.length<=1024*1024,
    'work pilot must remain a bounded <= 1 MiB complete original GLB');
  const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
  assert.equal(v.getUint32(0,true),0x46546c67,'exact glTF GLB magic');
  assert.equal(v.getUint32(4,true),2,'glTF 2 only');
  assert.equal(v.getUint32(8,true),bytes.length,'no extra GLB bytes');
  const jlen=v.getUint32(12,true),jtype=v.getUint32(16,true);
  assert.equal(jtype,0x4e4f534a,'one initial JSON chunk');
  assert.ok(jlen>0&&jlen%4===0&&20+jlen+8<=bytes.length);
  const root=JSON.parse(new TextDecoder('utf-8',{fatal:true})
    .decode(bytes.subarray(20,20+jlen)).trim());
  const binHead=20+jlen;
  assert.equal(v.getUint32(binHead+4,true),0x004e4942,'embedded BIN only');
  assert.equal(binHead+8+v.getUint32(binHead,true),bytes.length);
  return root;
}
function sourceSummaries(root){
  const parents=Array.from({length:root.nodes.length},()=>[]);
  for(let i=0;i<root.nodes.length;i++)
    for(const child of root.nodes[i].children||[]){
      assert.ok(Number.isSafeInteger(child)&&child>=0&&child<root.nodes.length,
        'bounded parent/child pointer');
      parents[child].push(i);
    }
  const allNodes=root.nodes.map((node,i)=>({
    index:i,name:node.name||null,mesh:node.mesh??null,skin:node.skin??null,
    parentNodeIndices:parents[i],children:node.children?.length??0,
    sourceTRS:node.matrix?'matrix':node.translation||node.rotation||node.scale?'trs':'identity',
  }));
  const meshNodes=allNodes.filter(x=>x.mesh!==null);
  const rootIndices=root.scenes[root.scene].nodes;
  const nestedMeshes=meshNodes.filter(x=>!rootIndices.includes(x.index));
  const materialInfos=(root.materials||[]).map((m,i)=>({
    index:i,name:m.name??null,doubleSided:m.doubleSided??false,
    metallic:m.pbrMetallicRoughness?.metallicFactor??1,
    roughness:m.pbrMetallicRoughness?.roughnessFactor??1,
    baseColorFactor:m.pbrMetallicRoughness?.baseColorFactor??[1,1,1,1],
  }));
  const indices=root.meshes.flatMap(m=>m.primitives.map(p=>p.indices));
  const meshPositionAccessors=root.meshes.flatMap(m=>
    m.primitives.map(p=>p.attributes?.POSITION));
  const vertexCount=meshPositionAccessors.reduce((a,i)=>
    a+(root.accessors[i]?.count||0),0);
  return {
    sceneRoots:rootIndices,meshCount:root.meshes.length,
    primitiveCount:root.meshes.reduce((a,m)=>a+m.primitives.length,0),
    skinCount:root.skins.length,
    skinJoints:root.skins[0].joints.map(i=>root.nodes[i].name),
    nodeCount:root.nodes.length,
    meshNodeCount:meshNodes.length,
    nestedMeshNodeCount:nestedMeshes.length,
    nestedMeshes:nestedMeshes.map(x=>({name:x.name,parentNodeIndices:x.parentNodeIndices})),
    skinRootIndices:root.scenes[root.scene].nodes,
    jointHierarchy:allNodes.filter(n=>root.skins[0].joints.includes(n.index)),
    materialCount:materialInfos.length,
    materialInfos,vertexCount,
    omittedUV0Count:root.meshes.flatMap(m=>m.primitives)
      .filter(p=>p.attributes.TEXCOORD_0===undefined).length,
    primitiveIndexAccessors:indices.length,
    externalURIRequired:JSON.stringify(root.buffers||[]).includes('"uri"') ||
      JSON.stringify(root.images||[]).includes('"uri"'),
  };
}
function exactManifest(dir){
  const files=readdirSync(dir).sort();
  assert.deepEqual(files.filter(x=>x.toLowerCase().endsWith('.glb')),
    [ARTIFACT_SOURCE.glb],'only the expected authored source GLB may be accepted');
  const m=JSON.parse(readFileSync(path.join(dir,'pilot_manifest.json'),'utf8'));
  assert.equal(m.candidate,ARTIFACT_SOURCE.candidate);
  assert.equal(m.source_record_sha256,ARTIFACT_SOURCE.sourceRecordSha256);
  assert.equal(m.status,'PROVISIONAL_SHOULDER_ONLY_NOT_ORIGINAL_HUMAN');
  assert.equal(m.anatomy_approved,false);
  assert.equal(m.motion_approved,false);
  assert.equal(m.production_approved,false);
  assert.ok(m.native_frame.includes('+Z superior'));
  assert.ok(m.glb_frame.includes('Y-up conversion'));
  assert.ok(Array.isArray(m.frames)&&m.frames.length>=2);
  // Work deliberately keeps the full native .blend scene PRIVATE: its
  // manifest hashes it but the CI artifact is GLB/PNG/JSON-only.
  // Requiring that scene would be an unintended private-asset disclosure.
  const publicAuthored=Object.keys(m.files_sha256)
    .filter(name=>!name.toLowerCase().endsWith('.blend'));
  assert.deepEqual(files,['pilot_manifest.json',...publicAuthored].sort(),
    'ZIP must contain exactly manifested public GLB/PNG evidence; private Blender stays excluded');
  for(const [name,sha]of Object.entries(m.files_sha256)){
    if(name.toLowerCase().endsWith('.blend'))continue;
    assert.equal(path.basename(name),name,'no nested/escaped manifest file');
    assert.match(sha,/^[a-f0-9]{64}$/);
    assert.equal(digest(readFileSync(path.join(dir,name))),sha,
      'source authored file digest mismatch: '+name);
  }
  return m;
}
const arg=process.argv[2];
if(!arg)throw new Error('Usage: node scripts/audit-original-work-shoulder-pilot.mjs <extracted-artifact-dir>');
const dir=path.resolve(arg),m=exactManifest(dir);
const source=readFileSync(path.join(dir,ARTIFACT_SOURCE.glb));
assert.equal(digest(source),ARTIFACT_SOURCE.glbSha256,
  'original Work pilot byte SHA changed; re-audit rather than using stale manifest');
const snapshot=Buffer.from(source);
const root=readStructuredGLB(source);
const summary=sourceSummaries(root);
assert.deepEqual([summary.meshCount,summary.primitiveCount,summary.skinCount,
  summary.skinJoints.length],[18,18,1,6],
  'this exact Work pilot profile changed; do not re-use cached audit');
assert.equal(summary.externalURIRequired,false);
const expectedNames=Object.keys(m.rig_mapping);
assert.deepEqual([...summary.skinJoints].sort(),expectedNames.sort(),
  'explicit human source controls must match rig identity exactly');
const allControls=Object.values(m.frames).every(frame=>
  frame.controls && expectedNames.every(n=>Object.hasOwn(frame.controls,n)));
assert.equal(allControls,true,'all Work-authored pose matrices must declare every exact source joint');
let importerStatus='ACCEPTED_AS_DIAGNOSTIC_ONLY',firstPartyImporterError=null;
try{
  parseRestrictedBatchedSkinnedGlb(
    source.buffer.slice(source.byteOffset,source.byteOffset+source.byteLength),
    {allowProvisionalPilot:true,allowSourceFlatColors:true,
      allowSourceUV0:true,allowSourceNormals:true});
}catch(e){
  importerStatus='BLOCKED_BY_STRICT_ORIGINAL_SOURCE_PROFILE';
  firstPartyImporterError={name:e.name,message:e.message};
}
assert.deepEqual(source,snapshot,'original Work GLB cannot be rewritten');
const issues=[];
if(summary.nestedMeshNodeCount)
  issues.push({code:'NESTED_MESH_NODES',
    count:summary.nestedMeshNodeCount,
    recommendation:'First-party source GLB traversal must explicitly preserve identity/world parent transforms; never flatten Work joint centres by changing source asset'});
if(summary.materialInfos.some(x=>x.doubleSided))
  issues.push({code:'DOUBLE_SIDED_SOURCE_MATERIAL',
    count:summary.materialInfos.filter(x=>x.doubleSided).length,
    recommendation:'First-party renderer must support original material culling choice, not demand Work re-export physically incorrect surfaces'});
if(summary.materialInfos.some(x=>x.metallic!==0||x.roughness!==1))
  issues.push({code:'SOURCE_PBR_PROFILE_OUTSIDE_UNLIT_DIAGNOSTIC',
    count:summary.materialInfos.filter(x=>x.metallic!==0||x.roughness!==1).length,
    recommendation:'Keep source PBR properties and plan native lighting validation; never silently remap roughness'});
if(summary.omittedUV0Count)
  issues.push({code:'SOME_MESHES_MISSING_UV0',
    count:summary.omittedUV0Count,
    recommendation:'Permit source UV absence for untextured materials only, not fabricated UVs'});
issues.push({code:'POSE_FRAME_REGISTRATION_NOT_YET_PROVEN',
  count:m.frames.length,
  recommendation:'Explicitly compare Work Z-up ROW-MAJOR native matrices to source glTF Y-up COLUMN-MAJOR rest/world via authoritative basis conversion; do not treat one as the other'});
if(importerStatus!=='ACCEPTED_AS_DIAGNOSTIC_ONLY')
  issues.push({code:'CURRENT_FIRST_PARTY_PILOT_IMPORTER_REJECTED_ACTUAL_SOURCE',
    message:firstPartyImporterError?.message,
    recommendation:'Add bounded source-first compatibility only; do not alter bone positions or source GLB'});
const report={
  kind:'hgpt-real-work-shoulder-g4g-exact-artifact-audit-v1',
  originalSource:{...ARTIFACT_SOURCE,verifiedActualSha256:digest(source),
    authoredManifestFileCount:Object.keys(m.files_sha256).length,
    verifiedCIArtifactFiles:Object.keys(m.files_sha256).filter(n=>!n.toLowerCase().endsWith('.blend')).length,
    nativeBlenderSceneIntentionallyPrivate:true,
    byteLength:source.length},
  verifiedAuthenticArtifactFiles:true,
  sourceWorkStatus:m.status,authorReportedAnatomyApproved:false,
  authorReportedMotionApproved:false,
  authorReportedProductionApproved:false,
  sourceSummary:summary,workAuthoredFrameCount:m.frames.length,
  nativeVsGLBBasisRegistered:false,firstPartyImporterStatus:importerStatus,
  firstPartyImporterError,issues,
  fullHumanMeshAvailable:false,
  actualHumanModelAccepted:false,
  clinicalAcceptance:false,verifiedRightsForDistribution:false,
  productionReady:false,
};
const output=path.resolve(process.argv[3]||
  'reports/work-pilot/real-work-shoulder-first-party-audit.json');
mkdirSync(path.dirname(output),{recursive:true});
writeFileSync(output,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({audit:report.kind,sourceSha256:digest(source),
  realMeshes:summary.meshCount,sourceControls:summary.skinJoints,
  authoredPoseFrames:m.frames.length,
  importerStatus,blockers:issues.map(x=>x.code),reportFile:output}));
