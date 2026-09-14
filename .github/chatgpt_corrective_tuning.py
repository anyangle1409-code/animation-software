from pathlib import Path


def replace(path, old, new):
    p = Path(path)
    text = p.read_text()
    if old not in text:
        raise SystemExit(f"missing anchor in {path}: {old[:80]!r}")
    p.write_text(text.replace(old, new, 1))

# Character deformation controls are character/source state, not exercise state.
replace(
    "src/character/types.ts",
    "export interface DeformationStack {\n  /** Called each frame, after the bone matrices have been written. */\n  update(context: DeformationContext): void;",
    "export interface DeformationControl {\n  /** Stable id for authoring UI and tests. */\n  id: string;\n  label: string;\n  min: number;\n  max: number;\n  step: number;\n  /** Value authored in the character source before interactive review. */\n  defaultValue: number;\n  /** Current source-level value; export reads the same backing state. */\n  readonly value: number;\n  note?: string;\n  set(value: number): void;\n}\n\nexport interface DeformationStack {\n  /** Called each frame, after the bone matrices have been written. */\n  update(context: DeformationContext): void;\n  /** Character-specific authoring controls shared with the export sampler. */\n  controls?: readonly DeformationControl[];",
)
replace(
    "src/character/index.ts",
    "  DeformationContext,\n  DeformationSampler,\n  DeformationStack,",
    "  DeformationContext,\n  DeformationControl,\n  DeformationSampler,\n  DeformationStack,",
)

