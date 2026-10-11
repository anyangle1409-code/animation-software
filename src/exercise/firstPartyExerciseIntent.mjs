/**
 * G4c: first-party deterministic text -> EXERCISE INTENT contract.
 * No motion generated, no physiology guessed and no network/vendor libraries.
 * Unsupported, conflicting or silently lossy descriptions are rejected.
 */
export const HGPT_EXERCISE_INTENT_KIND='hgpt-original-exercise-intent-v1';
const fail=s=>{throw new RangeError('Exercise intent rejected: '+s)};
const need=(ok,s)=>{if(!ok)fail(s)};
const spec=(id,aliases,family,limb,checks)=>Object.freeze({
  id,aliases:Object.freeze(aliases),family,limb,checks:Object.freeze(checks)
});
const SH=['shoulder-girdle','scapulohumeral-coordination',
  'glenohumeral-rotation','elbow-motion','trunk-stability',
  'joint-ROM','equipment-contact'];
const PULL=['scapular-control','clavicle-coupling','elbow-motion',
  'grip','joint-ROM'];
const LOWER=['hip-motion','knee-motion','ankle-motion','balance',
  'ground-contact','joint-ROM'];
const HINGE=['lumbar-pelvic-control','hip-hinge','knee-motion',
  'ground-contact','joint-ROM'];
const ELBOW=['elbow-motion','forearm-rotation','wrist-alignment',
  'equipment-contact','joint-ROM'];
const TRUNK=['trunk-alignment','balance','ground-contact','joint-ROM'];
const EXERCISES=Object.freeze([
  spec('overhead_press',['shoulder press','overhead press','military press',
    'strict press'],'vertical-press','upper',SH),
  spec('bench_press',['bench press','chest press'],'horizontal-press','upper',SH),
  spec('push_up',['push up','push ups','pushup','pushups'],
    'horizontal-press','upper',SH),
  spec('pull_up',['pull up','pull ups','pullup','pullups'],
    'vertical-pull','upper',PULL),
  spec('chin_up',['chin up','chin ups','chinup','chinups'],
    'vertical-pull','upper',PULL),
  spec('lat_pulldown',['lat pulldown','lat pull down'],
    'vertical-pull','upper',PULL),
  spec('row',['row','bent over row','seated row'],
    'horizontal-pull','upper',PULL),
  spec('air_squat',['air squat'],'knee-dominant','lower',LOWER),
  spec('squat',['squat','squats'],'knee-dominant','lower',LOWER),
  spec('front_squat',['front squat'],'knee-dominant','lower',LOWER),
  spec('back_squat',['back squat'],'knee-dominant','lower',LOWER),
  spec('goblet_squat',['goblet squat'],'knee-dominant','lower',LOWER),
  spec('lunge',['lunge','lunges','reverse lunge','walking lunge'],
    'unilateral-leg','lower',LOWER),
  spec('split_squat',['split squat','bulgarian split squat'],
    'unilateral-leg','lower',LOWER),
  spec('deadlift',['deadlift','conventional deadlift'],
    'hip-hinge','lower',HINGE),
  spec('romanian_deadlift',['romanian deadlift','rdl'],
    'hip-hinge','lower',HINGE),
  spec('hip_hinge',['hip hinge','good morning'],
    'hip-hinge','lower',HINGE),
  spec('biceps_curl',['curl','biceps curl','bicep curl'],
    'elbow-flexion','upper',ELBOW),
  spec('hammer_curl',['hammer curl'],'elbow-flexion','upper',ELBOW),
  spec('triceps_extension',['triceps extension','tricep extension'],
    'elbow-extension','upper',ELBOW),
  spec('lateral_raise',['lateral raise','side raise'],
    'shoulder-abduction','upper',SH),
  spec('front_raise',['front raise'],
    'shoulder-flexion','upper',SH),
  spec('rear_delt_fly',['rear delt fly','reverse fly'],
    'shoulder-horizontal-abduction','upper',SH),
  spec('calf_raise',['calf raise','calf raises'],
    'ankle-plantarflexion','lower',LOWER),
  spec('plank',['plank','forearm plank'],
    'isometric-trunk','core',TRUNK),
  spec('crunch',['crunch','crunches','abdominal crunch'],
    'trunk-flexion','core',TRUNK)
]);
const MODIFIERS=Object.freeze([
  ['equipment','dumbbell',['dumbbells','dumbbell']],
  ['equipment','barbell',['barbells','barbell']],
  ['equipment','kettlebell',['kettlebells','kettlebell']],
  ['equipment','cable',['cable machine','cable']],
  ['equipment','band',['resistance bands','resistance band','bands','band']],
  ['equipment','bodyweight',['body weight','bodyweight']],
  ['equipment','machine',['machine']],
  ['side','left',['left arm','left leg','left']],
  ['side','right',['right arm','right leg','right']],
  ['side','unilateral-unspecified',['one arm','single arm','one leg',
    'single leg','unilateral']],
  ['side','alternating',['alternating']],
  ['side','bilateral',['bilateral','both arms','both legs']],
  ['posture','seated',['seated','sitting']],
  ['posture','standing',['standing']],
  ['posture','kneeling',['kneeling']],
  ['posture','supine',['supine']],
  ['posture','prone',['prone']],
  ['posture','incline',['incline']],
  ['posture','decline',['decline']],
  ['grip','neutral',['neutral grip']],
  ['grip','pronated',['pronated grip','overhand grip']],
  ['grip','supinated',['supinated grip','underhand grip']],
  ['grip','mixed',['mixed grip']]
]);
const ALTERNATIVES=MODIFIERS.flatMap(([field,key,words])=>
  words.map(phrase=>({field,key,phrase})))
  .sort((a,b)=>b.phrase.length-a.phrase.length);
