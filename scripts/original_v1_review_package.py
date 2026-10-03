#!/usr/bin/env python3
"""Build a hash-bound owner-facing review index from existing real review artifacts.

Never renders or synthesizes an image. It indexes only previously verified source
PNG review manifests and optional comparison-board manifests.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from original_v1_production_control import ROOT,CAND,digest,ensure_finite
from original_v1_candidate_closure import candidate_entry


def review_manifest(root:Path,revision:str,kind:str):
    path=root/CAND/f"review/{kind}_{revision}/visual_review_manifest.json"
    if not path.is_file():return None
    data=json.loads(path.read_text(encoding="utf-8"));ensure_finite(data)
    row,_=candidate_entry(root,revision)
    if data.get("candidate_revision")!=revision or data.get("candidate_sha256")!=row.get("sha256"):
        raise ValueError(kind+" review candidate identity differs")
    files=[]
    for item in data.get("files",[]):
        p=(root/item["output"]).resolve()
        if not p.is_relative_to((root/CAND/"review").resolve()) or not p.is_file() or digest(p)!=item["sha256"]:
            raise ValueError(kind+" review image hash/path differs")
        files.append({
            "label":item.get("file") or p.name,
            "path":p.relative_to(root).as_posix(),
            "sha256":item["sha256"],
            "capture":item.get("capture"),
            "set":item.get("set"),
            "pose":item.get("pose"),
            "view":item.get("view"),
            "region":item.get("region"),
        })
    return {
        "kind":kind,
        "owner_review":data.get("owner_review"),
        "blocking":data.get("blocking"),
        "manifest":{"path":path.relative_to(root).as_posix(),"sha256":digest(path)},
        "files":files,
    }


def comparison_manifests(root:Path,revision:str):
    base=root/CAND/"review"
    rows=[]
    if not base.is_dir():return rows
    for path in sorted(base.glob(f"comparison_*_{revision}*/comparison_manifest.json")):
        data=json.loads(path.read_text(encoding="utf-8"));ensure_finite(data)
        if data.get("candidate_revision")!=revision:continue
        boards=[]
        for item in data.get("boards",[]):
            p=path.parent/item["file"]
            if not p.is_file() or digest(p)!=item.get("board_sha256"):
                raise ValueError("comparison board hash/path differs")
            boards.append({
                "path":p.relative_to(root).as_posix(),"sha256":item["board_sha256"],
                "capture_settings_match":item.get("capture_settings_match"),
                "previous_png":item.get("previous_png"),"candidate_png":item.get("candidate_png")
            })
        rows.append({
            "previous_revision":data.get("previous_revision"),
            "owner_review":data.get("owner_review"),
            "blocking":data.get("blocking"),
            "manifest":{"path":path.relative_to(root).as_posix(),"sha256":digest(path)},
            "boards":boards,
        })
    return rows


def build_package(root:Path,revision:str)->dict:
    if not re.fullmatch(r"r\d+",revision):raise ValueError("numbered candidate revision required")
    row,_=candidate_entry(root,revision)
    packages=[]
    for kind in ("visual","milestone"):
        item=review_manifest(root,revision,kind)
        if item is not None:packages.append(item)
    comparisons=comparison_manifests(root,revision)
    image_count=sum(len(x["files"]) for x in packages)
    return {
        "schema_version":1,
        "status":"REVIEW_PACKAGE_READY" if packages else "NO_REVIEW_CAPTURE_YET",
        "production_approved":False,
        "candidate_revision":revision,
        "candidate_sha256":row.get("sha256"),
        "candidate_classification":row.get("classification"),
        "candidate_state":row.get("state"),
        "owner_review":row.get("owner_review"),
        "review_sets":packages,
        "comparison_sets":comparisons,
        "image_count":image_count,
        "comparison_board_count":sum(len(x["boards"]) for x in comparisons),
        "next_review_action":"Use RUN_ORIGINAL_V1_MILESTONE_REVIEW.bat "+revision if not packages else "Owner may review indexed real images; routine review remains non-blocking.",
        "note":"Index of existing real review artifacts only. No image is generated, altered or accepted by this packager."
    }


def markdown(data:dict)->str:
    lines=[
        f"# {data['candidate_revision']} review package","",
        f"Candidate SHA: `{data['candidate_sha256']}`",
        f"Classification/state: **{data.get('candidate_classification')} / {data.get('candidate_state')}**",
        f"Owner review: **{data.get('owner_review')}** — routine review NON-BLOCKING.","",
    ]
    if not data["review_sets"]:
        lines+=["No verified review captures are indexed yet.","",data["next_review_action"],""]
    for review in data["review_sets"]:
        lines += [f"## {review['kind'].title()} review",""]
        for item in review["files"]:
            label=" / ".join(str(x) for x in (item.get("region") or item.get("pose"),item.get("view")) if x)
            lines += [f"- {label or Path(item['path']).name}: {item['path']} — {item['sha256'][:12]}..."]
        lines.append("")
    if data["comparison_sets"]:
        lines+=["## Comparisons",""]
        for comp in data["comparison_sets"]:
            lines += [f"- vs {comp['previous_revision']}: {len(comp['boards'])} board(s); owner review {comp.get('owner_review')}"]
        lines.append("")
    lines += ["This package indexes actual project review artifacts only; it is not visual acceptance.",""]
    return "\n".join(lines)


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("revision");ap.add_argument("--out-dir",type=Path)
    args=ap.parse_args()
    try:
        data=build_package(ROOT,args.revision)
        if args.out_dir:
            out=args.out_dir.resolve()
            if not out.is_relative_to(ROOT.resolve()):raise ValueError("output folder must remain inside repository")
            if out.exists():raise ValueError("review package output collision")
            out.mkdir(parents=True)
            (out/"review_package.json").write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
            (out/"README.md").write_text(markdown(data),encoding="utf-8")
        print(json.dumps(data,indent=2))
        return 0 if data["status"]=="REVIEW_PACKAGE_READY" else 1
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc));return 2

if __name__=="__main__":
    raise SystemExit(main())
