"""Create a focused prompt-family certification handoff from the current source tree.

This is a preparation/report tool. It does not edit the source adapter or mark
a family certified.

Usage:
  python scripts/prepare_prompt_family_certification.py hinge
  python scripts/prepare_prompt_family_certification.py row --source-root path/to/source
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent
MANIFEST=ROOT/"PROMPT_FAMILY_CERTIFICATION_MANIFEST.json"

def git(source,*args):
    try:
        return subprocess.check_output(["git",*args],cwd=source,text=True,stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None

def extract_interface(text,name_hint="Variant"):
    pattern=re.compile(
        rf"export\s+interface\s+(\w*{name_hint}\w*)\s*\{{(?P<body>.*?)\n\}}",
        re.S,
    )
    m=pattern.search(text)
    if not m:return None
    return m.group(1),m.group("body").strip()

def definition_hits(source,eid):
    hits=[]
    root=source/"src"/"exercises"/"definitions"
    if not root.is_dir():return hits
    token=re.compile(rf"\bid\s*:\s*['\"]{re.escape(eid)}['\"]")
    for path in sorted(root.glob("*.ts")):
        try:text=path.read_text(encoding="utf-8")
        except Exception:continue
        if token.search(text) or eid in text:
            hits.append(path.relative_to(source).as_posix())
    return hits

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("family")
    ap.add_argument("--source-root",type=Path,default=REPO)
    args=ap.parse_args()
    source=args.source_root.resolve()

    manifest=json.loads(MANIFEST.read_text())
    family=next((x for x in manifest["families"] if x["id"]==args.family),None)
    if not family:
        raise SystemExit(
            f"Unknown family {args.family!r}. Known: "
            +", ".join(x["id"] for x in manifest["families"])
        )

    family_path=source/family["file"]
    if not family_path.is_file():
        raise SystemExit(f"Missing family builder: {family_path}")
    family_text=family_path.read_text(encoding="utf-8")
    interface=extract_interface(family_text)
    test_path=family_path.with_suffix(".test.ts")
    generator=source/"src"/"generation"/"families.ts"
    parser=source/"src"/"generation"/"parse.ts"
    generate_test=source/"src"/"generation"/"generate.test.ts"
    parse_test=source/"src"/"generation"/"parse.test.ts"

    definitions={eid:definition_hits(source,eid) for eid in family["library"]}
    head=git(source,"rev-parse","HEAD")
    current_branch=git(source,"branch","--show-current")

    lines=[
        f"# Prompt certification start — {family['id']}",
        "",
        "This handoff is generated from the current checkout. It does not certify the family.",
        "",
        "## Source",
        f"- branch: {current_branch}",
        f"- HEAD: {head}",
        f"- manifest state: {family['status']}",
        f"- planned order: {family.get('order')}",
        f"- builder: {family['builder']}",
        f"- builder file: {family['file']}",
        f"- builder test: {test_path.relative_to(source).as_posix() if test_path.is_file() else 'MISSING'}",
        f"- parser refusal marker: {family.get('refusal_marker','—')}",
        "",
        "## Proving library exercises",
    ]
    for eid in family["library"]:
        found=definitions[eid]
        lines.append(f"- {eid} — definitions: {', '.join(found) if found else 'not located by static scan'}")

    if interface:
        name,body=interface
        lines += [
            "",
            "## Existing typed family variant",
            f"{name} fields from the builder:",
            "",
            "~~~ts",
            f"interface {name} {{",
            body,
            "}",
            "~~~",
        ]

    lines += [
        "",
        "## Required workflow",
        "",
        "1. Reproduce the proving set through the family builder first. If a library reference cannot be reproduced by its own family, fix/record that architecture before generator work.",
        "2. Add one thin adapter in src/generation/families.ts. Do not copy joint angles, rules or equipment geometry into the adapter.",
        "3. Translate only prompt fields that correspond to real typed family parameters.",
        "4. Keep explicit assumptions/defaults. Never silently drop named equipment, load, support, grip, side or execution.",
        "5. Remove/change this family's active parser refusal only after the adapter and validation evidence exist.",
        "6. Run first-pass generation on the final character before adding any correction lever.",
        "7. Add a lever only for a measured failure and only when it is a bounded family-level parameter.",
        "8. Require one-step-beyond confirmation for an accepted correction value.",
        "9. Add positive, contradictory and nearby-unsupported prompt tests.",
        "10. Generate automatic review views before calling the family autonomous.",
        "11. Run the full source suite and the existing certified-prompt regression corpus.",
        "12. Update PROMPT_FAMILY_CERTIFICATION_MANIFEST.json and matrix to CERTIFIED only after all evidence is recorded.",
        "",
        "## Core source files",
        f"- {generator.relative_to(source).as_posix()}",
        f"- {parser.relative_to(source).as_posix()}",
        f"- {generate_test.relative_to(source).as_posix() if generate_test.is_file() else 'MISSING'}",
        f"- {parse_test.relative_to(source).as_posix() if parse_test.is_file() else 'MISSING'}",
        "",
        "## Suggested test progression",
        "",
        "~~~text",
        f"npx vitest run {test_path.relative_to(source).as_posix() if test_path.is_file() else family['file']}",
        "npx vitest run src/generation/parse.test.ts src/generation/generate.test.ts",
        "python HIGH_DETAIL_MESH_WORK/scripts/audit_prompt_generation_coverage.py --source-root .",
        "npm test",
        "~~~",
        "",
        "For character-dependent certification, point the generation/validation harness at the final accepted character, not an older production mesh.",
        "",
        "## Evidence to fill",
        "",
        "Use PROMPT_FAMILY_CERTIFICATION_TEMPLATE.md. Final status must be exactly one of CERTIFIED / IN REVIEW / BLOCKED.",
    ]

    out=ROOT/"reports"/f"PROMPT_CERT_START_{family['id']}.md"
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(out.read_text())

if __name__=="__main__":
    main()
