/** First-party sampled-pose playback, not an animation interpolator.
 * Holds the last authored sample between timestamps. No fabricated motion,
 * background continuation or production authorization. One RAF at a time.
 */
import {getBoundDiagnosticExerciseFrame} from '../exercise/firstPartyExercisePoseBinding.mjs';
export function createDiagnosticExercisePlayback(binding,{
  draw,requestFrame=cb=>globalThis.requestAnimationFrame(cb),
  cancelFrame=id=>globalThis.cancelAnimationFrame(id),
}={}){
  // Authenticate the opaque binding before inspecting public metadata.
  getBoundDiagnosticExerciseFrame(binding,0);
  if(typeof draw!=='function'||typeof requestFrame!=='function'||typeof cancelFrame!=='function')
    throw new TypeError('Playback requires draw and frame scheduler');
  const duration=binding.durationSeconds;
  const times=Array.from({length:binding.frameCount},(_,i)=>
    getBoundDiagnosticExerciseFrame(binding,i).timeSeconds);
  let status='paused',time=0,pending=null,generation=0,origin=null,lastClock=null,lastIndex=-1;
  const usable=()=>{if(status==='disposed')throw Error('Playback disposed');};
  const cancel=()=>{generation++;if(pending!==null)cancelFrame(pending);pending=null;origin=null;lastClock=null;};
  const select=()=>{
    let lo=0,hi=times.length-1;
    while(lo<hi){const mid=Math.ceil((lo+hi)/2);if(times[mid]<=time)lo=mid;else hi=mid-1;}
    return lo;
  };
  const render=force=>{
    const index=select();if(!force&&index===lastIndex)return;
    lastIndex=index;
    try{draw(getBoundDiagnosticExerciseFrame(binding,index),index);}
    catch(e){if(status!=='disposed'){status='paused';cancel();}throw e;}
  };
  const schedule=()=>{
    if(status!=='playing'||pending!==null)return;
    const current=generation;
    try{pending=requestFrame(timestamp=>{
      if(current!==generation||status!=='playing')return;
      pending=null;
      if(!Number.isFinite(timestamp)||(lastClock!==null&&timestamp<lastClock)){
        status='paused';cancel();throw new RangeError('Playback clock must be finite and monotonic');
      }
      if(origin===null)origin=timestamp-time*1000;
      lastClock=timestamp;time=Math.min(duration,(timestamp-origin)/1000);
      render(false);
      if(status!=='playing')return;
      if(time>=duration){status='completed';cancel();}else schedule();
    });}catch(e){if(status!=='disposed'){status='paused';cancel();}throw e;}
  };
  return Object.freeze({
    play(){usable();if(status==='playing')return;
      if(status==='completed')time=0;
      cancel();status='playing';render(false);schedule();},
    pause(){usable();if(status==='playing'){status='paused';cancel();}},
    seek(seconds){usable();if(!Number.isFinite(seconds)||seconds<0||seconds>duration)
      throw new RangeError('Playback seek time must lie within authored duration');
      cancel();time=seconds;render(true);schedule();},
    dispose(){if(status==='disposed')return;status='disposed';cancel();},
    state:()=>Object.freeze({status,timeSeconds:time,durationSeconds:duration,
      interpolationPerformed:false,productionApproved:false}),
  });
}
