#!/usr/bin/env python3
"""Noncanonical offline *tentative* CT axial contour capture and physical area.

Uses three existing verified original-source CT slices in the local review
plate. Original PNG/header bytes never enter Git. User-drawn contours do NOT
certify named bones or any joint. The rechecker recomputes local contour areas
from original scanner FOV geometry and samples unaltered 16-bit source HU.
"""
import argparse
import json
import math
from pathlib import Path
import re

from ct_pelvis_window_geometry import assert_private_location
from nlm_ct_provisional_surface import GRID, _private_source_slice
from nlm_ct_raw_png_calibration import validate_calibration_evidence
from pelvic_ct_series_manifest import validate_series_bundle

KIND="PRIVATE_ORIGINAL_CT_TENTATIVE_AXIAL_CONTOUR_REVIEW"
LABELS=(
    "unknown_dense_structure",
    "candidate_right_femoral_head",
    "candidate_left_femoral_head",
    "candidate_right_acetabulum",
    "candidate_left_acetabulum",
    "candidate_right_ilium",
    "candidate_left_ilium",
    "candidate_sacrum",
    "candidate_pubic_region",
)
ALIAS=re.compile(r"^[A-Za-z0-9_-]{2,32}$")


def pinned_three(bundle,evidence):
    validate_series_bundle(bundle)
    ids=evidence.get("source_ids")
    if not isinstance(ids,list) or len(ids)!=3 or len(set(ids))!=3:
        raise ValueError("source three-slice review has invalid original image set")
    for group,series in enumerate(bundle["series"],1):
        rows=series["slices"]
        for i in range(1,len(rows)-1):
            trio=rows[i-1:i+2]
            if [r["source_id"] for r in trio]==ids:
                if (evidence.get("source_sha256")!=
                        [r["source_png_sha256"] for r in trio] or
                        evidence.get("canonical_promotion_allowed") is not False):
                    raise ValueError("original source three-slice provenance changed")
                return group,trio
    raise ValueError("CT slice trio cannot span groups or is not consecutive")


def contour_packet(bundle,evidence):
    group,rows=pinned_three(bundle,evidence)
    return {
        "schema_version":1,
        "kind":KIND,
        "source_group":group,
        "source_planes":[{
            "source_id":r["source_id"],
            "source_png_sha256":r["source_png_sha256"],
            "source_header_sha256":r["source_header_sha256"],
            "scanner_S_mm":r["scanner_centre_RAS_mm"][2],
        } for r in rows],
        "reviewer_alias":"",
        "outlines":[],
        "pixel_centre_origin_verified":False,
        "scanner_to_HGPT_transform_verified":False,
        "bone_identity_verified":False,
        "canonical_promotion_allowed":False,
    }


