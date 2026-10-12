import {readFileSync} from 'node:fs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {
  HGPT_LOCAL_FULLBODY_REVIEW_KIND,
  ORIGINAL_V1_REVIEW_PINNED_SHA,
  ORIGINAL_V1_REVIEW_PINNED_BYTES,
  cameraForOriginalFullBodyReview,
  openOriginalFullBodyOwnerLocalReview,
  bindOriginalFullBodyOwnerLocalControls
} from '../src/viewer/firstPartyOriginalFullBodyLocalReview.mjs';

const fakeCanvas={
  getContext(){throw new Error('GPU must never be called before full SHA validation')},
  addEventListener(){},removeEventListener(){},
};
const goodFile=()=>({
  name:'HomeGymPT_Male_ORIGINAL_v1_REVIEW_ONLY.glb',
  size:ORIGINAL_V1_REVIEW_PINNED_BYTES,
  async arrayBuffer(){return new ArrayBuffer(ORIGINAL_V1_REVIEW_PINNED_BYTES)}
});
test('strict review source hash, original size and never-production classifier are explicit',()=>{
  assert.equal(ORIGINAL_V1_REVIEW_PINNED_SHA,
    'd267dac344affb5d52c7155f8d0254794e818a8eab3ad54f7f263694f36c390d');
  assert.equal(ORIGINAL_V1_REVIEW_PINNED_BYTES,1495720);
  assert.equal(HGPT_LOCAL_FULLBODY_REVIEW_KIND,
    'hgpt-original-local-owner-file-neutral-review-v1');
});
test('five fixed-scale neutral cameras use only glTF Y-up and copy mutable caller arrays',()=>{
  const seen=new Set();
  for(const view of ['front','rear','left','right','three-quarter']){
    const camera=cameraForOriginalFullBodyReview(view);
    assert.equal(camera.view,view);
    assert.deepEqual(camera.target,[0,.91,0]);
    assert.equal(camera.eye.length,3);
    assert.ok(Math.hypot(...camera.eye)>2.5);
    assert.match(camera.status,/DIAGNOSTIC_CAMERA_/);
    seen.add(camera.eye.join(','));
    camera.eye[0]=999;
    assert.notEqual(cameraForOriginalFullBodyReview(view).eye[0],999);
  }
  assert.equal(seen.size,5);
});
test('invalid camera/malicious camera input cannot generate unverified model views',()=>{
  for(const bad of ['', 'clinical-approval', 'shoulder-motion',null,
    {}, '__proto__','foot-length-fixed']){
    assert.throws(()=>cameraForOriginalFullBodyReview(bad),
      /camera must be one of the five bounded/);
  }
});
test('no remote URL, wrong name, unbounded length or a forged local file accepted',async()=>{
  for(const ownerFile of [
    'https://example.invalid/original.glb',
    {name:'untrusted.glb',size:ORIGINAL_V1_REVIEW_PINNED_BYTES,arrayBuffer:async()=>new ArrayBuffer(0)},
    {name:'HomeGymPT_Male_ORIGINAL_v1_REVIEW_ONLY.glb',size:10,arrayBuffer:async()=>new ArrayBuffer(10)},
    {name:'HomeGymPT_Male_ORIGINAL_v1_REVIEW_ONLY.glb',size:ORIGINAL_V1_REVIEW_PINNED_BYTES},
    {name:'HomeGymPT_Male_ORIGINAL_v1_REVIEW_ONLY.glb',size:ORIGINAL_V1_REVIEW_PINNED_BYTES,
      arrayBuffer(){throw new Error('Should not be called with bad canvas')}},
  ]){
    const bad=ownerFile?.arrayBuffer&&ownerFile?.name==='HomeGymPT_Male_ORIGINAL_v1_REVIEW_ONLY.glb'&&
      ownerFile?.size===ORIGINAL_V1_REVIEW_PINNED_BYTES?
      null:ownerFile;
    if(bad!==null)
      await assert.rejects(
        ()=>openOriginalFullBodyOwnerLocalReview({ownerFile:bad,canvas:fakeCanvas}),
        /select the exact ORIGINAL_v1 review GLB locally/);
  }
});
test('the original file bytes are checked before any GPU context or source-mesh render',async()=>{
  let reads=0,draws=0;
  const ownerFile=goodFile();
  ownerFile.arrayBuffer=async()=>{reads++;return new ArrayBuffer(ORIGINAL_V1_REVIEW_PINNED_BYTES)};
  const canvas={...fakeCanvas,getContext(){draws++;throw Error('GPU must not run')}};
  await assert.rejects(
    ()=>openOriginalFullBodyOwnerLocalReview({ownerFile,canvas}),
    /source SHA mismatch/);
  assert.equal(reads,1);
  assert.equal(draws,0);
});
test('wrong actual file length refused before source SHA even for nominal correct filename',async()=>{
  const ownerFile=goodFile();
  ownerFile.arrayBuffer=async()=>new ArrayBuffer(300);
  await assert.rejects(()=>openOriginalFullBodyOwnerLocalReview({ownerFile,canvas:fakeCanvas}),
    /file bytes changed during read/);
});
test('unsupported viewport and missing WebGL2 surface refused without touching the file',async()=>{
  let reads=0;
  const ownerFile=goodFile();ownerFile.arrayBuffer=async()=>{reads++;return new ArrayBuffer(20)};
  for(const options of [
    {width:20},{height:3000},{pixelRatio:9},{view:'forced-human-motion'},
  ]){
    await assert.rejects(
      ()=>openOriginalFullBodyOwnerLocalReview({
        ownerFile,canvas:fakeCanvas,...options}),
      /viewport required|camera must be one of the five bounded/);
  }
  await assert.rejects(
    ()=>openOriginalFullBodyOwnerLocalReview({
      ownerFile,canvas:{notARealCanvas:true}
    }),/local WebGL2 canvas required/);
  assert.equal(reads,0);
});
test('DOM review controls refuse inert or remote elements',()=>{
  assert.throws(()=>bindOriginalFullBodyOwnerLocalControls({
    fileInput:{type:'text',addEventListener(){}},
    cameraSelector:{tagName:'SELECT',addEventListener(){}},
    statusTarget:{textContent:'state'},
  }),/manual source file\/select\/status DOM controls required/);
  assert.throws(()=>bindOriginalFullBodyOwnerLocalControls({
    fileInput:{type:'file',addEventListener(){}},
    cameraSelector:{tagName:'BUTTON',addEventListener(){}},
    statusTarget:{textContent:'state'},
  }),/manual source file\/select\/status DOM controls required/);
});
test('DOM review controls can dispose without ever reading an original file',()=>{
  const added=[],removed=[];
  const el=(name)=>({
    type:name==='source'?'file':undefined,
    tagName:name==='camera'?'SELECT':undefined,
    addEventListener(t,fn){added.push([name,t,fn])},
    removeEventListener(t,fn){removed.push([name,t,fn])},
  });
  const fileInput=el('source'),cameraSelector=el('camera');
  const controls=bindOriginalFullBodyOwnerLocalControls({
    fileInput,cameraSelector,statusTarget:{textContent:'Choose file'},
  });
  assert.equal(added.length,2);
  controls.dispose();
  assert.deepEqual(removed,added);
});


