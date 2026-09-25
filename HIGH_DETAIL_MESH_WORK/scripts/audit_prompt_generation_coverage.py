"""Audit prompt-family certification coverage against a source checkout.

The manifest is the explicit project truth for which existing movement families
are certified, not certified, in review or blocked. This audit catches drift:
- a family builder vanished;
- an exercise proving set vanished;
- a manifest CERTIFIED family is not actually registered in GENERATOR_FAMILIES;
- a NOT_CERTIFIED/BLOCKED family was accidentally registered;
- an uncertified family no longer has an explicit refusal marker;
- the current family/library counts no longer match the manifest.

Usage:
  python scripts/audit_prompt_generation_coverage.py
  python scripts/audit_prompt_generation_coverage.py --source-root path/to/source
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent
MANIFEST=ROOT/"PROMPT_FAMILY_CERTIFICATION_MANIFEST.json"

ADAPTER_RE=re.compile(
    r"const\s+(?P<var>\w+)\s*:\s*GeneratorFamily(?:<[^;={]+>)?\s*=\s*\{.*?"
    r"\bid\s*:\s*['\"](?P<id>[^'\"]+)['\"]",
    re.S,
)
REGISTRY_RE=re.compile(
    r"export\s+const\s+GENERATOR_FAMILIES\s*:\s*GeneratorFamily\[\]\s*=\s*\[(?P<body>.*?)\];",
    re.S,
)
ARRAY_VAR_RE=re.compile(r"\b([A-Za-z_]\w*)\s*(?:as\s+unknown\s+as\s+GeneratorFamily)?\s*,?")

def read(path):
    return path.read_text(encoding="utf-8")

def find_library_ids(source_root):
    ids=set()
    definitions=source_root/"src"/"exercises"/"definitions"
    if definitions.is_dir():
        for path in definitions.glob("*.ts"):
            text=read(path)
            ids.update(re.findall(r"\bid\s*:\s*['\"]([a-z0-9_]+)['\"]",text))
    # Family-backed definition files may still be enough, but scanning the
    # exercises tree catches proving IDs declared in small adapter definitions.
    for path in (source_root/"src"/"exercises").glob("*.ts"):
        text=read(path)
        ids.update(re.findall(r"\bid\s*:\s*['\"]([a-z0-9_]+)['\"]",text))
    return ids

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-root",type=Path,default=REPO)
    args=ap.parse_args()
    source=args.source_root.resolve()

    if not MANIFEST.is_file():
        raise SystemExit(f"Missing certification manifest: {MANIFEST}")
    manifest=json.loads(MANIFEST.read_text())
    families=manifest["families"]

    failures=[];warnings=[];detail={}

    family_files=[
        p for p in (source/"src"/"exercises"/"families").glob("*.ts")
        if not p.name.endswith(".test.ts")
    ]
    actual_builder_files={p.relative_to(source).as_posix() for p in family_files}
    detail["actual_family_builder_files"]=sorted(actual_builder_files)
    if len(family_files)!=manifest["total_family_builders"]:
        failures.append(
            f"Family builder count drift: manifest {manifest['total_family_builders']}, "
            f"source {len(family_files)}."
        )

    gen_path=source/"src"/"generation"/"families.ts"
    parse_path=source/"src"/"generation"/"parse.ts"
    library_path=source/"src"/"exercises"/"library.ts"
    for p in (gen_path,parse_path,library_path):
        if not p.is_file():failures.append(f"Missing generator source: {p}")
    if failures:
        print(json.dumps({"pass":False,"failures":failures},indent=2))
        raise SystemExit(1)

    gen=read(gen_path);parse=read(parse_path);library=read(library_path)
    adapters={m.group("var"):m.group("id") for m in ADAPTER_RE.finditer(gen)}
    registry_match=REGISTRY_RE.search(gen)
    if not registry_match:
        failures.append("Could not locate GENERATOR_FAMILIES registry.")
        registered_vars=set()
    else:
        body=registry_match.group("body")
        registered_vars={
            m.group(1) for m in ARRAY_VAR_RE.finditer(body)
            if m.group(1) not in {"as","unknown","GeneratorFamily"}
        }
    certified_source_ids={adapters[v] for v in registered_vars if v in adapters}
    detail["adapter_variables"]=adapters
    detail["registered_adapter_variables"]=sorted(registered_vars)
    detail["certified_source_ids"]=sorted(certified_source_ids)

    library_ids=find_library_ids(source)
    # The library array itself is still the authoritative count.
    lib_body=re.search(r"export\s+const\s+EXERCISES[^=]*=\s*\[(.*?)\];",library,re.S)
    lib_entries=[]
    if lib_body:
        lib_entries=[x.strip() for x in lib_body.group(1).split(",") if x.strip()]
    if len(lib_entries)!=manifest["total_library_exercises"]:
        failures.append(
            f"Library count drift: manifest {manifest['total_library_exercises']}, "
            f"source array {len(lib_entries)}."
        )
    detail["library_array_entries"]=lib_entries

    family_results={}
    manifest_ids=set()
    proving_ids=[]
    for family in families:
        fid=family["id"];manifest_ids.add(fid)
        status=family["status"]
        result={"status":status,"checks":{}}

        fpath=source/family["file"]
        exists=fpath.is_file()
        result["checks"]["family_file_exists"]=exists
        if not exists:
            failures.append(f"{fid}: missing builder file {family['file']}")
        else:
            text=read(fpath)
            exported=bool(re.search(
                rf"export\s+function\s+{re.escape(family['builder'])}\s*\(",
                text,
            ))
            result["checks"]["builder_export_exists"]=exported
            if not exported:
                failures.append(f"{fid}: builder export {family['builder']} not found")

        for eid in family["library"]:
            proving_ids.append(eid)
            present=eid in library_ids or eid in library
            result["checks"][f"library:{eid}"]=present
            if not present:
                failures.append(f"{fid}: proving library exercise {eid} not found in source")

        registered=fid in certified_source_ids
        result["registered_for_generation"]=registered
        if status=="CERTIFIED":
            if not registered:
                failures.append(f"{fid}: manifest says CERTIFIED but source registry does not")
            marker=family.get("refusal_marker")
            if marker and marker.lower() in parse.lower():
                warnings.append(
                    f"{fid}: certified family still contains old refusal marker {marker!r}; "
                    "verify it is historical/comment text rather than active NOT_CERTIFIED logic."
                )
        elif status in {"NOT_CERTIFIED","BLOCKED"}:
            if registered:
                failures.append(f"{fid}: {status} family is unexpectedly registered for generation")
            marker=family.get("refusal_marker")
            if marker:
                found=marker.lower() in parse.lower()
                result["checks"]["explicit_refusal_marker"]=found
                if not found:
                    failures.append(
                        f"{fid}: uncertified family lacks expected parser refusal marker {marker!r}"
                    )
            else:
                warnings.append(f"{fid}: uncertified family has no refusal_marker in manifest")
        elif status=="IN_REVIEW":
            # Either registration state can be valid while work is staged, but
            # it must not be declared complete by this audit.
            warnings.append(f"{fid}: family is IN_REVIEW; certification is intentionally unresolved")
        else:
            failures.append(f"{fid}: unknown manifest status {status!r}")

        family_results[fid]=result

    if len(manifest_ids)!=len(families):
        failures.append("Duplicate family IDs in certification manifest.")
    if len(proving_ids)!=len(set(proving_ids)):
        failures.append("A library exercise appears in more than one family proving set.")
    if len(set(proving_ids))!=manifest["total_library_exercises"]:
        failures.append(
            f"Manifest family proving sets cover {len(set(proving_ids))} unique exercises, "
            f"expected {manifest['total_library_exercises']}."
        )

    # No registered adapter should exist outside the explicit manifest.
    untracked=sorted(certified_source_ids-manifest_ids)
    if untracked:
        failures.append("Registered generator families missing from manifest: "+", ".join(untracked))

    report={
        "source_root":str(source),
        "manifest":MANIFEST.name,
        "manifest_prepared_from_source_head":manifest.get("prepared_from_source_head"),
        "family_count_manifest":len(families),
        "family_count_source":len(family_files),
        "library_count_manifest":manifest["total_library_exercises"],
        "library_count_source":len(lib_entries),
        "certified_manifest_ids":sorted(f["id"] for f in families if f["status"]=="CERTIFIED"),
        "certified_source_ids":sorted(certified_source_ids),
        "families":family_results,
        "warnings":warnings,
        "failures":failures,
        "pass":not failures,
    }
    out=ROOT/"reports"/"prompt_generation_coverage.json"
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    if failures:raise SystemExit(1)

if __name__=="__main__":
    main()
