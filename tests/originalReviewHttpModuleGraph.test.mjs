/**
 * G5f: serve the real owner-local page and crawl its actual transitive native
 * module imports. Detect missing modules and blocked HTTP paths before a
 * private GLB is ever selected. Not a simulated human GPU draw.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createOriginalReviewLoopbackServer} from '../scripts/serve_original_review_local.mjs';

test('owner-local original viewer entire ES module graph serves without a remote import',async()=>{
 const server=createOriginalReviewLoopbackServer();
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try{
  const origin='http://127.0.0.1:'+server.address().port;
  const page=await fetch(origin+'/');
  assert.equal(page.status,200);
  const html=await page.text();
  const entry=html.match(/<script type="module" src="([^"]+)"/)?.[1];
  assert.equal(entry,'./originalFullBodyOwnerLocalReviewBoot.mjs');
  const queue=[new URL(entry,origin+'/').href];
  const visited=new Set();
  while(queue.length){
   const url=queue.shift();
   if(visited.has(url))continue;
   visited.add(url);
   assert.equal(new URL(url).origin,origin,'external dependency forbidden');
   const response=await fetch(url);
   assert.equal(response.status,200,'missing module '+url);
   assert.match(response.headers.get('content-type'),/javascript/);
   const src=await response.text();
   // Static ESM imports only; the review page must have no dynamic imports.
   assert.doesNotMatch(src,/\bimport\s*\(/,'dynamic imports cannot be audited here: '+url);
   const pattern=/\b(?:import|export)\s+(?:[^;]*?\s+from\s*)?['"]([^'"]+)['"]/gs;
   let match;
   while((match=pattern.exec(src))){
    assert.ok(match[1].startsWith('./')||match[1].startsWith('../'),
      'remote/bare import forbidden: '+match[1]);
    const child=new URL(match[1],url);
    assert.equal(child.origin,origin);
    queue.push(child.href);
   }
  }
  assert.ok(visited.size>=5,'expected transitive native renderer imports');
 }finally{
  await new Promise((resolve,reject)=>server.close(error=>error?reject(error):resolve()));
 }
});
