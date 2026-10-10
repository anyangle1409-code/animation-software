#!/usr/bin/env python3
"""Offline CT review annotations: exact source pins, tentative ONLY, no approval.

Embeds a previously verified three-slice private SVG in a standalone HTML page
with clickable source pixel coordinates. Exports proposed corrections/rejections
as local JSON, then independently rechecks marked pixels against the original
16-bit SHA-pinned CT source. No server, external JavaScript or Python package.
"""
import argparse
from html import escape
import json
from pathlib import Path
import re

from ct_pelvis_window_geometry import assert_private_location
from nlm_ct_provisional_surface import GRID, _private_source_slice
from nlm_ct_raw_png_calibration import validate_calibration_evidence
from pelvic_ct_series_manifest import validate_series_bundle

SCHEMA="PRIVATE_ORIGINAL_CT_TENTATIVE_REVIEWER_PIXEL_ANNOTATIONS"
VALID=("unreviewed","rejected_original_point","tentative_reviewer_pixel")
ALIAS=re.compile(r"^[A-Za-z0-9_-]{2,32}$")


def records(bundle,review,centre_id):
    validate_series_bundle(bundle)
    if review.get("kind")!="NLM_CT_ANATOMICAL_REVIEW_PACKET":
        raise ValueError("original CT observation packet invalid")
    hits=[(g,r) for g,s in enumerate(bundle["series"],1) for r in s["slices"]
          if r["source_id"]==centre_id]
    if len(hits)!=1:
        raise ValueError("original CT plane must occur exactly once")
    group,row=hits[0]
    out=[]
    seen=set()
    for p in review["observations"]:
        if p["source_id"]!=centre_id:continue
        if (p["observation_id"] in seen or
                p["source_png_sha256"]!=row["source_png_sha256"] or
                p["source_header_sha256"]!=row["source_header_sha256"] or
                abs(p["scanner_S_mm"]-row["scanner_centre_RAS_mm"][2])>1e-6):
            raise ValueError("prior source-point identity/hash/position mismatch")
        seen.add(p["observation_id"])
        old=p["pixel"]
        if any(type(old[k]) is not int or not 0<=old[k]<GRID for k in ("row","column")):
            raise ValueError("original source-pixel bounds invalid")
        out.append({
            "observation_id":p["observation_id"],
            "source_id":centre_id,
            "original_pixel":{"row":old["row"],"column":old["column"]},
            "original_source_png_sha256":row["source_png_sha256"],
            "original_source_header_sha256":row["source_header_sha256"],
            "source_scanner_S_mm":row["scanner_centre_RAS_mm"][2],
            "review_status":"unreviewed",
            "tentative_pixel":None,
            "evidence_note":"",
        })
    if not out:raise ValueError("no original candidate points on CT plane")
    return group,row,out


def packet_template(bundle,review,centre_id):
    group,row,pts=records(bundle,review,centre_id)
    return {
        "schema_version":1,"kind":SCHEMA,
        "source_group":group,"centre_source_id":centre_id,
        "source_png_sha256":row["source_png_sha256"],
        "source_header_sha256":row["source_header_sha256"],
        "source_scanner_S_mm":row["scanner_centre_RAS_mm"][2],
        "original_scanner_frame":"GE_ORIGINAL_RAS_MM",
        "reviewer_alias":"",
        "observations":pts,
        "scanner_pixel_origin_verified":False,
        "scanner_to_HGPT_skeleton_registered":False,
        "bone_identity_independently_verified":False,
        "canonical_promotion_allowed":False,
    }


