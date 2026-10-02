import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { auditExerciseAnimationProvenance } from "./audit-exercise-animation-provenance.mjs";

const ROOT = process.cwd();

function fixture(source) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "hgpt-exercise-provenance-"));
  fs.mkdirSync(path.join(root, "src", "exercises", "definitions"), { recursive: true });
  fs.writeFileSync(
    path.join(root, "EXERCISE_ANIMATION_PROVENANCE.json"),
    JSON.stringify({
      component_id: "exercise_animation_data",
      classification: "first_party_project_authored",
      operational_source_root: "src/exercises",
      third_party_sources: [],
      external_animation_inputs: [],
    }),
  );
  fs.writeFileSync(
    path.join(root, "src", "exercises", "definitions", "sample.ts"),
    source,
  );
  return root;
}

test("current repository exercise-animation data satisfies the first-party provenance boundary", () => {
  const result = auditExerciseAnimationProvenance(ROOT);
  assert.equal(result.pass, true, JSON.stringify(result, null, 2));
  assert.ok(result.definitionFileCount >= 28, JSON.stringify(result, null, 2));
  assert.ok(result.familyFileCount >= 16, JSON.stringify(result, null, 2));
});

test("provenance gate rejects an external animation asset reference", () => {
  const root = fixture("const clip = 'motion.bvh';\n");
  try {
    const result = auditExerciseAnimationProvenance(root);
    assert.equal(result.pass, false);
    assert.ok(result.evidence.assetReferences.length > 0);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("provenance gate rejects a bare third-party import or remote read", () => {
  const root = fixture("import thing from 'some-package';\nfetch('https://example.com/motion');\n");
  try {
    const result = auditExerciseAnimationProvenance(root);
    assert.equal(result.pass, false);
    assert.ok(result.evidence.bareImports.length > 0);
    assert.ok(result.evidence.remoteReads.length > 0);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});