# Imported elbow: preserve the existing radial target, but make the directional
# outer settling its own morph when a runtime tuning object is supplied. This
# lets the v5 source remain at 0 and the review candidate reach 1 without baking
# one into the other or exceeding the existing 8 mm authored target cap.
p = Path("src/character/importedDeformation.ts")
text = p.read_text()
text = text.replace(
    "import type { DeformationSampler, DeformationStack } from './types';",
    "import type { DeformationControl, DeformationSampler, DeformationStack } from './types';",
    1,
)
start = text.index("interface Target {")
end = text.index("function elbowPairWeights(")
new_block = r'''export interface ImportedElbowRuntimeTuning {
  /** 0 = retained radial corrective only; 1 = full measured outer-smoothing candidate. */
  outerSmooth: number;
  /** Source-authored value used by Reset in the editor. */
  defaultOuterSmooth: number;
}

interface Target {
  mesh: SkinnedMesh;
  side: Side;
  influence: number;
  name: string;
  scale: () => number;
}

const clampOuterSmooth = (value: number): number => Math.min(1, Math.max(0, value));

/** Build opt-in pose shapes for an imported mesh's own elbow topology. */
export function importedElbowDeformation(
  meshes: SkinnedMesh[],
  boneByName: Map<BoneName, Bone>,
  rig: Skeleton,
  options?: ImportedElbowCorrectiveOptions,
  tuning?: ImportedElbowRuntimeTuning,
): DeformationStack | null {
  if (!options?.enabled) return null;
  const targets: Target[] = [];
  let hasTunableOuter = false;
  for (const mesh of meshes) {
    for (const side of ['l', 'r'] as const) {
      const built = appendTargets(mesh, boneByName, side, options, tuning);
      targets.push(...built.targets);
      hasTunableOuter ||= built.hasTunableOuter;
    }
  }
  if (!targets.length) return null;

  const controls: DeformationControl[] | undefined = tuning && hasTunableOuter
    ? [{
        id: 'elbowOuterSmooth',
        label: 'Outer elbow smoothing',
        min: 0,
        max: 1,
        step: 0.05,
        defaultValue: clampOuterSmooth(tuning.defaultOuterSmooth),
        get value() {
          return clampOuterSmooth(tuning.outerSmooth);
        },
        set(value: number) {
          tuning.outerSmooth = clampOuterSmooth(value);
        },
        note: '0% preserves the retained radial corrective; 100% is the measured directional outer-elbow candidate. The morph itself remains capped at 8 mm.',
      }]
    : undefined;

  return {
    controls,
    update({ evaluation }) {
      for (const target of targets) {
        if (target.mesh.morphTargetInfluences) {
          target.mesh.morphTargetInfluences[target.influence] =
            elbowFlexion(evaluation, target.side) * target.scale();
        }
      }
    },
    sampler: () => correctiveSampler(targets, rig),
  };
}

function appendTargets(
  mesh: SkinnedMesh,
  boneByName: Map<BoneName, Bone>,
  side: Side,
  options: ImportedElbowCorrectiveOptions,
  tuning?: ImportedElbowRuntimeTuning,
): { targets: Target[]; hasTunableOuter: boolean } {
  const upper = boneByName.get(`upperarm_${side}` as BoneName);
  const lower = boneByName.get(`forearm_${side}` as BoneName);
  if (!upper || !lower) return { targets: [], hasTunableOuter: false };
  const upperIndices = matchingBones(mesh, upper.name, options.includeSplitHelpers);
  const lowerIndices = matchingBones(mesh, lower.name, options.includeSplitHelpers);
  if (!upperIndices.size || !lowerIndices.size) return { targets: [], hasTunableOuter: false };

  mesh.updateWorldMatrix(true, false);
  const joint = mesh.worldToLocal(lower.getWorldPosition(new Vector3()));
  const shoulder = mesh.worldToLocal(upper.getWorldPosition(new Vector3()));
  const axis = joint.clone().sub(shoulder).normalize();
  const forward = new Vector3(0, 0, 1);
  const position = mesh.geometry.getAttribute('position');
  const skinIndex = mesh.geometry.getAttribute('skinIndex');
  const skinWeight = mesh.geometry.getAttribute('skinWeight');
  if (!position || !skinIndex || !skinWeight) return { targets: [], hasTunableOuter: false };

  const reach = options.reach ?? 0.095;
  const innerAmount = options.inner ?? 0.012;
  const outerAmount = options.outer ?? 0.006;
  const radialDelta = new Float32Array(position.count * 3);
  const point = new Vector3();
  const radial = new Vector3();

  for (let vertex = 0; vertex < position.count; vertex += 1) {
    pointFrom(position, vertex, point);
    const away = point.clone().sub(joint);
    if (away.length() > reach) continue;
    const weights = elbowPairWeights(
      skinIndex,
      skinWeight,
      vertex,
      upperIndices,
      lowerIndices,
    );
    const pair = weights.upper + weights.lower;
    if (pair < 0.5) continue;
    const share = weights.lower / pair;
    const centrality = 4 * share * (1 - share);
    if (centrality < 0.02) continue;
    radial.copy(away).addScaledVector(axis, -away.dot(axis));
    if (radial.lengthSq() < 1e-10) continue;
    radial.normalize();
    const facing = radial.dot(forward);
    const inner = Math.max(0, facing) ** 1.5;
    const outer = Math.max(0, -facing) ** 1.5;
    const push = (innerAmount * inner + outerAmount * outer) * centrality * pair;
    if (push < 1e-5) continue;
    radialDelta[vertex * 3] = radial.x * push;
    radialDelta[vertex * 3 + 1] = radial.y * push;
    radialDelta[vertex * 3 + 2] = radial.z * push;
  }

  const targets: Target[] = [];
  if (tuning) {
    const base = appendMorphTarget(
      mesh,
      side,
      radialDelta,
      `homeGymPT_elbow_${side}`,
      () => 1,
    );
    if (base) targets.push(base);

    // Build the full measured candidate once, then vary only its influence.
    // This keeps the authored bind-space displacement cap intact: the editor
    // control is bounded to 0..1 and never amplifies the 8 mm candidate target.
    const outerDelta = new Float32Array(position.count * 3);
    addOuterSmoothing(
      mesh.geometry,
      outerDelta,
      joint,
      axis,
      forward,
      upperIndices,
      lowerIndices,
      reach,
      1,
    );
    const outer = appendMorphTarget(
      mesh,
      side,
      outerDelta,
      `homeGymPT_elbow_outer_${side}`,
      () => clampOuterSmooth(tuning.outerSmooth),
    );
    if (outer) targets.push(outer);
    return { targets, hasTunableOuter: Boolean(outer) };
  }

  // Legacy/non-interactive path is byte-for-byte in spirit with the previous
  // behaviour: directional smoothing is folded into the one elbow target.
  const outerSmooth = Math.max(0, options.outerSmooth ?? 0);
  if (outerSmooth > 0) {
    addOuterSmoothing(
      mesh.geometry,
      radialDelta,
      joint,
      axis,
      forward,
      upperIndices,
      lowerIndices,
      reach,
      outerSmooth,
    );
  }
  const target = appendMorphTarget(
    mesh,
    side,
    radialDelta,
    `homeGymPT_elbow_${side}`,
    () => 1,
  );
  return { targets: target ? [target] : [], hasTunableOuter: false };
}

function appendMorphTarget(
  mesh: SkinnedMesh,
  side: Side,
  delta: Float32Array,
  name: string,
  scale: () => number,
): Target | null {
  const position = mesh.geometry.getAttribute('position');
  let affected = 0;
  for (let vertex = 0; vertex < position.count; vertex += 1) {
    const start = vertex * 3;
    if (
      Math.abs(delta[start]) > 1e-7 ||
      Math.abs(delta[start + 1]) > 1e-7 ||
      Math.abs(delta[start + 2]) > 1e-7
    ) {
      affected += 1;
    }
  }
  if (!affected) return null;

  // Three.js stores one morph convention per geometry. Do not flip an imported
  // character from absolute to relative morphs (or vice versa) just to append
  // this corrective: doing so would reinterpret every pre-existing expression
  // or body shape. Encode every new target in the existing convention.
  const morph = mesh.geometry.morphTargetsRelative
    ? new BufferAttribute(delta, 3)
    : absoluteMorph(position, delta);
  morph.name = name;
  const attributes = mesh.geometry.morphAttributes.position ?? [];
  mesh.geometry.morphAttributes.position = [...attributes, morph];
  mesh.updateMorphTargets();
  const influence = mesh.morphTargetDictionary?.[morph.name] ?? attributes.length;
  if (mesh.morphTargetInfluences) mesh.morphTargetInfluences[influence] = 0;
  return { mesh, side, influence, name: morph.name, scale };
}

'''
text = text[:start] + new_block + text[end:]
text = text.replace(
    "targets.forEach((target, index) => values[index].push(elbowFlexion(evaluation, target.side)));",
    "targets.forEach((target, index) =>\n        values[index].push(elbowFlexion(evaluation, target.side) * target.scale()),\n      );",
    1,
)
p.write_text(text)

