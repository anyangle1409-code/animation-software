import { readFileSync,writeFileSync,mkdirSync } from 'node:fs';
import { it,expect } from 'vitest';
import { Matrix4,Vector3 } from 'three';
import { retargetedCharacterSource } from '../../src/character/retargetSource';
import { canonicalSkeleton as rig,PoseEvaluation } from '../../src/rig/skeleton';
import { generateClip } from '../../src/animation/generate';
import { sampleClip } from '../../src/animation/clip';
import { resolveFrame } from '../../src/animation/pipeline';
import { lockAnchors } from '../../src/constraints/locks';
import { applyCharacterPose } from '../../src/character/pose';
import { EXERCISES } from '../../src/exercises/library';
import { equipmentSocketForInstance } from '../../src/equipment/library';
import { anatomicalGripOffset } from '../../src/equipment/attach';
import { handAttachmentMatrix } from '../../src/export/clipBuilder';
import { validateClip } from '../../src/animation/validate';
import { EQUIPMENT_PARTS } from '../../src/equipment/geometry';
const version=process.env.CANDIDATE_VERSION??'v3';
const dest=`../reports/poses_${version}`;mkdirSync(dest,{recursive:true});
const sources={baseline:'../HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb',candidate:`../HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_${version}.glb`};
it('compares all five exercises with frozen rig, correctives and actual equipment frames',async()=>{
 const report:any={sources:{},exercises:[]};const builds:any={};
 for(const [id,path]of Object.entries(sources)){const b=readFileSync(path);const s=retargetedCharacterSource({id,label:id,data:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength)});builds[id]=await s.build(rig);report.sources[id]=s.lastReport;}
 expect(report.sources.candidate.height).toBeCloseTo(report.sources.baseline.height,7);
 for(const ex of EXERCISES){const clip=generateClip(rig,ex),ev=new PoseEvaluation(rig),anchors=lockAnchors(ev,sampleClip(clip,0).pose,clip.locks);const validation=validateClip(rig,new PoseEvaluation(rig),ex,clip);const peak=clip.keyframes.find(m=>m.marker==='peak')?.time??clip.duration*.4;
 const frames=[['bottom',0],...Array.from({length:23},(_,i)=>[`sample_${i+1}`,clip.duration*(i+1)/24]),['peak',peak],['return',clip.duration]] as [string,number][];let maxHand=0,maxBones=0,maxEquipment=0,maxFloor=0;const start:any={};
 for(const [label,t] of frames){const f=resolveFrame(rig,ev,clip,t,{anchors});const pair:any={};for(const [id,c]of Object.entries(builds) as any){applyCharacterPose(c,rig,f.pose,ev,{contacts:f.contacts,grip:{kind:ex.hands.grip,closure:ex.hands.closure}});
 const body=c.meshes.find((m:any)=>/freeman/i.test(m.name));const meshes=[];const p=new Vector3();
 for(const m of c.meshes){m.skeleton.update();m.updateWorldMatrix(true,false);const positions=[];for(let i=0;i<m.geometry.getAttribute('position').count;i++){m.getVertexPosition(i,p);p.applyMatrix4(m.matrixWorld);if(!Number.isFinite(p.x)||!Number.isFinite(p.y)||!Number.isFinite(p.z)) throw new Error(`Non-finite ${id} ${ex.id} ${label} vertex ${i}`);positions.push(p.toArray());}meshes.push({name:m.name,positions,indices:Array.from(m.geometry.index.array)});}
 if(ex.id==='dumbbell_bicep_curl'&&label==='bottom'&&id==='baseline'){
  const matrices=body.skeleton.bones.map((_:any,j:number)=>new Matrix4().multiplyMatrices(body.matrixWorld,body.bindMatrixInverse).multiply(new Matrix4().fromArray(body.skeleton.boneMatrices,16*j)).multiply(body.bindMatrix).toArray());
  writeFileSync('../reports/v10_actual_curl_skin_matrices.json',JSON.stringify({boneNames:body.skeleton.bones.map((b:any)=>b.name),matrices}));
 }
 const bones=c.bones.map((b:any)=>b.matrixWorld.toArray());const equipment=[];
 for(const instance of clip.equipment){let matrix=f.equipment.get(instance.id)?.matrix?.clone();if(instance.attachment.mode==='hand'){const side=instance.attachment.side;const hand=c.handMatrix?.(side,new Matrix4());if(hand){const socket=equipmentSocketForInstance(instance,instance.attachment.socket);matrix=hand.clone().multiply(handAttachmentMatrix(instance.attachment.gripOffset??c.gripOffset?.(side)??anatomicalGripOffset(side),socket?.position??{x:0,y:0,z:0},{gripRotation:instance.attachment.gripRotation,socketRotation:socket?.rotation}));}}if(matrix)equipment.push({kind:instance.kind,matrix:matrix.toArray(),parts:EQUIPMENT_PARTS[instance.kind]});}
 const hands=[];const si=body.geometry.getAttribute('skinIndex'),sw=body.geometry.getAttribute('skinWeight');for(let i=0;i<10839;i++){let w=0;for(let lane=0;lane<4;lane++)if(/hand|palm|f_|thumb/.test(body.skeleton.bones[si.getComponent(i,lane)].name))w+=sw.getComponent(i,lane);if(w>.001)hands.push(meshes[0].positions[i]);}
 const handFloor={l:Infinity,r:Infinity};
 for(let i=0;i<body.geometry.getAttribute('position').count;i++){
   let owned=0;
   for(let lane=0;lane<4;lane++){
    const name=body.skeleton.bones[si.getComponent(i,lane)].name;
    if(/hand|palm|f_|thumb/.test(name))owned+=sw.getComponent(i,lane);
   }
   if(owned>.001){const side=body.geometry.getAttribute('position').getX(i)>0?'l':'r';handFloor[side]=Math.min(handFloor[side],meshes[0].positions[i][1]);}
 }
 pair[id]={bones,hands,equipment,meshes,handFloor};if(label==='bottom')start[id]=meshes.map(m=>m.positions);
 if(label==='return'){let loop=0;meshes.forEach((m,mi)=>m.positions.forEach((p,i)=>loop=Math.max(loop,new Vector3(...p).distanceTo(new Vector3(...start[id][mi][i])))));expect(loop).toBeLessThan(1e-6);}
 if (!label.startsWith('sample_') || label==='sample_12') writeFileSync(`${dest}/${ex.id}_${label}_${id}.json`,JSON.stringify({exercise:ex.name,label,time:t,meshes,equipment}));
 }
 const a=pair.baseline,b=pair.candidate;
 if(ex.id==='push_up')for(const side of ['l','r']){
  const difference=Math.abs(a.handFloor[side]-b.handFloor[side]);
  maxFloor=Math.max(maxFloor,difference);
  expect(difference).toBeLessThan(1e-6);
 }
 expect(b.hands.length).toBe(a.hands.length);a.hands.forEach((p:any,i:number)=>maxHand=Math.max(maxHand,new Vector3(...p).distanceTo(new Vector3(...b.hands[i]))));a.bones.forEach((m:any,i:number)=>m.forEach((v:number,k:number)=>maxBones=Math.max(maxBones,Math.abs(v-b.bones[i][k]))));a.equipment.forEach((m:any,i:number)=>m.matrix.forEach((v:number,k:number)=>maxEquipment=Math.max(maxEquipment,Math.abs(v-b.equipment[i].matrix[k]))));
 }
 report.exercises.push({name:ex.name,frames:frames.length,handMaxDifferenceMm:maxHand*1000,boneMatrixMaxDifference:maxBones,equipmentMatrixMaxDifference:maxEquipment,pushupFloorMaxDifferenceMm:maxFloor*1000,techniqueViolations:validation.violations.map(v=>v.ruleId),unreachable:validation.unreachable,loopClosed:validation.loopClosed});console.log('EXERCISE_DIFFERENCE',ex.name,{maxBones,maxHand,maxEquipment});expect(maxBones).toBeLessThan(1e-6);expect(maxHand).toBeLessThan(0.01);expect(maxEquipment).toBeLessThan(1e-6);
 }
 writeFileSync(`../reports/exercise_validation_${version}.json`,JSON.stringify(report,null,2));console.log(JSON.stringify(report.exercises));Object.values(builds).forEach((c:any)=>c.dispose());
},900000);
