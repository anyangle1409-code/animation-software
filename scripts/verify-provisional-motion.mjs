#!/usr/bin/env node
/** G4b original Work-source offline model + poses numeric preflight, no npm. */
import {readFile,stat} from 'node:fs/promises';
import {validateProvisionalModelHandoff} from
  '../src/viewer/firstPartyPrototypeModelHandoff.mjs';
import {compileProvisionalPoseSequence} from
  '../src/viewer/firstPartyPrototypePoseSequence.mjs';

async function readBounded(path,max){
  const size=(await stat(path)).size;
  if(!Number.isSafeInteger(size)||size<=0||size>max)
    throw new Error('Local source exceeds bounded offline size: '+max+' bytes');
  return readFile(path);
}
async function run(){
  if(process.argv.length!==5)
    throw new Error('Usage: node scripts/verify-provisional-motion.mjs <model.glb> <handoff.json> <pose-frames.json>');
  const [gpath,mpath,ppath]=process.argv.slice(2);
  const bytes=await readBounded(gpath,32*1024*1024);
  const glb=bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength);
  const manifest=JSON.parse((await readBounded(mpath,1024*1024)).toString('utf8'));
  const frames=JSON.parse((await readBounded(ppath,16*1024*1024)).toString('utf8'));
  const model=await validateProvisionalModelHandoff(glb,manifest);
  const compiled=compileProvisionalPoseSequence(model,frames);
  process.stdout.write(JSON.stringify({
    verdict:'VERIFIED_NUMERIC_PROTOTYPE_ONLY',
    candidateId:compiled.candidateId,
    assetSha256:compiled.sourceSha256,
    exerciseId:compiled.exerciseId,
    frameCount:compiled.frames.length,
    durationSeconds:compiled.durationSeconds,
    sourcePaletteJoints:compiled.runtimeBoneNames.length,
    modelAudit:model.audit,
    motionAudit:compiled.audit,
  },null,2)+'\n');
}
run().catch(e=>{
  process.stderr.write('G4b motion preflight FAILED: '+String(e?.message||e)+'\n');
  process.exitCode=1;
});
