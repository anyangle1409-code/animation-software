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
const dest='../reports/poses';mkdirSync(dest,{recursive:true});
const sources={baseline:'../reference/anyangle1409-code-animation-software-f9cca7c/HOME_GYM_PT_GPT_MESH_HANDOFF/characters/HomeGymPT_Male_CORNER_FINAL_SHORTS.glb',candidate:'../HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v1.glb'};
it('compares all five exercises with frozen rig, correctives and actual equipment frames',async()=>{
 const report:any={sources:{},exercises:[]};const builds:any={};
 for(const [id,path]of Object.entries(sources)){const b=readFileSync(path);const s=retargetedCharacterSource({id,label:id,data:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength)});builds[id]=await s.build(rig);report.sources[id]=s.lastReport;}
 expect(report.sources.candidate.height).toBeCloseTo(report.sources.baseline.height,7);
 for(const ex of EXERCISES){const clip=generateClip(rig,ex),ev=new PoseEvaluation(rig),anchors=lockAnchors(ev,sampleClip(clip,0).pose,clip.locks);const validation=validateClip(rig,new PoseEvaluation(rig),ex,clip);const peak=clip.keyframes.find(m=>m.marker==='peak')?.time??clip.duration*.4;
 const frames=[['bottom',0],['mid',peak*.5],['peak',peak],['return',clip.duration]] as [string,number][];let maxHand=0,maxBones=0,maxEquipment=0;const start:any={};
 for(const [label,t] of frames){const f=resolveFrame(rig,ev,clip,t,{anchors});const pair:any={};for(const [id,c]of Object.entries(builds) as any){applyCharacterPose(c,rig,f.pose,ev,{contacts:f.contacts,grip:{kind:ex.hands.grip,closure:ex.hands.closure}});
 const body=c.meshes.find((m:any)=>/freeman/i.test(m.name));const meshes=[];const p=new Vector3();
 for(const m of c.meshes){m.skeleton.update();m.updateWorldMatrix(true,false);const positions=[];for(let i=0;i<m.geometry.getAttribute('position').count;i++){m.getVertexPosition(i,p);p.applyMatrix4(m.matrixWorld);positions.push(p.toArray());expect(p.toArray().every(Number.isFinite)).toBe(true);}meshes.push({name:m.name,positions,indices:Array.from(m.geometry.index.array)});}
 const bones=c.bones.map((b:any)=>b.matrixWorld.toArray());const equipment=[];
 for(const instance of clip.equipment){let matrix=f.equipment.get(instance.id)?.matrix?.clone();if(instance.attachment.mode==='hand'){const side=instance.attachment.side;const hand=c.handMatrix?.(side,new Matrix4());if(hand){const socket=equipmentSocketForInstance(instance,instance.attachment.socket);matrix=hand.clone().multiply(handAttachmentMatrix(instance.attachment.gripOffset??c.gripOffset?.(side)??anatomicalGripOffset(side),socket?.position??{x:0,y:0,z:0},{gripRotation:instance.attachment.gripRotation,socketRotation:socket?.rotation}));}}if(matrix)equipment.push({kind:instance.kind,matrix:matrix.toArray(),parts:EQUIPMENT_PARTS[instance.kind]});}
 const hands=[];const si=body.geometry.getAttribute('skinIndex'),sw=body.geometry.getAttribute('skinWeight');for(let i=0;i<10839;i++){let w=0;for(let lane=0;lane<4;lane++)if(/hand|palm|f_|thumb/.test(body.skeleton.bones[si.getComponent(i,lane)].name))w+=sw.getComponent(i,lane);if(w>.001)hands.push(meshes[0].positions[i]);}
 pair[id]={bones,hands,equipment,meshes};if(label==='bottom')start[id]=meshes.map(m=>m.positions);
 if(label==='return'){let loop=0;meshes.forEach((m,mi)=>m.positions.forEach((p,i)=>loop=Math.max(loop,new Vector3(...p).distanceTo(new Vector3(...start[id][mi][i])))));expect(loop).toBeLessThan(1e-6);}
 writeFileSync(`${dest}/${ex.id}_${label}_${id}.json`,JSON.stringify({exercise:ex.name,label,time:t,meshes,equipment}));
 }
 const a=pair.baseline,b=pair.candidate;expect(b.hands.length).toBe(a.hands.length);a.hands.forEach((p:any,i:number)=>maxHand=Math.max(maxHand,new Vector3(...p).distanceTo(new Vector3(...b.hands[i]))));a.bones.forEach((m:any,i:number)=>m.forEach((v:number,k:number)=>maxBones=Math.max(maxBones,Math.abs(v-b.bones[i][k]))));a.equipment.forEach((m:any,i:number)=>m.matrix.forEach((v:number,k:number)=>maxEquipment=Math.max(maxEquipment,Math.abs(v-b.equipment[i].matrix[k]))));
 }
 report.exercises.push({name:ex.name,frames:frames.length,handMaxDifferenceMm:maxHand*1000,boneMatrixMaxDifference:maxBones,equipmentMatrixMaxDifference:maxEquipment,techniqueViolations:validation.violations.map(v=>v.ruleId),unreachable:validation.unreachable,loopClosed:validation.loopClosed});expect(maxBones).toBeLessThan(1e-6);expect(maxHand).toBeLessThan(1e-6);expect(maxEquipment).toBeLessThan(1e-6);
 }
 writeFileSync('../reports/exercise_validation.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report.exercises));Object.values(builds).forEach((c:any)=>c.dispose());
},900000);