# A retargeted source owns one tuning object for its lifetime. Every viewport
# build and every export build from that same source reads this same object.
replace(
    "src/character/retargetSource.ts",
    "import { importedElbowDeformation } from './importedDeformation';",
    "import { importedElbowDeformation } from './importedDeformation';\nimport type { ImportedElbowRuntimeTuning } from './importedDeformation';",
)
replace(
    "src/character/retargetSource.ts",
    "export function retargetedCharacterSource(\n  options: RetargetedCharacterOptions,\n): RetargetedCharacterSource {\n  const source: RetargetedCharacterSource = {",
    "export function retargetedCharacterSource(\n  options: RetargetedCharacterOptions,\n): RetargetedCharacterSource {\n  const elbowTuning: ImportedElbowRuntimeTuning = { outerSmooth: 0, defaultOuterSmooth: 0 };\n  let elbowTuningInitialised = false;\n\n  const source: RetargetedCharacterSource = {",
)
replace(
    "src/character/retargetSource.ts",
    "      const deformation = importedElbowDeformation(\n        character.meshes as SkinnedMesh[],\n        boneByName,\n        rig,\n        scene.userData?.homeGymPT?.elbowCorrective,\n      );",
    "      const elbowOptions = scene.userData?.homeGymPT?.elbowCorrective;\n      if (elbowOptions?.enabled && !elbowTuningInitialised) {\n        const authored = Number(elbowOptions.outerSmooth ?? 0);\n        const bounded = Number.isFinite(authored) ? Math.min(1, Math.max(0, authored)) : 0;\n        elbowTuning.outerSmooth = bounded;\n        elbowTuning.defaultOuterSmooth = bounded;\n        elbowTuningInitialised = true;\n      }\n      const deformation = importedElbowDeformation(\n        character.meshes as SkinnedMesh[],\n        boneByName,\n        rig,\n        elbowOptions,\n        elbowOptions?.enabled ? elbowTuning : undefined,\n      );",
)

