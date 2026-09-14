from pathlib import Path


def replace(path, old, new):
    p = Path(path)
    text = p.read_text()
    if old not in text:
        raise SystemExit(f"missing anchor in {path}: {old[:110]!r}")
    p.write_text(text.replace(old, new, 1))

# Review workspace: consolidate existing descriptive movement diagnostics into
# one place without turning them into new approval thresholds.
p = Path("src/editor/panels/ReviewPanel.tsx")
text = p.read_text()
text = text.replace(
    "import { useCharacter } from '../characterStore';",
    "import { useCharacter } from '../characterStore';\nimport { boneLabel, type BoneName } from '../../rig/boneNames';\nimport {\n  measureBilateralMotionSymmetry,\n  measureJointMotion,\n  measureJointPath,\n  measureJointTransitions,\n} from '../motionDiagnostics';",
    1,
)
text = text.replace(
    "  const clearVisualReview = useStudio((state) => state.clearVisualReview);",
    "  const clearVisualReview = useStudio((state) => state.clearVisualReview);\n  const selectedBone = useStudio((state) => state.selection.bone);\n  const selectBone = useStudio((state) => state.selectBone);\n  const setCamera = useStudio((state) => state.setCamera);\n  const setTime = useStudio((state) => state.setTime);",
    1,
)
text = text.replace(
    "  const approved = review.automatedPass && visualPassed;",
    "  const approved = review.automatedPass && visualPassed;\n  const reviewBone: BoneName | null =\n    selectedBone ?? (document.exercise.id === 'dumbbell_bicep_curl' ? 'forearm_l' : null);\n  const movement = useMemo(() => {\n    if (!reviewBone) return null;\n    return {\n      bone: reviewBone,\n      motion: measureJointMotion(document.clip, reviewBone),\n      transitions: measureJointTransitions(document.clip, reviewBone),\n      bilateral: measureBilateralMotionSymmetry(document.clip, skeleton, reviewBone),\n      path: measureJointPath(document.clip, skeleton, reviewBone),\n    };\n  }, [document.clip, reviewBone]);",
    1,
)
anchor = """      <h3>Visual sign-off</h3>\n"""
section = r'''      <h3>Movement review</h3>
      {movement ? (
        <div className="joint-motion-diagnostic">
          <p className="panel__hint">
            Reviewing <strong>{boneLabel(movement.bone)}</strong>
            {!selectedBone && document.exercise.id === 'dumbbell_bicep_curl'
              ? ' — default elbow review joint for the dumbbell curl.'
              : '.'}{' '}
            These values locate frames for visual inspection; they do not add automatic approval thresholds.
          </p>
          <dl className="spec-list">
            <dt>Highest angular speed</dt>
            <dd>{movement.motion.maxSpeed.value.toFixed(1)}°/s · {movement.motion.maxSpeed.time.toFixed(2)}s</dd>
            <dt>Highest angular acceleration</dt>
            <dd>{movement.motion.maxAcceleration.value.toFixed(0)}°/s² · {movement.motion.maxAcceleration.time.toFixed(2)}s</dd>
            <dt>Largest keyframe velocity jump</dt>
            <dd>{movement.transitions.maxJump ? `${movement.transitions.maxJump.velocityJumpDegPerSec.toFixed(1)}°/s · ${movement.transitions.maxJump.time.toFixed(2)}s` : '—'}</dd>
            {movement.bilateral && (
              <>
                <dt>Bilateral mirror mismatch</dt>
                <dd>{movement.bilateral.maxError.value.toFixed(2)}° max · {movement.bilateral.rmsErrorDeg.toFixed(2)}° RMS · {movement.bilateral.maxError.time.toFixed(2)}s</dd>
              </>
            )}
            {movement.path && (
              <>
                <dt>Joint drift from parent</dt>
                <dd>{(movement.path.maxDriftMetres * 1000).toFixed(1)} mm · {movement.path.maxDriftTime.toFixed(2)}s</dd>
                <dt>Return error</dt>
                <dd>{(movement.path.returnErrorMetres * 1000).toFixed(1)} mm</dd>
              </>
            )}
          </dl>
          <div className="button-row">
            <button
              type="button"
              onClick={() => {
                selectBone(movement.bone);
                setCamera('focus');
              }}
            >
              Focus review joint
            </button>
            <button type="button" onClick={() => setTime(movement.motion.maxAcceleration.time)}>
              Sharpest change
            </button>
            {movement.transitions.maxJump && (
              <button type="button" onClick={() => setTime(movement.transitions.maxJump!.time)}>
                Worst transition
              </button>
            )}
            {movement.bilateral && (
              <button type="button" onClick={() => setTime(movement.bilateral!.maxError.time)}>
                Worst bilateral mismatch
              </button>
            )}
            {movement.path && (
              <button type="button" onClick={() => setTime(movement.path!.maxDriftTime)}>
                Maximum joint drift
              </button>
            )}
          </div>
        </div>
      ) : (
        <p className="panel__empty">
          Select a joint in the viewport or Joint workspace to add movement diagnostics to this review.
        </p>
      )}

'''
if anchor not in text:
    raise SystemExit("missing ReviewPanel visual sign-off anchor")
