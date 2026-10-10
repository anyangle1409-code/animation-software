#!/usr/bin/env python3
"""ONE command: prepare private, original-source CT review plates without Claude.

Use from repository root, with normal Python 3 (no pip packages):
    python scripts/anatomy_fit/nlm_ct_laptop_review.py --open

The default covers ALL original provisional pelvic point-containing slices,
plus one neighbouring slice on either side. It downloads original Visible
Human CT PNGs and GE headers directly from NLM, verifies exact original
SHA-256/bytes BEFORE writing them, and generates first-party browser-readable
three-slice CT plates. No third-party runtime or account required.

PRIVATE ONLY. Original source bytes, derived CT images and review reports are
stored under the user's HOME, OUTSIDE the Git worktree. Nothing is uploaded.
No previously proposed point is accepted as a bone landmark; no geometry
is modified, registered, or promoted.
"""
import argparse
from html import escape
import hashlib
import json
from pathlib import Path
import re
import urllib.request
import webbrowser

from ct_pelvis_window_geometry import assert_private_location
from nlm_ct_private_slice_review_plate import private_ct_plate
from nlm_ct_private_annotation_capture import make_offline_annotation_html
from nlm_ct_raw_png_calibration import validate_calibration_evidence
from pelvic_ct_series_manifest import validate_series_bundle

REPO=Path(__file__).resolve().parents[2]
AUDIT=REPO/"ORIGINAL_V1_WORK"/"anatomy"/"audit"
DEFAULT_BUNDLE=AUDIT/"nlm_pelvic_ct_full_series_candidate_bundle_20261009.json"
DEFAULT_CAL=AUDIT/"nlm_pelvic_ct_full_series_hu_calibration_20261009.json"
DEFAULT_REVIEW=AUDIT/"nlm_pelvic_ct_full_series_candidate_review_20261009.json"
DEFAULT_WORKSPACE=Path.home()/"HomeGymPT_Private_Original_CT_Review"
BASE_PNG="https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Male-Images/PNG_format/radiological/normalCT/"
BASE_HDR="https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Male-Images/PNG_format/radiological/normalCTHeaders/"
ALLOWED_ID=re.compile(r"^cvm[0-9]{4}f$")


def selected_three_neighbours(bundle, review, source_id):
    """Resolve one centre with exactly its two same-acquisition adjacent frames."""
    if not isinstance(source_id,str) or ALLOWED_ID.fullmatch(source_id) is None:
        raise ValueError("only original validated NLM source ID is allowed")
    if review.get("kind")!="NLM_CT_ANATOMICAL_REVIEW_PACKET":
        raise ValueError("unrecognized original source review packet")
    matches=[]
    for group, series in enumerate(bundle["series"],1):
        ids=[r["source_id"] for r in series["slices"]]
        if source_id in ids:
            idx=ids.index(source_id)
            if not (1<=idx<len(ids)-1):
                raise ValueError("review triplet would cross original acquisition boundary")
            matches.append((group,series["slices"][idx-1:idx+2]))
    if len(matches)!=1:
        raise ValueError("requested CT source ID must appear once in verified manifest")
    group,rows=matches[0]
    centre=rows[1]
    points=[p for p in review["observations"] if p["source_id"]==source_id]
    if not points:
        raise ValueError("source review contains no provisional observation at that axial plane")
    for obs in points:
        if obs["source_png_sha256"]!=centre["source_png_sha256"] or (
                obs["source_header_sha256"]!=centre["source_header_sha256"]):
            raise ValueError("original observation hash changed")
        if abs(obs["scanner_S_mm"]-centre["scanner_centre_RAS_mm"][2])>1e-6:
            raise ValueError("original observation scanner position changed")
    return group,rows


