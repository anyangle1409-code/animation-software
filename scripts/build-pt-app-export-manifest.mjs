import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';
const ROOT=path.resolve(path.dirname(new URL(import.meta.url).pathname),'..');
const hex64=x=>typeof x==='string'&&/^[0-9a-f]{64}$/.test(x);
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
export function validatePromotionContract(c){
 const e=[];if(c?.mode!=='approved_for_promotion')e.push('ORIGINAL-v1 promotion contract is not approved_for_promotion');
 if(!/^[0-9a-f]{40}$/.test(c?.source_track?.approved_source_commit??''))e.push('approved source commit missing');
 if(c?.required_runtime_metadata?.rigId!=='hgpt_canonical_v4_original')e.push('approved rig id is not canonical v4 original');
 for(const k of ['bare','dressed'])if(!hex64(c?.production_targets?.[k]?.sha256))e.push(k+' production character SHA-256 missing');
 return e;
}
export function buildManifest(input,dir,promotion){
 const e=validatePromotionContract(promotion);
 if(input?.schema_version!==2)e.push('input schema_version must be 2');
 if(input?.rig_version!=='hgpt_canonical_v4_original')e.push('rig_version must be hgpt_canonical_v4_original');
 if(input?.character_version!=='HomeGymPT_Male_ORIGINAL_v1')e.push('character_version must be HomeGymPT_Male_ORIGINAL_v1');
 if(input?.character_approval_status!=='production_approved')e.push('character must be production_approved');
 if(!hex64(input?.character_sha256))e.push('character_sha256 invalid');
 if(!input?.generator_version)e.push('generator_version missing');if(!input?.render_profile_version)e.push('render_profile_version missing');
 if(!Array.isArray(input?.assets)||!input.assets.length)e.push('assets missing');
 const seenE=new Set(),seenF=new Set(),assets=[];
 for(const [i,a] of (input?.assets??[]).entries()){
  const tag='asset['+i+'] ';
  if(!a.exercise_id||!a.source_exercise_id)e.push(tag+'exercise identity missing');
  if(seenE.has(a.exercise_id))e.push(tag+'duplicate exercise_id');seenE.add(a.exercise_id);
  if(!/\.(webm|mp4)$/i.test(a.filename??''))e.push(tag+'media must be WebM/MP4');
  if(seenF.has(a.filename))e.push(tag+'duplicate filename');seenF.add(a.filename);
  const media=path.resolve(dir,a.filename??'');if(!media.startsWith(path.resolve(dir)+path.sep)||!fs.existsSync(media))e.push(tag+'media missing/outside bundle');
  if(!hex64(a.source_animation_sha256))e.push(tag+'source_animation_sha256 invalid');
  if(a.validation_status!=='passed')e.push(tag+'animation validation not passed');
  if(a.provenance_classification!=='FIRST_PARTY_CONFIRMED'||a.generated_by_first_party_animation_software!==true)e.push(tag+'first-party provenance invalid');
  if(fs.existsSync(media))assets.push({...a,sha256:sha(media)});
 }
 if(e.length)throw new Error('PT APP EXPORT BLOCKED\n- '+e.join('\n- '));
 return {schema_version:2,generator_version:input.generator_version,rig_version:input.rig_version,character_version:input.character_version,character_sha256:input.character_sha256,character_approval_status:'production_approved',render_profile_version:input.render_profile_version,assets};
}
if(import.meta.url===new URL('file://'+process.argv[1]).href){
 const dir=path.resolve(process.argv[2]??'');const inputPath=path.resolve(process.argv[3]??'');
 if(!dir||!inputPath)throw new Error('usage: node scripts/build-pt-app-export-manifest.mjs <bundle-dir> <input.json>');
 const promotion=JSON.parse(fs.readFileSync(path.join(ROOT,'ORIGINAL_V1_PROMOTION_CONTRACT.json'),'utf8'));
 const input=JSON.parse(fs.readFileSync(inputPath,'utf8'));const out=buildManifest(input,dir,promotion);
 const target=path.join(dir,'animation-export.manifest.json');if(fs.existsSync(target))throw new Error('refusing to overwrite '+target);
 fs.writeFileSync(target,JSON.stringify(out,null,2)+'\n');console.log('PT APP EXPORT MANIFEST WRITTEN',target);
}