# Correctives workspace: live, source-level, export-aware control.
p = Path("src/editor/panels/CorrectivePanel.tsx")
text = p.read_text()
text = text.replace(
    "  const diagnostics = active ? correctiveDiagnostics(active.meshes) : [];\n  const [strain, setStrain] = useState<MeshStrainDiagnostic[]>([]);",
    "  const diagnostics = active ? correctiveDiagnostics(active.meshes) : [];\n  const controls = active?.deformation?.controls ?? [];\n  const [, refreshControls] = useState(0);\n  const [strain, setStrain] = useState<MeshStrainDiagnostic[]>([]);",
    1,
)
anchor = """      <div className=\"corrective-ab\">\n        <button type=\"button\" className={enabled ? 'is-active' : ''} onClick={() => setEnabled(true)}>\n          Correctives on\n        </button>\n        <button type=\"button\" className={!enabled ? 'is-active' : ''} onClick={() => setEnabled(false)}>\n          Raw skinning\n        </button>\n      </div>\n"""
insert = anchor + """\n      {controls.length > 0 && (\n        <>\n          <h3>Corrective tuning</h3>\n          <p className=\"panel__hint\">\n            Character-specific and export-aware. These controls change neither the exercise clip nor\n            the source skin weights; the active character and GLB export share the same value.\n          </p>\n          {controls.map((control) => (\n            <div className=\"strain-card\" key={control.id}>\n              <strong>{control.label} · {Math.round(control.value * 100)}%</strong>\n              <input\n                type=\"range\"\n                min={control.min}\n                max={control.max}\n                step={control.step}\n                value={control.value}\n                onChange={(event) => {\n                  control.set(Number(event.target.value));\n                  refreshControls((value) => value + 1);\n                  setWholeRep(null);\n                }}\n              />\n              {control.note && <small>{control.note}</small>}\n              <div className=\"button-row\">\n                <button\n                  type=\"button\"\n                  disabled={Math.abs(control.value - control.defaultValue) < 1e-9}\n                  onClick={() => {\n                    control.set(control.defaultValue);\n                    refreshControls((value) => value + 1);\n                    setWholeRep(null);\n                  }}\n                >\n                  Reset authored value\n                </button>\n              </div>\n            </div>\n          ))}\n        </>\n      )}\n"""
if anchor not in text:
    raise SystemExit("missing corrective A/B anchor")
text = text.replace(anchor, insert, 1)
p.write_text(text)

