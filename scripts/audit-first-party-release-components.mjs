#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const manifest = JSON.parse(
  fs.readFileSync(path.join(ROOT, "FIRST_PARTY_COMPONENT_MANIFEST.json"), "utf8"),
);

const required = manifest.required_release_component_ids || [];
const components = manifest.components || [];
const byId = new Map();
const duplicateIds = [];

for (const component of components) {
  if (byId.has(component.id)) duplicateIds.push(component.id);
  byId.set(component.id, component);
}

const missing = [];
const notApproved = [];
for (const id of required) {
  const component = byId.get(id);
  if (!component) {
    missing.push(id);
    continue;
  }
  if (component.status !== "first_party_approved") {
    notApproved.push({
      id,
      status: component.status,
      required_action: component.required_action || null,
    });
  }
}

const pass =
  required.length > 0 &&
  duplicateIds.length === 0 &&
  missing.length === 0 &&
  notApproved.length === 0;

const result = {
  generatedAt: new Date().toISOString(),
  pass,
  requiredReleaseComponents: required,
  blockers: {
    noRequiredComponentsDeclared: required.length === 0,
    duplicateIds: [...new Set(duplicateIds)].sort(),
    missing,
    notApproved,
  },
  rule:
    "A release cannot pass while any required software/model component is absent or has a status other than first_party_approved.",
};

fs.mkdirSync(path.join(ROOT, "reports"), { recursive: true });
fs.writeFileSync(
  path.join(ROOT, "reports", "first_party_release_components.json"),
  JSON.stringify(result, null, 2) + "\n",
);
const expectBlocked = process.argv.includes("--expect-blocked");
if (expectBlocked) {
  const requiredPending = [
    "male_character",
    "male_shorts",
    "canonical_rig",
    "equipment_geometry",
  ];
  const pendingIds = new Set(notApproved.map((entry) => entry.id));
  const unexpectedPending = notApproved.filter(
    (entry) => !requiredPending.includes(entry.id),
  );
  const expectationPass =
    !pass &&
    missing.length === 0 &&
    requiredPending.every((id) => pendingIds.has(id)) &&
    unexpectedPending.length === 0;
  const expectation = {
    ...result,
    expectation: "release_blocked_only_by_original_model_rig_and_final_equipment_fit",
    requiredPending,
    unexpectedPending,
    expectationPass,
  };
  console.log(JSON.stringify(expectation, null, 2));
  process.exit(expectationPass ? 0 : 1);
}

console.log(JSON.stringify(result, null, 2));
process.exit(pass ? 0 : 1);
