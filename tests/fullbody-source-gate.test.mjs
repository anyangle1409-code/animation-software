import fs from 'node:fs';import test from 'node:test';import assert from 'node:assert/strict';
import {verifyOriginalBodySourcePreflight} from '../src/viewer/firstPartyOriginalBodySourceGate.mjs';
const b=fs.readFileSync(process.env.HGPT_ORIGINAL_REVIEW_GLB);
const input=()=>b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength);
test('actual original source authenticated, six sparse corrective targets remain disabled',async()=>{
 const x=await verifyOriginalBodySourcePreflight(input(),{reviewOnly:true});
 assert.equal(x.originalVertices,17946);assert.equal(x.originalRuntimeJoints,67);
 assert.equal(x.zeroWeightedSparseCorrectiveMorphTargets,6);
 assert.equal(x.productionApproved,false);
});
test('rejects implicit production and tampered GLB',async()=>{
 await assert.rejects(verifyOriginalBodySourcePreflight(input()),/opt-in/);
 const tampered=input();new Uint8Array(tampered)[b.length-11]^=1;
 await assert.rejects(verifyOriginalBodySourcePreflight(tampered,{reviewOnly:true}),/SHA-256 mismatch/);
});