# Regression: a v5-style zero outer value still builds the candidate target in
# interactive mode; the live driver and exporter sampler both read one shared control.
p = Path("src/character/importedDeformation.test.ts")
text = p.read_text()
text = text.replace(
    "import { canonicalSkeleton } from '../rig/skeleton';",
    "import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';\nimport { restPose } from '../rig/pose';",
    1,
)
addition = r'''

  it('tunes outer smoothing live and bakes the same value through the export sampler', () => {
    const { mesh, boneByName } = elbowFixture();
    const tuning = { outerSmooth: 0, defaultOuterSmooth: 0 };
    const deformation = importedElbowDeformation(
      [mesh],
      boneByName,
      canonicalSkeleton,
      { enabled: true, inner: 0, outer: 0, outerSmooth: 0 },
      tuning,
    );
    expect(deformation).not.toBeNull();
    const control = deformation!.controls?.find((entry) => entry.id === 'elbowOuterSmooth');
    expect(control).toBeDefined();
    expect(control!.value).toBe(0);

    const outerIndex = mesh.morphTargetDictionary?.homeGymPT_elbow_outer_l;
    expect(typeof outerIndex).toBe('number');
    const pose = restPose();
    pose.rotations.forearm_l = { x: (120 * Math.PI) / 180, y: 0, z: 0 };
    const evaluation = new PoseEvaluation(canonicalSkeleton).apply(pose);

    deformation!.update({
      rig: canonicalSkeleton,
      pose,
      evaluation,
      character: null as never,
    });
    expect(mesh.morphTargetInfluences?.[outerIndex as number]).toBe(0);

    control!.set(1);
    deformation!.update({
      rig: canonicalSkeleton,
      pose,
      evaluation,
      character: null as never,
    });
    const live = mesh.morphTargetInfluences?.[outerIndex as number] ?? 0;
    expect(live).toBeGreaterThan(0.5);

    const sampler = deformation!.sampler?.();
    expect(sampler).not.toBeNull();
    sampler!.sample(restPose());
    sampler!.sample(pose);
    const track = sampler!.tracks([0, 1]).find((entry) =>
      entry.name.includes('homeGymPT_elbow_outer_l'),
    );
    expect(track).toBeDefined();
    expect(Number(track!.values[track!.values.length - 1])).toBeCloseTo(live, 6);

    control!.set(2);
    expect(control!.value).toBe(1);
    control!.set(-1);
    expect(control!.value).toBe(0);
  });
'''
pos = text.rfind("\n});")
if pos < 0:
    raise SystemExit("missing importedDeformation test suite end")
text = text[:pos] + addition + text[pos:]
p.write_text(text)

# Roadmap and coordination log.
replace(
    "docs/STUDIO_CAPABILITY_ROADMAP.md",
    "- On-demand whole-rep strain review scans the active character at the authored clip FPS, records worst P99/max deformation timestamps for each mesh, restores the current playhead pose, and can jump directly to the worst frame in either Correctives-on or Raw-skinning mode.",
    "- On-demand whole-rep strain review scans the active character at the authored clip FPS, records worst P99/max deformation timestamps for each mesh, restores the current playhead pose, and can jump directly to the worst frame in either Correctives-on or Raw-skinning mode.\n- Imported elbow outer-smoothing is now a bounded 0–100% character-level control. The retained radial volume morph remains separate, the measured candidate morph stays capped at 8 mm, and the active viewport plus GLB export sampler share the exact same source-level tuning value.",
)

p = Path("AI_CHANGELOG.md")
text = p.read_text()
entry = r'''
### ChatGPT — 2026-09-14 — export-aware outer-elbow corrective tuning

Split the imported elbow's optional directional outer-smoothing from the retained radial volume corrective when a retargeted character is built for interactive authoring. The radial `homeGymPT_elbow_*` target is unchanged; a separate `homeGymPT_elbow_outer_*` target contains the full measured directional candidate and keeps the existing 8 mm bind-space displacement cap. Its authoring value is bounded to 0–100%, so the editor can never amplify that candidate beyond the measured cap.

The retargeted character source owns one shared outer-smoothing tuning object for its lifetime. Viewport builds and fresh GLB export builds from that source therefore read the same value rather than keeping a viewport-only override. The Correctives workspace exposes the control with an authored-value reset, while Raw skinning remains a separate non-destructive A/B bypass. Exercise data, source vertices, source skin weights and the preserved skeleton remain untouched.

Regression coverage starts from a v5-style authored value of 0%, proves the tunable outer target is available without changing the retained radial path, verifies the live deformation influence responds to the control, verifies the export deformation sampler bakes the same influence, and proves out-of-range edits clamp to the safe 0–100% interval.

'''
marker = "## Unreleased\n\n"
if marker not in text:
    raise SystemExit("missing changelog Unreleased marker")
text = text.replace(marker, marker + entry, 1)
p.write_text(text)

print("Applied export-aware outer-elbow corrective tuning")
