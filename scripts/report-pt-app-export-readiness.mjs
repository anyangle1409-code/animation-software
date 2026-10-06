import fs from 'node:fs';import path from 'node:path';
const ROOT=path.resolve(path.dirname(new URL(import.meta.url).pathname),'..');
const promotion=JSON.parse(fs.readFileSync(path.join(ROOT,'ORIGINAL_V1_PROMOTION_CONTRACT.json'),'utf8'));
const mapping=JSON.parse(fs.readFileSync(path.join(ROOT,'contracts','pt-app-exercise-id-map.json'),'utf8'));
const checks=[
 ['promotion_mode',promotion.mode==='approved_for_promotion',promotion.mode],
 ['approved_source_commit',/^[0-9a-f]{40}$/.test(promotion?.source_track?.approved_source_commit??''),promotion?.source_track?.approved_source_commit??'missing'],
 ['rig_identity',promotion?.required_runtime_metadata?.rigId==='hgpt_canonical_v4_original',promotion?.required_runtime_metadata?.rigId??'missing'],
 ['bare_character_hash',/^[0-9a-f]{64}$/.test(promotion?.production_targets?.bare?.sha256??''),promotion?.production_targets?.bare?.sha256??'missing'],
 ['dressed_character_hash',/^[0-9a-f]{64}$/.test(promotion?.production_targets?.dressed?.sha256??''),promotion?.production_targets?.dressed?.sha256??'missing'],
 ['exercise_map',Array.isArray(mapping.entries)&&mapping.entries.length>0,mapping.entries?.length??0],
];
const direct=(mapping.entries??[]).filter(x=>x.status==='direct_confirmed').length;
console.log('PT APP EXPORT READINESS');
for(const [name,ok,detail] of checks)console.log((ok?'PASS ':'BLOCK')+' '+name+': '+detail);
console.log('INFO direct-confirmed exercise mappings: '+direct);
const blocked=checks.filter(x=>!x[1]).length;
console.log(blocked?('BLOCKED — '+blocked+' prerequisite(s) remain.'):'READY — producer prerequisites are satisfied; run render/export acceptance next.');
process.exitCode=blocked?1:0;
