/**
 * Cloud compatibility probe for immutable provisional r95 exports.
 * A successful job can report BLOCKED intake; it is never model acceptance.
 */
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {parseOriginalFullBodyReviewGLB,assertAuthenticatedOriginalFullBodyReviewUnmodified}
 from '../src/viewer/firstPartyOriginalFullBodyReview.mjs';
import {prepareVerifiedOriginalFullBodyRestGpu}
 from '../src/viewer/firstPartyOriginalFullBodyGpuRest.mjs';
import {openOriginalFullBodyOwnerLocalReview,ORIGINAL_V1_REVIEW_PINNED_SHA,ORIGINAL_V1_REVIEW_PINNED_BYTES}
 from '../src/viewer/firstPartyOriginalFullBodyLocalReview.mjs';

const directory='ORIGINAL_V1_WORK/candidates/exports/r95_phase4_freeze';
const pins={
 bare:{bytes:1496696,sha256:'c4b8e388e624a4a3d22510b40c1fc45017b3374b1ff9de2cae79f2dbb0797c85'},
 dressed:{bytes:1126108,sha256:'12ba867ed80e54d9e6b6f626ff584f69e996c1437ffaa15bf2f6ae158e00dcbe'}
};
const manifest=JSON.parse(await readFile(directory+'/CANDIDATE_GLB_EXPORT.json','utf8'));
assert.equal(manifest.production_approved,false);
assert.equal(manifest.visual_review_available,false);
assert.equal(manifest.candidate_revision,'r95');
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const report={schemaVersion:1,stage:'PROVISIONAL_SOURCE_COMPATIBILITY_DIAGNOSTIC',
 productionApproved:false,anatomicalAcceptance:false,rightsAcceptance:false,
 actualHumanMovementVerified:false,gpuDrawPerformed:false,variants:[]};
for(const variant of ['bare','dressed']){
 const pin=pins[variant],record=manifest.exports[variant];
 assert.equal(record.bytes,pin.bytes);assert.equal(record.sha256,pin.sha256);
 const bytes=await readFile(directory+'/'+record.file);
 assert.equal(bytes.length,pin.bytes);assert.equal(sha(bytes),pin.sha256);
 const input=bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength);
 const view=new DataView(input);
 assert.equal(view.getUint32(0,true),0x46546c67);
 assert.equal(view.getUint32(4,true),2);assert.equal(view.getUint32(8,true),bytes.length);
 assert.equal(view.getUint32(16,true),0x4e4f534a);
 const root=JSON.parse(new TextDecoder().decode(new Uint8Array(input,20,view.getUint32(12,true))));
 const result={variant,sha256:pin.sha256,bytes:bytes.length,
  meshes:root.meshes?.length??0,skins:root.skins?.length??0,
  joints:root.skins?.[0]?.joints?.length??0,
  morphNames:root.meshes?.map(m=>m.extras?.targetNames??[]),
  animationCount:root.animations?.length??0,
  boneDisplayNodes:(root.nodes??[]).filter(n=>/icosphere/i.test(n.name??'')).map(n=>n.name),
  intake:'BLOCKED',restPreparation:'NOT_REACHED'};
 assert.equal(result.boneDisplayNodes.length,0,'bone display object must not enter export');
 let review;
 try{review=await parseOriginalFullBodyReviewGLB(input,{expectedSha256:pin.sha256});}
 catch(error){if(!(error instanceof RangeError))throw error;result.intakeReason=error.message;}
 if(review){
  assertAuthenticatedOriginalFullBodyReviewUnmodified(review);
  assert.equal(review.audit.productionReady,false);
  assert.equal(review.audit.independentAnatomicalAcceptance,false);
  result.intake='PARSED_REVIEW_ONLY';
  result.vertices=review.vertices;result.triangles=review.triangles;
  result.restInverseBindResidual=review.audit.maximumRestInverseBindResidual;
  try{
   const prepared=prepareVerifiedOriginalFullBodyRestGpu(review);
   assert.equal(prepared.productionReady,false);
   result.restPreparation='PREPARED_NOT_RENDERED';
  }catch(error){if(!(error instanceof RangeError))throw error;result.restPreparation='BLOCKED';result.restReason=error.message;}
 }
 await assert.rejects(parseOriginalFullBodyReviewGLB(input,{expectedSha256:'0'.repeat(64)}),/source SHA mismatch/);
 assert.notEqual(pin.sha256,ORIGINAL_V1_REVIEW_PINNED_SHA);
 assert.notEqual(pin.bytes,ORIGINAL_V1_REVIEW_PINNED_BYTES);
 // The strict owner intake refuses this different export before canvas/read access.
 let touched=false;
 await assert.rejects(openOriginalFullBodyOwnerLocalReview({
  ownerFile:{name:'HomeGymPT_Male_ORIGINAL_v1_REVIEW_ONLY.glb',size:pin.bytes,
   arrayBuffer(){touched=true;return input;}}
 }),/select the exact ORIGINAL_v1 review GLB locally/);
 assert.equal(touched,false);
 assert.equal(sha(new Uint8Array(input)),pin.sha256,'probe changed source bytes');
 result.sourceUnmodified=true;result.strictOwnerGateRefused=true;result.wrongShaRefused=true;
 report.variants.push(result);
}
await mkdir('artifacts',{recursive:true});
await writeFile('artifacts/r95-runtime-compatibility.json',JSON.stringify(report,null,2)+'\n');
console.log('R95_COMPATIBILITY_DIAGNOSTIC '+JSON.stringify(report));