def offline_contour_html(plate,bundle,evidence):
    packet=contour_packet(bundle,evidence)
    if (not plate.lstrip().startswith('<svg ') or
            plate.count('data:image/png;base64,')!=6 or
            "<script" in plate.lower() or "<foreignobject" in plate.lower()):
        raise ValueError("review image must be original pinned static CT SVG")
    safe=json.dumps(packet,separators=(",",":")).replace("<","\\u003c").replace("&","\\u0026")
    script='''"use strict";
const packet=JSON.parse(document.getElementById("source-data").textContent);
const svg=document.querySelector("#view svg"),ns="http://www.w3.org/2000/svg";
const overlay=document.createElementNS(ns,"g");
overlay.setAttribute("pointer-events","none");svg.appendChild(overlay);
const status=document.getElementById("status");
const label=document.getElementById("structure");
const note=document.getElementById("note");
let draft=null;
function redraw(){
 while(overlay.firstChild)overlay.removeChild(overlay.firstChild);
 const sequences=packet.outlines.concat(draft?[draft]:[]);
 for(const outline of sequences){
  const verts=outline.vertices;
  if(!verts.length)continue;
  const pos=packet.source_planes.findIndex(x=>x.source_id===outline.source_id);
  if(pos<0)continue;
  for(const ybase of [125,670]){
   const shape=document.createElementNS(ns,outline.closed?"polygon":"polyline");
   const coords=verts.map(v=>(32+pos*554+v.column+0.5)+","+
                                (ybase+v.row+0.5)).join(" ");
   shape.setAttribute("points",coords);
   shape.setAttribute("fill",outline.closed?"#00ffff30":"none");
   shape.setAttribute("stroke",outline.closed?"#00ffff":"#ffff00");
   shape.setAttribute("stroke-width","2.5");
   overlay.appendChild(shape);
  }
 }
}
function tell(s){status.textContent=s;}
svg.addEventListener("click",e=>{
 const matrix=svg.getScreenCTM();if(!matrix)return;
 const pos=svg.createSVGPoint();pos.x=e.clientX;pos.y=e.clientY;
 const xy=pos.matrixTransform(matrix.inverse());
 const k=Math.floor((xy.x-32)/554);
 const col=Math.floor(xy.x-(32+k*554));
 const ybase=xy.y>=125&&xy.y<637?125:xy.y>=670&&xy.y<1182?670:null;
 if(k<0||k>=3||ybase===null||col<0||col>=512)return;
 const row=Math.floor(xy.y-ybase);
 if(row<0||row>=512)return;
 const sid=packet.source_planes[k].source_id;
 if(draft&&draft.source_id!==sid){
  tell("Finish or discard this outline before switching source planes.");return;
 }
 if(!draft)draft={source_id:sid,label:label.value,
   vertices:[],note:"",closed:false};
 if(draft.vertices.length>=240){tell("Maximum 240 points per outline.");return;}
 draft.vertices.push({row,column:col});
 tell("Tentative outline "+draft.label+": "+draft.vertices.length+" points on "+sid);
 redraw();
});
document.getElementById("undo").onclick=()=>{
 if(draft&&draft.vertices.length)draft.vertices.pop();
 redraw();tell("Last tentative outline point undone.");
};
document.getElementById("discard").onclick=()=>{
 draft=null;redraw();tell("Unsaved tentative outline discarded.");
};
document.getElementById("finish").onclick=()=>{
 if(!draft||draft.vertices.length<3){tell("At least 3 distinct pixels needed.");return;}
 if(packet.outlines.length>=50){tell("Maximum 50 outlines per review export.");return;}
 draft.closed=true;draft.note=note.value.slice(0,2000);
 draft.id="outline_"+String(packet.outlines.length+1);
 packet.outlines.push(draft);draft=null;note.value="";
 redraw();tell("Tentative outline captured (NOT accepted bone). "+packet.outlines.length+" contours.");
};
document.getElementById("export").onclick=()=>{
 const who=document.getElementById("reviewer").value.trim();
 if(!/^[A-Za-z0-9_-]{2,32}$/.test(who)){
  tell("Use a 2-32 character reviewer alias.");return;
 }
 if(draft){tell("Finish or discard the in-progress outline first.");return;}
 if(!packet.outlines.length){tell("No tentative outlines to export.");return;}
 packet.reviewer_alias=who;
 const u=URL.createObjectURL(new Blob([JSON.stringify(packet,null,2)],
   {type:"application/json"}));
 const a=document.createElement("a");a.href=u;
 a.download=packet.source_planes[1].source_id+"_tentative_contours.json";
 document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(u);
 tell("Private candidate contours exported; exact original-source recheck is still required. NOTHING APPROVED.");
};
tell("Choose an uncertain candidate structure. Click image pixels; finish each polygon.");'''
    choices=''.join('<option value="'+label+'">'+label.replace("_"," ")+'</option>' for label in LABELS)
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'none'; object-src 'none'; base-uri 'none'">
<title>Private CT outline capture — NOT accepted bone geometry</title>
<style>body{margin:0;background:#111827;color:#f9fafb;font:15px/1.5 system-ui,sans-serif}
header{background:#1f2937;padding:12px 20px;position:sticky;top:0;z-index:2}
h1{margin:0;font-size:20px}p{margin:3px 0;color:#fcd34d}
select,input,button,textarea{background:white;color:#111827;padding:6px;margin:4px}
#view svg{width:100%;height:auto;max-width:1692px;display:block;margin:auto}</style></head>
<body><header><h1>Original CT — PRIVATE, TENTATIVE outlines only</h1>
<p>Click individual pixels on any original CT plane (three neighbouring slices, two HU
windows). Close one polyline before selecting another plane. Source anatomy
is NOT certified and contours MUST NOT be used as production bone surfaces.</p>
<label>Reviewer alias <input id="reviewer" placeholder="reviewer01" maxlength="32"></label>
<label>Candidate feature <select id="structure">'''+choices+'''</select></label>
<label>Notes <textarea id="note" rows="2" maxlength="2000"></textarea></label>
<button id="undo" type="button">Undo vertex</button>
<button id="discard" type="button">Discard draft</button>
<button id="finish" type="button">Finish tentative outline</button>
<button id="export" type="button">Export private JSON</button>
<p id="status" role="status"></p></header>
<section id="view">'''+plate+'''</section>
<script type="application/json" id="source-data">'''+safe+'''</script>
<script>'''+script+'''</script></body></html>
'''


def _cross(a,b,c):
    return ((b["column"]-a["column"])*(c["row"]-a["row"])
            -(b["row"]-a["row"])*(c["column"]-a["column"]))


def _intersection(a,b,c,d):
    """Reject strict crossing or collinear non-adjacent shared geometry."""
    # Every vertex must be distinct, so zero-length edges already excluded.
    oa,ob=_cross(a,b,c),_cross(a,b,d)
    oc,od=_cross(c,d,a),_cross(c,d,b)
    if oa==0 and min(a["column"],b["column"])<=c["column"]<=max(a["column"],b["column"]) and min(a["row"],b["row"])<=c["row"]<=max(a["row"],b["row"]):return True
    if ob==0 and min(a["column"],b["column"])<=d["column"]<=max(a["column"],b["column"]) and min(a["row"],b["row"])<=d["row"]<=max(a["row"],b["row"]):return True
    if oc==0 and min(c["column"],d["column"])<=a["column"]<=max(c["column"],d["column"]) and min(c["row"],d["row"])<=a["row"]<=max(c["row"],d["row"]):return True
    if od==0 and min(c["column"],d["column"])<=b["column"]<=max(c["column"],d["column"]) and min(c["row"],d["row"])<=b["row"]<=max(c["row"],d["row"]):return True
    return (oa*ob<0 and oc*od<0)


def validate_polygon(vertices):
    if not isinstance(vertices,list) or not 3<=len(vertices)<=240:
        raise ValueError("contour must contain 3-240 vertices")
    points=[]
    seen=set()
    for v in vertices:
        if (not isinstance(v,dict) or set(v)!={"row","column"} or
                any(type(v[k]) is not int or not 0<=v[k]<GRID for k in ("row","column"))):
            raise ValueError("contour source pixel out of range")
        key=(v["row"],v["column"])
        if key in seen:raise ValueError("contour has repeated source pixels")
        seen.add(key);points.append(v)
    n=len(points)
    for i in range(n):
        a,b=points[i],points[(i+1)%n]
        for j in range(i+1,n):
            if j==i+1 or (i==0 and j==n-1):continue
            if _intersection(a,b,points[j],points[(j+1)%n]):
                raise ValueError("self-intersecting source contour is not a defensible boundary")
    double_area=sum(
        a["column"]*b["row"]-b["column"]*a["row"]
        for a,b in zip(points,points[1:]+points[:1]))
    if abs(double_area)<2:
        raise ValueError("degenerate source contour has no meaningful enclosed area")
    return abs(double_area)/2


def validate_contour_packet(packet,bundle,template):
    valid=contour_packet(bundle,template)
    for key in ("schema_version","kind","source_group","source_planes",
                "pixel_centre_origin_verified","scanner_to_HGPT_transform_verified",
                "bone_identity_verified","canonical_promotion_allowed"):
        if packet.get(key)!=valid[key]:
            raise ValueError("source provenance or noncanonical permission changed")
    alias=packet.get("reviewer_alias")
    if not isinstance(alias,str) or ALIAS.fullmatch(alias) is None:
        raise ValueError("invalid local reviewer alias")
    outlines=packet.get("outlines")
    if not isinstance(outlines,list) or not 1<=len(outlines)<=50:
        raise ValueError("review export must contain 1-50 outlines")
    ids={s["source_id"] for s in valid["source_planes"]}
    for i,p in enumerate(outlines,1):
        if (not isinstance(p,dict) or p.get("id")!="outline_"+str(i)
                or p.get("source_id") not in ids or p.get("label") not in LABELS
                or p.get("closed") is not True or
                not isinstance(p.get("note"),str) or len(p["note"])>2000):
            raise ValueError("invalid or false-identity anatomical outline")
        validate_polygon(p.get("vertices"))
        if p.get("canonical_promotion_allowed",False) is not False:
            raise ValueError("attempted anatomical promotion by outline")
    return valid


def original_source_contour_metrics(packet,bundle,cal,template,source_dir,*,loader=None):
    validate_series_bundle(bundle)
    validate_calibration_evidence(cal,bundle)
    original=validate_contour_packet(packet,bundle,template)
    if loader is None:loader=_private_source_slice
    rows={r["source_id"]:r for s in bundle["series"] for r in s["slices"]}
    source_dir=assert_private_location(source_dir)
    cache={}
    stats=[]
    for p in packet["outlines"]:
        sid=p["source_id"];row=rows[sid]
        if sid not in cache:
            geometry,pixels=loader(source_dir,row)
            if (len(pixels)!=GRID*GRID or
                    abs(geometry["scanner_S_mm"]-row["scanner_centre_RAS_mm"][2])>1e-6):
                raise ValueError("source GE CT header mismatch during contour validation")
            cache[sid]=(geometry,pixels)
        geometry,pixels=cache[sid]
        px_area=validate_polygon(p["vertices"])
        tl,tr,br=(geometry[k] for k in (
            "plane_TL_RAS_mm","plane_TR_RAS_mm","plane_BR_RAS_mm"))
        width=math.dist(tl,tr)/GRID;height=math.dist(tr,br)/GRID
        if not (.1<width<3 and .1<height<3):
            raise ValueError("scanner geometric pixel spacing outside source expectations")
        hu=[pixels[v["row"]*GRID+v["column"]]-1024 for v in p["vertices"]]
        stats.append({
            "outline_id":p["id"],
            "unverified_named_candidate":p["label"],
            "source_id":sid,
            "scanner_S_mm":row["scanner_centre_RAS_mm"][2],
            "polygon_area_pixel_squared":round(px_area,3),
            "physical_in_plane_area_mm_squared":round(px_area*width*height,3),
            "scanner_in_plane_mm_per_pixel_row_column":[round(height,7),round(width,7)],
            "vertex_original_source_HU_min_max":[min(hu),max(hu)],
            "vertex_count":len(hu),
            "scanner_pixel_centre_origin_verified":False,
            "actual_bone_boundary_or_surface_verified":False,
        })
    return {
        "kind":"PRIVATE_ORIGINAL_CT_PROVISIONAL_CONTOUR_METRICS_NOT_BONE_IDENTITY",
        "source_ids":[x["source_id"] for x in original["source_planes"]],
        "original_scanner_frame":"GE_ORIGINAL_RAS_MM",
        "reviewer_alias":packet["reviewer_alias"],
        "contours":stats,
        "complete_named_bone_3D_surface_verified":False,
        "human_anatomical_reviewer_approved":False,
        "canonical_promotion_allowed":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--private-export",required=True)
    p.add_argument("--ct-dir",required=True)
    p.add_argument("--bundle",required=True)
    p.add_argument("--calibration",required=True)
    p.add_argument("--original-plate-sidecar",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    out=assert_private_location(args.out)
    if out.exists() or out.suffix.lower()!=".json":
        raise ValueError("refuse overwrite private CT contour report")
    report=original_source_contour_metrics(
        json.loads(Path(args.private_export).read_text()),
        json.loads(Path(args.bundle).read_text()),
        json.loads(Path(args.calibration).read_text()),
        json.loads(Path(args.original_plate_sidecar).read_text()),
        args.ct_dir)
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("x",encoding="utf8") as f:json.dump(report,f,indent=2);f.write("\n")
    print(json.dumps({"source_ids":report["source_ids"],
                      "tentative_contour_areas_mm2":[c["physical_in_plane_area_mm_squared"]
                      for c in report["contours"]],
                      "canonical_promotion_allowed":False},indent=2))


if __name__=="__main__":
    main()