// G4v: cancellation and out-of-order selection regressions.
// The source bytes in these tests are intentionally invalid: an obsolete
// selection MUST stop before authenticating them or touching the renderer.
function pendingFileBytes(){
  let resolve;
  const promise=new Promise(r=>{resolve=r});
  return {promise,resolve};
}
function localControlsForConcurrency(canvas){
  const handlers={};
  const fileInput={
    type:'file',files:[],
    addEventListener(type,fn){handlers['file-'+type]=fn},
    removeEventListener(type,fn){if(handlers['file-'+type]===fn)delete handlers['file-'+type]},
  };
  const cameraSelector={
    tagName:'SELECT',value:'front',
    addEventListener(type,fn){handlers['camera-'+type]=fn},
    removeEventListener(type,fn){if(handlers['camera-'+type]===fn)delete handlers['camera-'+type]},
  };
  const statusTarget={textContent:'Select a file'};
  const controls=bindOriginalFullBodyOwnerLocalControls({
    fileInput,canvas,cameraSelector,statusTarget
  });
  return {handlers,fileInput,cameraSelector,statusTarget,controls};
}
test('already-cancelled owner file cannot read, hash or create WebGL2',async()=>{
  let reads=0,gpus=0;
  const controller=new AbortController();controller.abort();
  const ownerFile=goodFile();
  ownerFile.arrayBuffer=async()=>{reads++;throw Error('must not read')};
  const canvas={...fakeCanvas,getContext(){gpus++;throw Error('must not GPU')}};
  await assert.rejects(
    ()=>openOriginalFullBodyOwnerLocalReview({
      ownerFile,canvas,signal:controller.signal
    }),/owner file selection cancelled/);
  assert.equal(reads,0);assert.equal(gpus,0);
});
test('cancelled in-flight source read stops before actual SHA and GPU',async()=>{
  let gpus=0;
  const pending=pendingFileBytes();
  const controller=new AbortController();
  const ownerFile=goodFile();
  ownerFile.arrayBuffer=()=>pending.promise;
  const canvas={...fakeCanvas,getContext(){gpus++;throw Error('must not GPU')}};
  const loading=openOriginalFullBodyOwnerLocalReview({
    ownerFile,canvas,signal:controller.signal
  });
  controller.abort();
  pending.resolve(new ArrayBuffer(ORIGINAL_V1_REVIEW_PINNED_BYTES));
  await assert.rejects(loading,/owner file selection cancelled/);
  assert.equal(gpus,0);
});
test('clearing file selection supersedes slower first read with no stale GPU or status',async()=>{
  let gpus=0;
  const pending=pendingFileBytes();
  const ownerFile=goodFile();
  ownerFile.arrayBuffer=()=>pending.promise;
  const canvas={...fakeCanvas,getContext(){gpus++;throw Error('must not GPU')}};
  const ui=localControlsForConcurrency(canvas);
  ui.fileInput.files=[ownerFile];
  const loading=ui.handlers['file-change']();
  assert.match(ui.statusTarget.textContent,/Checking original source/);
  ui.fileInput.files=[];
  await ui.handlers['file-change']();
  assert.match(ui.statusTarget.textContent,/Select the original review-only GLB/);
  pending.resolve(new ArrayBuffer(ORIGINAL_V1_REVIEW_PINNED_BYTES));
  await loading;
  assert.match(ui.statusTarget.textContent,/Select the original review-only GLB/);
  assert.equal(gpus,0);
  ui.controls.dispose();
});
test('closing UI during source read permanently blocks stale completion',async()=>{
  let gpus=0;
  const pending=pendingFileBytes();
  const ownerFile=goodFile();
  ownerFile.arrayBuffer=()=>pending.promise;
  const canvas={...fakeCanvas,getContext(){gpus++;throw Error('must not GPU')}};
  const ui=localControlsForConcurrency(canvas);
  ui.fileInput.files=[ownerFile];
  const loading=ui.handlers['file-change']();
  ui.controls.dispose();
  assert.equal(ui.statusTarget.textContent,'Original review closed.');
  assert.equal(ui.handlers['file-change'],undefined);
  pending.resolve(new ArrayBuffer(ORIGINAL_V1_REVIEW_PINNED_BYTES));
  await loading;
  assert.equal(ui.statusTarget.textContent,'Original review closed.');
  assert.equal(gpus,0);
  ui.controls.dispose(); // idempotent
});
test('invalid optional cancellation signal fails before source read',async()=>{
  let reads=0;
  const ownerFile=goodFile();ownerFile.arrayBuffer=async()=>{reads++;return new ArrayBuffer(8)};
  await assert.rejects(
    ()=>openOriginalFullBodyOwnerLocalReview({ownerFile,canvas:fakeCanvas,signal:{}}),
    /optional cancellation signal must be AbortSignal-compatible/);
  assert.equal(reads,0);
});

test('G5h optional latest-camera callback must be callable before original file read',async()=>{
 let reads=0;
 const ownerFile=goodFile();ownerFile.arrayBuffer=async()=>{reads++;return new ArrayBuffer(0)};
 await assert.rejects(()=>openOriginalFullBodyOwnerLocalReview({
  ownerFile,canvas:fakeCanvas,currentView:'rear'
 }),/current camera must be an optional local function/);
 assert.equal(reads,0);
});
test('G5h DOM review uses a live camera getter rather than capturing the first selection',()=>{
 const src=readFileSync(new URL('../src/viewer/firstPartyOriginalFullBodyLocalReview.mjs',import.meta.url),'utf8');
 assert.ok(src.includes('currentView:()=>cameraSelector.value'));
 assert.ok(src.includes('renderView(currentView===undefined?firstCamera.view:currentView())'));
});
