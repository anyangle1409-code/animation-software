#!/usr/bin/env node
/**
 * Offline Work -> GPT first-party model handoff check.
 * Reads local files only; prints scalar/identity audit, never GLB/medical bytes.
 * PROTOTYPE ONLY: passing is not real human anatomy or release acceptance.
 */
import {readFile,stat} from 'node:fs/promises';
import {validateProvisionalModelHandoff}
  from '../src/viewer/firstPartyPrototypeModelHandoff.mjs';

async function main(){
  if(process.argv.length!==4)
    throw new Error('Usage: node scripts/verify-provisional-handoff.mjs <model.glb> <manifest.json>');
  const [file,manifestPath]=process.argv.slice(2);
  const size=(await stat(file)).size;
  if(!Number.isSafeInteger(size)||size<28||size>32*1024*1024)
    throw new Error('GLB must fit the strict current 32 MiB offline prototype gate');
  const buffer=await readFile(file);
  const binary=buffer.buffer.slice(buffer.byteOffset,buffer.byteOffset+buffer.byteLength);
  const descriptor=JSON.parse(await readFile(manifestPath,'utf8'));
  const checked=await validateProvisionalModelHandoff(binary,descriptor);
  process.stdout.write(JSON.stringify({
    verdict:'VERIFIED_PROTOTYPE_ONLY',
    candidateId:checked.candidateId,
    sourceSha256:checked.sourceSha256,
    primitives:checked.numberOfPrimitives,
    sourceJointNames:checked.sourceJointNames,
    runtimeJointNames:checked.runtimeJointNames,
    audit:checked.audit,
  },null,2)+'\n');
}
main().catch(err=>{
  process.stderr.write('G4 handoff FAILED: '+String(err?.message||err)+'\n');
  process.exitCode=1;
});
