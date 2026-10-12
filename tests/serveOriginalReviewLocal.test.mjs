import test from 'node:test';
import assert from 'node:assert/strict';
import {createOriginalReviewLoopbackServer} from '../scripts/serve_original_review_local.mjs';
import {request} from 'node:http';
async function withServer(fn){
 const server=createOriginalReviewLoopbackServer();
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try{await fn(server.address().port)}finally{
  await new Promise((resolve,reject)=>server.close(err=>err?reject(err):resolve()));
 }
}
function hit(port,path,method='GET'){
 return new Promise((resolve,reject)=>{
  const req=request({hostname:'127.0.0.1',port,path,method},res=>{
   const chunks=[];res.on('data',c=>chunks.push(c));
   res.on('end',()=>resolve({status:res.statusCode,headers:res.headers,
    body:Buffer.concat(chunks).toString('utf8')}));
  });req.on('error',reject);req.end();
 });
}
test('serves only local review HTML and first-party module files',()=>withServer(async p=>{
 const page=await hit(p,'/');
 assert.equal(page.status,200);
 assert.match(page.body,/ORIGINAL_v1/);
 assert.equal(page.headers['cache-control'],'no-store');
 const js=await hit(p,'/firstPartyOriginalFullBodyLocalReview.mjs');
 assert.equal(js.status,200);
 assert.match(js.headers['content-type'],/javascript/);
}));
test('rejects GLB, blend, directory traversal and foreign sites',()=>withServer(async p=>{
 for(const path of ['/HomeGymPT_Male_ORIGINAL_v1_REVIEW_ONLY.glb',
 '/private.blend','/%2e%2e/secret','/../secret',
 '/originalFullBodyOwnerLocalReview.html?fake=ok/../../foo.glb']){
  const r=await hit(p,path);
  if(path.includes('?fake'))assert.equal(r.status,200);
  else assert.equal(r.status,404,path);
 }
}));
test('rejects writes, upload methods and unlisted HTML',()=>withServer(async p=>{
 assert.equal((await hit(p,'/','POST')).status,405);
 assert.equal((await hit(p,'/test.html')).status,404);
 assert.equal((await hit(p,'/','HEAD')).body,'');
}));
