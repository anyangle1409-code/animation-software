import type { StudioClip } from '../animation/clip';
import { resolveFrame } from '../animation/pipeline';
import type { HgFrame } from '../core/frameLoop';
import { advancePlaybackTime } from '../editor/playback';
import type { LoopRange } from '../editor/playback';
import type { Skeleton } from '../rig/skeleton';
import type { Vec3 } from '../rig/types';
import type { SceneState } from './sceneStateCore';

export interface ScenePlaybackPort {
  time: number;
  playing: boolean;
  loop: boolean;
  speed: number;
  loopRange: LoopRange | null;
  setTime(time: number): void;
  pause(): void;
}

export interface DriveSceneFrameInput {
  scene: SceneState;
  skeleton: Skeleton;
  clip: StudioClip;
  anchors?: Map<string, Vec3>;
  playback: ScenePlaybackPort;
  frame: HgFrame;
}

/**
 * Resolve one Studio animation frame independently of the renderer/host.
 *
 * The host supplies timing. This function owns the ordering that used to live
 * inside R3F's useFrame callback:
 *   playback -> resolve -> evaluation -> visual-consumer dispatch.
 */
export function driveSceneFrame({
  scene,
  skeleton,
  clip,
  anchors,
  playback,
  frame,
}: DriveSceneFrameInput) {
  let time = playback.time;

  if (playback.playing) {
    const advanced = advancePlaybackTime(
      time,
      Math.min(Math.max(frame.delta, 0), 0.1) * playback.speed,
      clip.duration,
      playback.loop,
      playback.loopRange,
    );
    time = advanced.time;
    if (advanced.ended) playback.pause();
    playback.setTime(time);
  }

  scene.frame = resolveFrame(skeleton, scene.evaluation, clip, time, { anchors });
  scene.evaluation.apply(scene.frame.pose);
  scene.consumers.dispatch(frame);
  return scene.frame;
}