def download_original_pinned_pair(row, destination, *, opener=None):
    """Never overwrite mismatched originals or follow redirected URLs.

    Returns (number of newly retrieved files, reused exact originals). The
    only accepted content is the official pinned PNG/header SHA and byte size.
    """
    if opener is None:
        opener=urllib.request.urlopen
    raw_folder=Path(destination)
    if raw_folder.is_symlink():
        raise ValueError("CT input directory must not be a symlink")
    folder=assert_private_location(raw_folder)
    folder.mkdir(parents=True,exist_ok=True)
    sid=row["source_id"]
    if ALLOWED_ID.fullmatch(sid) is None:
        raise ValueError("untrusted source filename")
    total_new=0
    reused=0
    for ext,base,digest_key,limit in (
            (".png",BASE_PNG,"source_png_sha256",2_000_000),
            (".txt",BASE_HDR,"source_header_sha256",65_536)):
        target=folder/(sid+ext)
        if target.is_symlink():
            raise ValueError("source files must not be symlinks")
        digest=row[digest_key]
        if not isinstance(digest,str) or not re.fullmatch(r"[0-9a-f]{64}",digest):
            raise ValueError("source digest missing or malformed")
        if target.exists():
            payload=target.read_bytes()
            if (len(payload)>limit or
                    hashlib.sha256(payload).hexdigest()!=digest or
                    (ext==".png" and len(payload)!=row["source_png_bytes"])):
                raise ValueError("existing original source is not exact hash pinned; refusing to replace")
            reused+=1
            continue
        url=base+sid+ext
        request=urllib.request.Request(url,headers={"User-Agent":"HomeGymPT-Private-Original-CT-Review/1.0"})
        with opener(request,timeout=45) as reply:
            status=getattr(reply,"status",200)
            final_url=reply.geturl()
            if status!=200 or final_url!=url:
                raise ValueError("original NLM source endpoint changed or redirected")
            payload=reply.read(limit+1)
        if (len(payload)>limit or
                hashlib.sha256(payload).hexdigest()!=digest or
                (ext==".png" and len(payload)!=row["source_png_bytes"])):
            raise ValueError("original NLM source sha256/length mismatch; nothing written")
        # Exclusive create avoids both overwriting existing files and silently
        # accepting a concurrent replacement by another process.
        with target.open("xb") as output:
            output.write(payload)
        total_new+=1
    return total_new,reused


def plan(bundle, review, centre_ids=None):
    validate_series_bundle(bundle)
    if review.get("kind")!="NLM_CT_ANATOMICAL_REVIEW_PACKET":
        raise ValueError("invalid source review packet")
    observed=sorted({p["source_id"] for p in review["observations"]})
    if not observed:
        raise ValueError("no pinned original pelvic hypotheses to inspect")
    selected=observed if centre_ids is None else centre_ids
    if not selected or len(set(selected))!=len(selected):
        raise ValueError("no repeated or empty source selection")
    groups=[]
    pinned={}
    for sid in selected:
        group,rows=selected_three_neighbours(bundle,review,sid)
        groups.append((group,sid,rows))
        for row in rows:
            if row["source_id"] in pinned and pinned[row["source_id"]]!=row:
                raise ValueError("inconsistent shared source CT identity")
            pinned[row["source_id"]]=row
    return groups,pinned


def make_index(evidence, destination):
    """Self-contained local file index; no scripts/network access required."""
    if not evidence:
        raise ValueError("no CT inspection plates")
    items=[]
    for plate in evidence:
        sid=plate["source_id"]
        if ALLOWED_ID.fullmatch(sid) is None:
            raise ValueError("unverified local CT plate identifier")
        items.append(
            '<li><a href="'+escape(sid+"_source_review.svg",quote=True)+'">'
            +escape(sid)+" — group "+str(plate["group"])+"</a> — "+
            str(plate["candidate_points"])+" original unverified point(s) | "+
            '<a href="'+escape(sid+"_tentative_review.html",quote=True)+'">'+
            'PRIVATE tentative correction/rejection form</a></li>')
    html='''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Home Gym PT — PRIVATE Original CT Anatomical Review</title>
<style>body{font:16px/1.6 system-ui,Arial,sans-serif;max-width:900px;margin:30px auto;
padding:0 20px;background:#141821;color:#f3f4f6}a{color:#93c5fd}
li{margin:12px 0}.warning{border-left:4px solid #eab308;padding:12px;background:#2b2d32}
code{color:#f1f5f9}</style></head><body>
<h1>PRIVATE Original CT Anatomical Review</h1>
<p class="warning"><strong>Not validated anatomy.</strong> Source points are
unverified image hypotheses, not accepted bones. No canonical skeleton change,
registration or pelvic landmark approval is authorised by these pictures.</p>
<p>The links open three neighbouring original NLM CT source slices, displayed
in soft-tissue and bone windows, with original candidate pixels indicated.
Original scanner RAS geometry applies, but pixel-centre convention and
scanner-to-HGPT skeleton registration remain unresolved.</p>
<ul>'''+''.join(items)+'''</ul>
<p>Use each <strong>PRIVATE tentative correction/rejection form</strong> to record source-reviewed
new pixel suggestions or reject old hypotheses. Exports require offline validation
against the original 16-bit scanner data and NEVER certify a bone.</p>
<p>Source files and rendered plates are private on this computer and must remain
outside the Git repository. These images are for anatomical review only.</p>
</body></html>
'''
    out=destination/"START_HERE_private_CT_review.html"
    with out.open("x",encoding="utf-8") as f:f.write(html)
    return out


