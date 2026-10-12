import test from 'node:test';
import assert from 'node:assert/strict';
import {boundedOriginalReviewViewport} from '../src/viewer/firstPartyOriginalReviewViewportBudget.mjs';
test('ordinary original review uses requested pixel ratio',()=>{
 const x=boundedOriginalReviewViewport(900,1200,1);
 assert.equal(x.pixelRatio,1);
 assert.equal(x.drawingBufferPixels,1_080_000);
 assert.equal(x.qualityReduced,false);
});
test('oversized 2x phone review is clamped to two million pixels',()=>{
 const x=boundedOriginalReviewViewport(2000,2400,2);
 assert.ok(x.qualityReduced);
 assert.ok(x.drawingBufferPixels<=2_000_000);
 assert.ok(x.estimatedRgba8Bytes<=8_000_000);
});
test('rejects invalid dimensions and ratios before allocating buffers',()=>{
 for(const args of [[0,1200,1],[900,Infinity,1],[900,1200,5],[-1,1000,1]])
  assert.throws(()=>boundedOriginalReviewViewport(...args),/outside documented bounds/);
});
test('viewport result is immutable and deterministic',()=>{
 const a=boundedOriginalReviewViewport(1600,1800,1.5);
 assert.deepEqual(a,boundedOriginalReviewViewport(1600,1800,1.5));
 assert.ok(Object.isFrozen(a));
});