const phraseToInput=s=>s.toLowerCase().replace(/-/g,' ')
  .replace(/\s+/g,' ').trim();

/**
 * This only identifies a bounded movement family and declared parameters.
 * A separate first-party solver must construct pose paths, contacts, load,
 * reciprocal balance and anatomy evidence or explicitly refuse generation.
 */
export function parseFirstPartyExerciseIntent(input){
  need(typeof input==='string'&&input.length>=3&&input.length<=160,
    '3..160 character exercise command required');
  const original=phraseToInput(input);
  need(original.length>=3&&original.length<=160 &&
    /^[a-z -]+$/.test(original),
    'letters only: loads/repetitions/extra qualifiers may not be ignored');
  let rest=' '+original+' ';
  const found={equipment:new Set(),side:new Set(),
    posture:new Set(),grip:new Set()};
  let sideLimb=null;
  for(const mod of ALTERNATIVES){
    // Each phrase is hardcoded ASCII words/spaces; no user text in RegExp.
    const re=new RegExp('(?<![a-z])'+mod.phrase+'(?![a-z])','g');
    if(!re.test(rest))continue;
    found[mod.field].add(mod.key);
    if(mod.field==='side'&&mod.phrase.endsWith(' arm'))
      sideLimb=sideLimb==='lower'?'conflict':'upper';
    if(mod.field==='side'&&mod.phrase.endsWith(' leg'))
      sideLimb=sideLimb==='upper'?'conflict':'lower';
    rest=rest.replace(re,' ');
  }
  rest=rest.replace(/\s+/g,' ').trim();
  const foundValues={};
  for(const [field,values] of Object.entries(found)){
    need(values.size<=1,'conflicting '+field+' modifiers');
    foundValues[field]=values.size?[...values][0]:null;
  }
  need(sideLimb!=='conflict','contradictory arm/leg qualifiers');
  const selected=EXERCISES.find(e=>e.aliases.includes(rest));
  need(Boolean(selected),'unknown or ambiguous exercise: '+rest.slice(0,80));
  if(sideLimb)
    need(selected.limb===sideLimb,'side-specific limb contradicts exercise');
  if(selected.limb==='core')
    need(foundValues.side===null,'side-specific core version not implemented');
  if(['push_up','plank'].includes(selected.id))
    need(foundValues.equipment===null||foundValues.equipment==='bodyweight',
      'equipment variant needs authored specific contacts');
  return Object.freeze({
    kind:HGPT_EXERCISE_INTENT_KIND,status:'INTENT_ONLY',
    source:Object.freeze({
      command:original,movementId:selected.id,
      movementFamily:selected.family,primaryLimb:selected.limb,
      equipment:foundValues.equipment,
      laterality:foundValues.side,
      posture:foundValues.posture,grip:foundValues.grip,
    }),
    requiredBiomechanicsVerification:Object.freeze([...selected.checks]),
    realHumanPoseGenerated:false,contactAndLoadDynamicsVerified:false,
    clinicallyApprovedROM:false,productionAnimationReady:false
  });
}
export function supportedFirstPartyExerciseIntentIds(){
  return Object.freeze(EXERCISES.map(x=>x.id));
}
