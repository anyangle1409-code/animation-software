#!/usr/bin/env node
/**
 * Actual headless Chromium WebGL2 proof, developer/test infrastructure only.
 * NOT an anatomical or production character visual acceptance.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { chromium } from 'playwright';

const PORT=5179;
const BASE='http://127.0.0.1:'+PORT+'/';
const REPORT_DIR=path.resolve('reports/browser-smoke/first-party-webgl2-prototype');
fs.mkdirSync(REPORT_DIR,{recursive:true});

const server=spawn(process.execPath,['node_modules/vite/bin/vite.js','--host','127.0.0.1','--port',String(PORT),'--strictPort'],
  {stdio:['ignore','pipe','pipe']});
let browser;
async function ready(){
  for(let i=0;i<80;i++){
    if(server.exitCode!==null)throw new Error('Vite exited before native browser proof');
    try{const r=await fetch(BASE);if(r.ok)return;}catch{}
    await new Promise(resolve=>setTimeout(resolve,250));
  }
  throw new Error('Dev server failed to start');
}
async function exerciseProof(page){
  const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto(BASE+'?hgptNativeSkeletonPreview=1',{waitUntil:'domcontentloaded'});
  await page.waitForSelector('[data-hgpt-native-viewport="skeleton-only-experimental"]',{timeout:20000});
  await page.waitForFunction(()=>{
    const canvas=document.querySelector('[data-hgpt-native-viewport] canvas');
    return canvas && Number(canvas.dataset.hgptNativeFrame)>=5 &&
      Number(canvas.dataset.hgptNativeBoneCount)>=35;
  },{timeout:25000});
  const report=await page.evaluate(async()=>{
    const canvas=document.querySelector('[data-hgpt-native-viewport] canvas');
    const {studioStore}=await import('/src/editor/storeCore.ts');
    const st=studioStore.getState();
    st.pause();st.setTime(0);
    const initial=studioStore.getState().time;
    st.play();
    return {
      frame:Number(canvas.dataset.hgptNativeFrame),
      bones:Number(canvas.dataset.hgptNativeBoneCount),
      canvasWidth:canvas.width,
      canvasHeight:canvas.height,
      renderer:canvas.dataset.hgptNativeRenderer,
      nativeContextLost:canvas.dataset.hgptNativeContextLost,
      initial,
    };
  });
  await page.waitForFunction(()=>{
    const canvas=document.querySelector('[data-hgpt-native-viewport] canvas');
    return Number(canvas.dataset.hgptNativeFrame)>10;
  },{timeout:10000});
  await page.waitForTimeout(220);
  const result=await page.evaluate(async()=>{
    const {studioStore}=await import('/src/editor/storeCore.ts');
    const state=studioStore.getState();
    state.pause();
    return {time:studioStore.getState().time,playing:studioStore.getState().playing};
  });
  assert.equal(report.renderer,'hgpt-native-webgl2-bones-v1');
  assert.equal(report.nativeContextLost,'false');
  assert.ok(report.canvasWidth>0 && report.canvasHeight>0);
  assert.ok(report.bones>=35);
  assert.ok(result.time>report.initial+0.01,'Native preview did not advance real exercise pose/playhead');
  assert.equal(result.playing,false);
  assert.deepEqual(errors,[],'Browser threw during real first-party GL preview');
  await page.screenshot({path:path.join(REPORT_DIR,'native-webgl2-skeleton-only-diagnostic.png')});
  return {...report,elapsedExerciseTime:result.time,pageErrors:errors,noncanonicalDiagnosticOnly:true};
}
async function defaultViewerUnchanged(page){
  const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto(BASE,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>{
    const canvas=document.querySelector('[data-hgpt-scene-host="first-party"] canvas');
    return canvas && Number(canvas.dataset.hgptFrameCount)>=3 &&
      Number(canvas.dataset.hgptRendererFrame)>0;
  },{timeout:35000});
  const report=await page.evaluate(()=>{
    const canvas=document.querySelector('[data-hgpt-scene-host="first-party"] canvas');
    return {
      hasExperimentalPreview:document.querySelectorAll('[data-hgpt-native-viewport]').length>0,
      originalThreeFrame:Number(canvas.dataset.hgptRendererFrame),
      originalStudioSceneChildren:Number(canvas.dataset.hgptSceneChildren),
      actualViewportOneCanvas:document.querySelectorAll('[data-hgpt-scene-host="first-party"] canvas').length===1
    };
  });
  assert.equal(report.hasExperimentalPreview,false);
  assert.equal(report.actualViewportOneCanvas,true);
  assert.ok(report.originalThreeFrame>0);
  assert.ok(report.originalStudioSceneChildren>0);
  assert.deepEqual(errors,[]);
  return report;
}
let complete=false;
try{
  await ready();
  browser=await chromium.launch({headless:true,args:['--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist']});
  const ctx=await browser.newContext({viewport:{width:1280,height:800}});
  const native=await ctx.newPage();
  const preview=await exerciseProof(native);
  const baseline=await ctx.newPage();
  const current=await defaultViewerUnchanged(baseline);
  const result={pass:true,preview,baseline:current,characterAndSkinParityClaimed:false,thirdPartyRemovedFromProduction:false};
  fs.writeFileSync(path.join(REPORT_DIR,'native-webgl2-vs-legacy-host-proof.json'),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify(result,null,2));
  complete=true;
}finally{
  await browser?.close().catch(()=>{});
  server.kill('SIGTERM');
}
if(!complete)process.exitCode=1;
