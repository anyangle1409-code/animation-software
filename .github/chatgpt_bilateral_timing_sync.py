from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text()


def write(path: str, text: str) -> None:
    Path(path).write_text(text)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'missing replacement target: {label}')
    return text.replace(old, new, 1)


p = 'src/editor/store.ts'
s = read(p)
s = replace_once(
    s,
    "import type { BoneName, Finger } from '../rig/boneNames';\n",
    "import type { BoneName, Finger } from '../rig/boneNames';\nimport { mirrorBoneName } from '../rig/boneNames';\n",
    'store mirrorBoneName import',
)
s = replace_once(
    s,
    "  setJointTiming: (id: string, bone: BoneName, timing: PhaseJointTiming | null) => void;\n",
    "  setJointTiming: (id: string, bone: BoneName, timing: PhaseJointTiming | null) => void;\n  copyJointTimingToOpposite: (id: string, bone: BoneName) => void;\n",
    'store action type',
)
s = replace_once(
    s,
    "    setJointTiming: (id, bone, timing) =>\n      editClip((clip) => ({\n        ...clip,\n        keyframes: clip.keyframes.map((frame) => {\n          if (frame.id !== id) return frame;\n          const jointTiming: Partial<Record<BoneName, PhaseJointTiming>> = {\n            ...(frame.jointTiming ?? {}),\n          };\n          if (!timing) delete jointTiming[bone];\n          else {\n            const delay = Math.max(0, Math.min(1, timing.delay ?? 0));\n            const finish = Math.max(delay, Math.max(0, Math.min(1, timing.finish ?? 1)));\n            jointTiming[bone] = {\n              delay,\n              finish,\n              ...(timing.easing ? { easing: timing.easing } : {}),\n            };\n          }\n          return {\n            ...frame,\n            jointTiming: Object.keys(jointTiming).length > 0 ? jointTiming : undefined,\n          };\n        }),\n      })),\n\n",
    "    setJointTiming: (id, bone, timing) =>\n      editClip((clip) => ({\n        ...clip,\n        keyframes: clip.keyframes.map((frame) => {\n          if (frame.id !== id) return frame;\n          const jointTiming: Partial<Record<BoneName, PhaseJointTiming>> = {\n            ...(frame.jointTiming ?? {}),\n          };\n          if (!timing) delete jointTiming[bone];\n          else {\n            const delay = Math.max(0, Math.min(1, timing.delay ?? 0));\n            const finish = Math.max(delay, Math.max(0, Math.min(1, timing.finish ?? 1)));\n            jointTiming[bone] = {\n              delay,\n              finish,\n              ...(timing.easing ? { easing: timing.easing } : {}),\n            };\n          }\n          return {\n            ...frame,\n            jointTiming: Object.keys(jointTiming).length > 0 ? jointTiming : undefined,\n          };\n        }),\n      })),\n\n    copyJointTimingToOpposite: (id, bone) => {\n      const opposite = mirrorBoneName(bone);\n      if (opposite === bone) return;\n      editClip((clip) => ({\n        ...clip,\n        keyframes: clip.keyframes.map((frame) => {\n          if (frame.id !== id) return frame;\n          const source = frame.jointTiming?.[bone];\n          const jointTiming: Partial<Record<BoneName, PhaseJointTiming>> = {\n            ...(frame.jointTiming ?? {}),\n          };\n          if (source) jointTiming[opposite] = { ...source };\n          else delete jointTiming[opposite];\n          return {\n            ...frame,\n            jointTiming: Object.keys(jointTiming).length > 0 ? jointTiming : undefined,\n          };\n        }),\n      }));\n    },\n\n",
    'store action implementation',
)
write(p, s)

p = 'src/editor/store.test.ts'
s = read(p)
s = replace_once(
    s,
    "  it('normalises invalid joint timing rather than creating an impossible segment', () => {\n",
    "  it('copies selected joint timing to the anatomical opposite through one undoable edit', () => {\n    const first = useStudio.getState().document.clip.keyframes[0];\n    useStudio.getState().setJointTiming(first.id, 'upperarm_l', {\n      delay: 0.31,\n      finish: 0.88,\n      easing: 'minimumJerk',\n    });\n    const beforeCopy = useStudio.getState().document.clip.keyframes.find((frame) => frame.id === first.id)!\n      .jointTiming?.upperarm_r;\n\n    useStudio.getState().copyJointTimingToOpposite(first.id, 'upperarm_l');\n    const after = useStudio.getState().document.clip.keyframes.find((frame) => frame.id === first.id)!;\n    expect(after.jointTiming?.upperarm_r).toEqual(after.jointTiming?.upperarm_l);\n\n    useStudio.getState().undo();\n    expect(\n      useStudio.getState().document.clip.keyframes.find((frame) => frame.id === first.id)?.jointTiming\n        ?.upperarm_r,\n    ).toEqual(beforeCopy);\n  });\n\n  it('clears opposite custom timing when the selected side uses phase-default timing', () => {\n    const first = useStudio.getState().document.clip.keyframes[0];\n    useStudio.getState().setJointTiming(first.id, 'hand_r', { delay: 0.4, finish: 0.9 });\n    expect(\n      useStudio.getState().document.clip.keyframes.find((frame) => frame.id === first.id)?.jointTiming\n        ?.hand_r,\n    ).toBeDefined();\n    useStudio.getState().copyJointTimingToOpposite(first.id, 'hand_l');\n    expect(\n      useStudio.getState().document.clip.keyframes.find((frame) => frame.id === first.id)?.jointTiming\n        ?.hand_r,\n    ).toBeUndefined();\n  });\n\n  it('normalises invalid joint timing rather than creating an impossible segment', () => {\n",
    'store timing tests',
)
write(p, s)