def run(bundle,cal,review,workspace,centre_ids=None,*,opener=None,source_loader=None):
    validate_series_bundle(bundle)
    validate_calibration_evidence(cal,bundle)
    raw_workspace=Path(workspace)
    if raw_workspace.is_symlink():
        raise ValueError("private workspace cannot be a symlink")
    workspace=assert_private_location(raw_workspace)
    source_dir=assert_private_location(workspace/"original_NLM_CT_sources")
    views_dir=assert_private_location(workspace/"PRIVATE_CT_VIEW")
    groups,pinned=plan(bundle,review,centre_ids)
    if views_dir.exists() and any(views_dir.iterdir()):
        raise ValueError("private output plates already exist; refuse overwrite; choose another --workspace")
    source_dir.mkdir(parents=True,exist_ok=True)
    new,reused=0,0
    for row in pinned.values():
        a,b=download_original_pinned_pair(row,source_dir,opener=opener)
        new+=a
        reused+=b
    views_dir.mkdir(parents=True,exist_ok=True)
    plates=[]
    for group,sid,rows in groups:
        # This verifier checks each original image/header hash again, after the download.
        plate,evidence=private_ct_plate(bundle,cal,review,group,sid,source_dir,
                                       loader=source_loader)
        out=views_dir/(sid+"_source_review.svg")
        side=views_dir/(sid+"_source_review.json")
        with out.open("x",encoding="utf-8") as f:f.write(plate)
        with side.open("x",encoding="utf-8") as f:
            json.dump(evidence,f,indent=2,sort_keys=True)
            f.write("\n")
        annotation=make_offline_annotation_html(plate,evidence,bundle,review,sid)
        annotation_out=views_dir/(sid+"_tentative_review.html")
        with annotation_out.open("x",encoding="utf-8") as f:f.write(annotation)
        plates.append({"group":group,"source_id":sid,
                       "candidate_points":len(evidence["points"]),
                       "svg_sha256":hashlib.sha256(plate.encode()).hexdigest(),
                       "offline_tentative_annotation":"PRIVATE source-pinned annotation; no anatomical acceptance"})
    index=make_index(plates,views_dir)
    return {
        "kind":"PRIVATE_CT_LAPTOP_REVIEW_HANDBACK_NOT_ANATOMY",
        "index_file":str(index),
        "source_directory":str(source_dir),
        "unique_pinned_source_slices":len(pinned),
        "downloaded_new_original_files":new,
        "verified_reused_original_files":reused,
        "review_plates":plates,
        "original_raw_headers_or_images_committed_to_git":False,
        "real_bony_landmarks_anatomically_verified":0,
        "canonical_promotion_allowed":False,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace",type=Path,default=DEFAULT_WORKSPACE,
                        help="PRIVATE output directory outside repository, default user's Home")
    parser.add_argument("--source-id",action="append",
                        help="optional exact original CT centre source ID; repeat if needed")
    parser.add_argument("--bundle",type=Path,default=DEFAULT_BUNDLE)
    parser.add_argument("--calibration",type=Path,default=DEFAULT_CAL)
    parser.add_argument("--review",type=Path,default=DEFAULT_REVIEW)
    parser.add_argument("--open",action="store_true",
                        help="open local generated review index in default browser")
    args=parser.parse_args()
    bundle=json.loads(args.bundle.read_text())
    cal=json.loads(args.calibration.read_text())
    review=json.loads(args.review.read_text())
    report=run(bundle,cal,review,args.workspace,args.source_id)
    print(json.dumps(report,indent=2))
    if args.open:
        webbrowser.open(Path(report["index_file"]).as_uri())


if __name__=="__main__":
    main()