def make_offline_annotation_html(svg,evidence,bundle,review,centre_id):
    """Only generated pinned SVGs allowed; original images never copied to Git."""
    packet=packet_template(bundle,review,centre_id)
    group=packet["source_group"]
    frames=bundle["series"][group-1]["slices"]
    index=next(i for i,row in enumerate(frames) if row["source_id"]==centre_id)
    if index==0 or index==len(frames)-1:
        raise ValueError("three-slice plate crosses scanner acquisition boundary")
    selected=frames[index-1:index+2]
    if (evidence.get("source_ids")!=[r["source_id"] for r in selected] or
            evidence.get("source_sha256")!=[r["source_png_sha256"] for r in selected] or
            evidence.get("canonical_promotion_allowed") is not False or
            len(evidence.get("points",[]))!=len(packet["observations"])):
        raise ValueError("private SVG provenance disagrees with original scan")
    for point,old in zip(evidence["points"],packet["observations"]):
        if (point["id"]!=old["observation_id"] or
                point["original_pixel_row"]!=old["original_pixel"]["row"] or
                point["original_pixel_column"]!=old["original_pixel"]["column"]):
            raise ValueError("original review pixel moved or reordered")
    if (not svg.lstrip().startswith('<svg ') or
            svg.count('data:image/png;base64,')!=6 or
            '<script' in svg.lower() or '<foreignobject' in svg.lower()):
        raise ValueError("unrecognised source CT plate or executable SVG")
    safe_json=json.dumps(packet,separators=(",",":")).replace("<","\\u003c").replace("&","\\u0026")
    script='''"use strict";
const packet=JSON.parse(document.getElementById("source-packet").textContent);
const select=document.getElementById("candidate"), decision=document.getElementById("action");
const note=document.getElementById("note"), status=document.getElementById("status");
const svg=document.querySelector("#view svg");
const ns="http://www.w3.org/2000/svg";
const layer=document.createElementNS(ns,"g");layer.setAttribute("pointer-events","none");
svg.appendChild(layer);
let chosen=0;
packet.observations.forEach((rec,i)=>{
 const opt=document.createElement("option");opt.value=String(i);
 opt.textContent=rec.observation_id;select.appendChild(opt);
});
function redraw(){
 while(layer.firstChild)layer.removeChild(layer.firstChild);
 packet.observations.forEach((rec,i)=>{
  if(!rec.tentative_pixel)return;
  for(const baseY of [125,670]){
   const c=document.createElementNS(ns,"circle");
   const attrs={cx:586+rec.tentative_pixel.column+0.5,
    cy:baseY+rec.tentative_pixel.row+0.5,r:8,fill:"none",
    stroke:i===chosen?"#00ffff":"#ffff00","stroke-width":2.8};
   for(const [k,v] of Object.entries(attrs))c.setAttribute(k,String(v));
   layer.appendChild(c);
  }
 });
}
function render(){
 const p=packet.observations[chosen];decision.value=p.review_status;
 note.value=p.evidence_note;
 status.textContent="Original (unchanged) pixel: row "+p.original_pixel.row+
 ", column "+p.original_pixel.column+(p.tentative_pixel?
 " | TENTATIVE NEW row "+p.tentative_pixel.row+" col "+p.tentative_pixel.column:"")+
 ". NOT CERTIFIED AS ANATOMICAL BONE.";redraw();
}
select.addEventListener("change",()=>{chosen=Number(select.value);render();});
decision.addEventListener("change",()=>{
 const p=packet.observations[chosen];p.review_status=decision.value;
 if(p.review_status!=="tentative_reviewer_pixel")p.tentative_pixel=null;
 render();
});
note.addEventListener("input",()=>{
 packet.observations[chosen].evidence_note=note.value.slice(0,2000);
});
svg.addEventListener("click",e=>{
 if(packet.observations[chosen].review_status!=="tentative_reviewer_pixel")return;
 const matrix=svg.getScreenCTM();if(!matrix)return;
 const pt=svg.createSVGPoint();pt.x=e.clientX;pt.y=e.clientY;
 const p=pt.matrixTransform(matrix.inverse());
 const offsetY=p.y>=125&&p.y<637?125:p.y>=670&&p.y<1182?670:null;
 if(offsetY===null||p.x<586||p.x>=1098)return;
 const r=Math.floor(p.y-offsetY),c=Math.floor(p.x-586);
 if(r<0||r>=512||c<0||c>=512)return;
 packet.observations[chosen].tentative_pixel={row:r,column:c};render();
});
document.getElementById("save").addEventListener("click",()=>{
 const alias=document.getElementById("reviewer").value.trim();
 if(!/^[A-Za-z0-9_-]{2,32}$/.test(alias)){
  status.textContent="Use a 2-32 character reviewer alias (letters/digits/-/_).";return;
 }
 if(packet.observations.some(p=>p.review_status==="tentative_reviewer_pixel"&&!p.tentative_pixel)){
  status.textContent="Click the centre CT image for each tentative pixel.";return;
 }
 packet.reviewer_alias=alias;
 const url=URL.createObjectURL(new Blob([JSON.stringify(packet,null,2)],{type:"application/json"}));
 const a=document.createElement("a");a.href=url;
 a.download=packet.centre_source_id+"_tentative_pixels.json";
 document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url);
 status.textContent="LOCAL export only. Revalidate against pinned original source before further use. No bone accepted.";
});
render();'''
    # safe JSON in inert script tag, no markup break-outs
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; object-src 'none'; connect-src 'none'; base-uri 'none'">
<title>Private CT review — tentative only</title><style>
body{background:#111827;color:#f8fafc;font:15px/1.5 system-ui,sans-serif;margin:0}
.header{position:sticky;top:0;z-index:3;background:#1f2937;padding:14px 22px}
h1{font-size:20px;margin:0 0 5px}p{margin:5px 0;color:#fcd34d}
input,select,textarea,button{background:#fff;color:#111;padding:5px;margin:4px}
textarea{width:min(700px,85vw)}#view svg{display:block;width:100%;height:auto;max-width:1692px;margin:auto}
button{cursor:pointer}</style></head><body><section class="header">
<h1>PRIVATE CT source correction — NEVER AN AUTOMATICALLY ACCEPTED BONE</h1>
<p>Original points remain immutable. Select an action, then click the CENTRE CT scan
to mark a tentative pixel. Export a private JSON review; no network connection or storage.</p>
<label>Reviewer alias <input id="reviewer" maxlength="32" placeholder="reviewer01"></label>
<label>Original point <select id="candidate"></select></label>
<label>Action <select id="action">
<option value="unreviewed">Unreviewed</option>
<option value="rejected_original_point">Reject original hypothesis</option>
<option value="tentative_reviewer_pixel">Tentative pixel (click centre CT image)</option>
</select></label>
<label>Source/anatomy evidence and uncertainty (not approval)
<textarea id="note" rows="2" maxlength="2000"></textarea></label>
<button id="save" type="button">Export private tentative JSON</button>
<p id="status" role="status"></p></section><section id="view">'''+svg+'''</section>
<script type="application/json" id="source-packet">'''+safe_json+'''</script>
<script>'''+script+'''</script></body></html>
'''


def validate_packet(packet,bundle,review):
    """Reject false approvals, changed provenance, bad alias, and silently moved points."""
    if not isinstance(packet,dict) or packet.get("kind")!=SCHEMA:
        raise ValueError("unknown reviewer annotation packet")
    if any(packet.get(k) is not False for k in (
            "scanner_pixel_origin_verified","scanner_to_HGPT_skeleton_registered",
            "bone_identity_independently_verified","canonical_promotion_allowed")):
        raise ValueError("unverified source cannot be promoted to accepted anatomy")
    if packet.get("schema_version")!=1 or packet.get("original_scanner_frame")!="GE_ORIGINAL_RAS_MM":
        raise ValueError("unrecognized source/scanner frame")
    alias=packet.get("reviewer_alias")
    if not isinstance(alias,str) or ALIAS.fullmatch(alias) is None:
        raise ValueError("reviewer alias must be 2–32 restricted characters")
    wanted=packet_template(bundle,review,packet["centre_source_id"])
    for fixed in ("source_group","centre_source_id","source_png_sha256",
                  "source_header_sha256","source_scanner_S_mm"):
        if packet.get(fixed)!=wanted[fixed]:
            raise ValueError("review packet source SHA/scanner provenance changed")
    observations=packet.get("observations")
    if not isinstance(observations,list) or len(observations)!=len(wanted["observations"]):
        raise ValueError("review must preserve all original candidate observations")
    for got,old in zip(observations,wanted["observations"]):
        for fixed in ("observation_id","source_id","original_pixel",
                      "original_source_png_sha256","original_source_header_sha256",
                      "source_scanner_S_mm"):
            if got.get(fixed)!=old[fixed]:
                raise ValueError("original observation identity or source coordinate modified")
        decision=got.get("review_status")
        candidate=got.get("tentative_pixel")
        if decision not in VALID or not isinstance(got.get("evidence_note"),str) or len(got["evidence_note"])>2000:
            raise ValueError("invalid review status or evidence note")
        if decision=="tentative_reviewer_pixel":
            if not isinstance(candidate,dict) or set(candidate)!={"row","column"} or any(
                    type(candidate[k]) is not int or not 0<=candidate[k]<GRID
                    for k in ("row","column")):
                raise ValueError("tentative pixel out of the original source range")
        elif candidate is not None:
            raise ValueError("unreviewed/rejected observations cannot silently hold replacement pixel")
        if got.get("canonical_promotion_allowed",False) is not False:
            raise ValueError("candidate requested forbidden anatomical promotion")
    return wanted["source_group"],wanted["centre_source_id"]


def recheck_source_HU(packet,bundle,cal,review,source_dir,*,loader=None):
    validate_series_bundle(bundle)
    validate_calibration_evidence(cal,bundle)
    group,source_id=validate_packet(packet,bundle,review)
    _,row,_=records(bundle,review,source_id)
    if loader is None:loader=_private_source_slice
    geom,pixels=loader(assert_private_location(source_dir),row)
    if len(pixels)!=GRID*GRID or abs(geom["scanner_S_mm"]-row["scanner_centre_RAS_mm"][2])>1e-6:
        raise ValueError("pinned GE scanner data or pixel dimensions changed")
    entries=[]
    for item in packet["observations"]:
        a=item["original_pixel"];b=item["tentative_pixel"]
        entries.append({
            "observation_id":item["observation_id"],
            "review_status":item["review_status"],
            "source_original_pixel":a,
            "source_original_HU_confirmed":pixels[a["row"]*GRID+a["column"]]-1024,
            "tentative_pixel":b,
            "tentative_HU_confirmed_if_selected":(
                pixels[b["row"]*GRID+b["column"]]-1024 if b else None),
            "reviewer_note":item["evidence_note"],
            "automatically_accepted_as_bone":False,
        })
    return {
        "kind":"RECHECKED_PRIVATE_REVIEW_HU_TENTATIVE_NOT_BONE_APPROVAL",
        "centre_source_id":source_id,"source_group":group,
        "source_png_sha256":row["source_png_sha256"],
        "source_header_sha256":row["source_header_sha256"],
        "reviewer_alias":packet["reviewer_alias"],"observations":entries,
        "accepted_true_pelvic_bony_landmarks":0,
        "canonical_promotion_allowed":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--private-export",required=True)
    p.add_argument("--ct-dir",required=True)
    p.add_argument("--bundle",required=True)
    p.add_argument("--calibration",required=True)
    p.add_argument("--review",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    out=assert_private_location(a.out)
    if out.exists() or out.suffix.lower()!=".json":
        raise ValueError("refuse overwrite of private anatomical review")
    result=recheck_source_HU(
        json.loads(Path(a.private_export).read_text()),
        json.loads(Path(a.bundle).read_text()),
        json.loads(Path(a.calibration).read_text()),
        json.loads(Path(a.review).read_text()),
        a.ct_dir)
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("x",encoding="utf-8") as f:
        json.dump(result,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps({"source_id":result["centre_source_id"],
                      "statuses":[(x["observation_id"],x["review_status"],
                                   x["tentative_HU_confirmed_if_selected"]) for x in result["observations"]],
                      "canonical_promotion_allowed":False},indent=2))


if __name__=="__main__":
    main()