p = 'src/editor/panels/JointPanel.tsx'
s = read(p)
s = replace_once(
    s,
    "import { boneLabel, isFingerBone } from '../../rig/boneNames';\n",
    "import { boneLabel, isFingerBone, mirrorBoneName } from '../../rig/boneNames';\n",
    'JointPanel opposite import',
)
s = replace_once(
    s,
    "  const setJointTiming = useStudio((state) => state.setJointTiming);\n",
    "  const setJointTiming = useStudio((state) => state.setJointTiming);\n  const copyJointTimingToOpposite = useStudio((state) => state.copyJointTimingToOpposite);\n",
    'JointPanel copy action',
)
s = replace_once(
    s,
    "  const timing = selected && segmentFrom ? segmentFrom.jointTiming?.[selected] : undefined;\n",
    "  const timing = selected && segmentFrom ? segmentFrom.jointTiming?.[selected] : undefined;\n  const oppositeBone = selected ? mirrorBoneName(selected) : null;\n  const oppositeTiming = oppositeBone && oppositeBone !== selected && segmentFrom\n    ? segmentFrom.jointTiming?.[oppositeBone]\n    : undefined;\n  const timingMatchesOpposite = Boolean(\n    oppositeBone && oppositeBone !== selected &&\n    (timing?.delay ?? 0) === (oppositeTiming?.delay ?? 0) &&\n    (timing?.finish ?? 1) === (oppositeTiming?.finish ?? 1) &&\n    (timing?.easing ?? '') === (oppositeTiming?.easing ?? ''),\n  );\n",
    'JointPanel timing symmetry state',
)
s = replace_once(
    s,
    "              <p className=\"panel__note\">\n                Use this for sequencing secondary joints—such as allowing the elbow to lead before\n                the shoulder joins a curl—without inserting stop/start keyframes.\n              </p>\n",
    "              <p className=\"panel__note\">\n                Use this for sequencing secondary joints—such as allowing the elbow to lead before\n                the shoulder joins a curl—without inserting stop/start keyframes.\n              </p>\n",
    'JointPanel keep timing note',
)
s = replace_once(
    s,
    "          )}\n        </div>\n      ) : (\n",
    "          )}\n          {oppositeBone && oppositeBone !== selected && (\n            <div className=\"joint-timing-symmetry\">\n              <h4>Left/right timing</h4>\n              <p className=\"panel__hint\">\n                Opposite joint: <strong>{boneLabel(oppositeBone)}</strong> ·{' '}\n                <span className={timingMatchesOpposite ? 'status-ok' : 'status-warn'}>\n                  {timingMatchesOpposite ? 'Timing matched' : 'Timing differs'}\n                </span>\n              </p>\n              <button\n                type=\"button\"\n                disabled={timingMatchesOpposite}\n                onClick={() => copyJointTimingToOpposite(segmentFrom.id, selected)}\n              >\n                Copy selected timing to opposite side\n              </button>\n              <p className=\"panel__note\">\n                Copies delay, finish and easing only. Pose angles stay untouched, and the edit uses\n                normal undo/redo history. If this side uses phase-default timing, the opposite side\n                is reset to the same default.\n              </p>\n            </div>\n          )}\n        </div>\n      ) : (\n",
    'JointPanel symmetry UI',
)
write(p, s)

p = 'docs/STUDIO_CAPABILITY_ROADMAP.md'
s = read(p)
s = replace_once(
    s,
    '- Segment-local joint coordination compares the selected joint against its anatomical parent, reporting excursion, meaningful-motion onset and onset lag; the parent can be selected directly for timing edits, making elbow-led/shoulder-follow sequencing explicit without extra stop/start keys.\n',
    '- Segment-local joint coordination compares the selected joint against its anatomical parent, reporting excursion, meaningful-motion onset and onset lag; the parent can be selected directly for timing edits, making elbow-led/shoulder-follow sequencing explicit without extra stop/start keys.\n- Bilateral timing symmetry is explicit: the Joint workspace compares delay/finish/easing against the anatomical opposite and can copy selected-side timing to the other side in one undoable edit without changing pose angles.\n',
    'roadmap timing symmetry',
)
write(p, s)

p = 'AI_CHANGELOG.md'
s = read(p)
entry = '''### ChatGPT — 2026-09-14 — explicit bilateral joint-timing symmetry\n\nAdded `copyJointTimingToOpposite()` to the Studio store. It uses the canonical anatomical mirror bone, copies the selected segment's explicit delay/finish/easing to the opposite side in one normal undoable document edit, and copies **timing only**—pose rotations and IK remain untouched. If the selected side has no explicit joint timing, copying clears the opposite override so both sides use the same phase-default timing. Centre-line bones are a no-op.\n\nThe Joint workspace now compares the selected joint's effective delay/finish/easing with its left/right counterpart and displays `Timing matched` or `Timing differs`, plus a `Copy selected timing to opposite side` action when needed. This closes a real authoring gap: pose mirroring alone never guaranteed bilateral motion timing. Regression coverage verifies a custom left upper-arm timing copies exactly to the right and undo restores the prior right-side timing, and verifies copying a default-timed left hand clears a stale right-hand override.\n\n\n'''
s = replace_once(s, '## Unreleased\n\n', '## Unreleased\n\n\n' + entry, 'changelog insertion')
write(p, s)

print('Applied explicit bilateral joint-timing symmetry')