text = text.replace(anchor, section + anchor, 1)
p.write_text(text)

# Retained curl regression: the summary signals needed for elbow review remain
# finite and the authored bilateral path stays mirrored.
p = Path("src/editor/review.test.ts")
text = p.read_text()
text = text.replace(
    "import { reviewExercise } from './review';",
    "import { reviewExercise } from './review';\nimport {\n  measureBilateralMotionSymmetry,\n  measureJointMotion,\n  measureJointPath,\n  measureJointTransitions,\n} from './motionDiagnostics';",
    1,
)
addition = r'''

  it('keeps the retained curl measurable for one-place elbow movement review', () => {
    const exercise = getExercise('dumbbell_bicep_curl');
    const clip = generateClip(canonicalSkeleton, exercise);
    const motion = measureJointMotion(clip, 'forearm_l');
    const transitions = measureJointTransitions(clip, 'forearm_l');
    const bilateral = measureBilateralMotionSymmetry(clip, canonicalSkeleton, 'forearm_l');
    const path = measureJointPath(clip, canonicalSkeleton, 'forearm_l');

    expect(motion.maxSpeed.value).toBeGreaterThan(0);
    expect(Number.isFinite(motion.maxAcceleration.value)).toBe(true);
    expect(transitions.maxJump).not.toBeNull();
    expect(bilateral).not.toBeNull();
    expect(bilateral!.maxError.value).toBeLessThan(1e-6);
    expect(path).not.toBeNull();
    expect(path!.parent).toBe('upperarm_l');
    expect(path!.maxDriftMetres).toBeGreaterThan(0);
    expect(path!.returnErrorMetres).toBeLessThan(1e-6);
  });
'''
pos = text.rfind("\n});")
if pos < 0:
    raise SystemExit("missing review test suite end")
text = text[:pos] + addition + text[pos:]
p.write_text(text)

replace(
    "docs/STUDIO_CAPABILITY_ROADMAP.md",
    "- Selected-joint spatial path diagnostics track the joint head relative to its anatomical parent, reporting maximum drift, total relative path length, return error and the worst timestamp. For a selected forearm this directly measures elbow wander relative to the shoulder while removing whole-body/root translation.",
    "- Selected-joint spatial path diagnostics track the joint head relative to its anatomical parent, reporting maximum drift, total relative path length, return error and the worst timestamp. For a selected forearm this directly measures elbow wander relative to the shoulder while removing whole-body/root translation.\n- Review now consolidates selected-joint speed, acceleration, keyframe continuity, bilateral mismatch and spatial drift with direct jump/focus actions. Dumbbell Bicep Curl defaults to the left forearm/elbow when no joint is selected, while descriptive movement metrics remain outside the automated approval gate.",
)

p = Path("AI_CHANGELOG.md")
text = p.read_text()
entry = r'''
### ChatGPT — 2026-09-14 — consolidated movement review summary

The Review workspace now brings the selected joint's existing movement diagnostics together beside the automated gates and human sign-off: maximum angular speed/acceleration, worst keyframe velocity discontinuity, resolved bilateral mirror mismatch, spatial joint drift and return error. Every measured problem point has a direct navigation action, and `Focus review joint` selects the joint and enters the close Focus camera.

For Dumbbell Bicep Curl, Review defaults to `forearm_l` when no joint is already selected, making the elbow review immediately useful without changing selection state until the author explicitly focuses it. Selecting another joint anywhere in the Studio takes over the Review summary. These movement signals remain descriptive navigation aids and do not silently add new automated approval thresholds.

Regression coverage now exercises the retained curl through the same summary ingredients and proves its forearm motion is finite, has an inspectable interior transition, remains bilaterally mirrored, moves the elbow through the small authored upper-arm contribution and returns the elbow to its starting relative position by the end of the rep.

'''
marker = "## Unreleased\n\n"
if marker not in text:
    raise SystemExit("missing changelog marker")
text = text.replace(marker, marker + entry, 1)
p.write_text(text)

print("Applied consolidated movement review summary")
