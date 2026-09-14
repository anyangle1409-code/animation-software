from pathlib import Path

# 1) Camera type: add a diagnostic focus mode to the existing dropdown.
path = Path('src/viewer/cameraTypes.ts')
text = path.read_text(encoding='utf-8')
old = "  'top',\n  'free',\n  'recommended',"
new = "  'top',\n  'focus',\n  'free',\n  'recommended',"
if old not in text:
    raise SystemExit('camera type anchor not found')
path.write_text(text.replace(old, new, 1), encoding='utf-8')

# 2) Camera resolver: focus is dynamic and therefore has no static setup.
path = Path('src/viewer/cameras.ts')
text = path.read_text(encoding='utf-8')
text = text.replace(
    "export const CAMERA_PRESETS: Record<Exclude<CameraPresetId, 'recommended' | 'free'>, CameraSetup> = {",
    "export const CAMERA_PRESETS: Record<Exclude<CameraPresetId, 'recommended' | 'free' | 'focus'>, CameraSetup> = {",
    1,
)
old = "  top: 'Top',\n  free: 'Free orbit',"
new = "  top: 'Top',\n  focus: 'Focus selected',\n  free: 'Free orbit',"
if old not in text:
    raise SystemExit('camera labels anchor not found')
text = text.replace(old, new, 1)
old = "  if (preset === 'free') return null;\n  if (preset === 'recommended') {"
new = "  if (preset === 'free' || preset === 'focus') return null;\n  if (preset === 'recommended') {"
if old not in text:
    raise SystemExit('camera resolver anchor not found')
path.write_text(text.replace(old, new, 1), encoding='utf-8')

# 3) Viewport: Focus selected follows the resolved joint after FrameDriver has
# evaluated the current frame. This affects only camera position/target/FOV and
# reuses scratch vectors so playback creates no per-frame garbage.
path = Path('src/viewer/Viewport.tsx')
text = path.read_text(encoding='utf-8')
old = "function CameraRig({ controls }: { controls: React.RefObject<OrbitControlsImpl | null> }) {\n  const preset = useStudio((state) => state.camera);\n  const recommendation = useStudio((state) => state.document.exercise.camera);\n  const { camera } = useThree();\n  const goal = useRef<{ position: Vector3; target: Vector3; fov: number } | null>(null);"
new = "function CameraRig({ controls }: { controls: React.RefObject<OrbitControlsImpl | null> }) {\n  const scene = useSceneState();\n  const preset = useStudio((state) => state.camera);\n  const recommendation = useStudio((state) => state.document.exercise.camera);\n  const selectedBone = useStudio((state) => state.selection.bone);\n  const { camera } = useThree();\n  const goal = useRef<{ position: Vector3; target: Vector3; fov: number } | null>(null);\n  const focusTarget = useRef(new Vector3());\n  const focusPosition = useRef(new Vector3());\n  const focusOffset = useRef(new Vector3());"
if old not in text:
    raise SystemExit('CameraRig declaration anchor not found')
text = text.replace(old, new, 1)
old = "  useFrame((_, delta) => {\n    const destination = goal.current;\n    if (!destination || !controls.current) return;\n    const blend = Math.min(1, delta * 6);"
new = "  useFrame((_, delta) => {\n    if (preset === 'focus' && selectedBone && controls.current) {\n      scene.evaluation.head(selectedBone, focusTarget.current);\n      const side = selectedBone.endsWith('_l') ? -1 : selectedBone.endsWith('_r') ? 1 : 1;\n      focusOffset.current.set(side * 0.58, 0.20, 0.78);\n      focusPosition.current.copy(focusTarget.current).add(focusOffset.current);\n      const blend = Math.min(1, delta * 7);\n      camera.position.lerp(focusPosition.current, blend);\n      controls.current.target.lerp(focusTarget.current, blend);\n      if ('fov' in camera) {\n        camera.fov += (32 - camera.fov) * blend;\n        camera.updateProjectionMatrix();\n      }\n      controls.current.update();\n      return;\n    }\n\n    const destination = goal.current;\n    if (!destination || !controls.current) return;\n    const blend = Math.min(1, delta * 6);"
if old not in text:
    raise SystemExit('CameraRig frame anchor not found')
path.write_text(text.replace(old, new, 1), encoding='utf-8')

# 4) Camera regression tests keep the dynamic focus mode out of the static
# resolver and make sure it remains discoverable in the UI labels/IDs.
Path('src/viewer/cameras.test.ts').write_text("""import { describe, expect, it } from 'vitest';
import { CAMERA_LABELS, resolveCamera } from './cameras';
import { CAMERA_PRESET_IDS } from './cameraTypes';

const recommendation = { preset: 'three_quarter' as const };

describe('diagnostic camera modes', () => {
  it('exposes Focus selected as a camera choice', () => {
    expect(CAMERA_PRESET_IDS).toContain('focus');
    expect(CAMERA_LABELS.focus).toBe('Focus selected');
  });

  it('keeps focus out of the static camera resolver because it follows the live joint', () => {
    expect(resolveCamera('focus', recommendation)).toBeNull();
  });

  it('leaves the existing recommended framing unchanged', () => {
    const camera = resolveCamera('recommended', recommendation);
    expect(camera).not.toBeNull();
    expect(camera?.fov).toBe(38);
  });
});
""", encoding='utf-8')
