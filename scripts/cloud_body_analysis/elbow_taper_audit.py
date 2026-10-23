"""Read-only pinned W8 upper-arm surface PCA proxy; never anatomical area/ROM."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from track_rest_hotspots import Evidence, read_frame

W8_SHA="2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c"
RIG_SHA="01ef8a7cf4eab8ea8eb29d2fcb2f5cd310ce8a936062624b06868a2e38b7b677"
FRAMES=(0,6,8)
BANDS={"middle":0.55,"distal":0.95}
NOT_GRANTED=("model_motion_axes_calibrated_to_ISB","actual_anatomical_joint_centres_verified",
             "anatomical_side_mapped","native_human_ROM_limits_validated","any_bones_rotated_or_keyframed")

def controls(path):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=RIG_SHA:
        raise ValueError("pinned rig JSON member SHA256 mismatch")
    d=json.loads(raw)
    if (d.get("model")!="W8" or d.get("source_sha256")!=W8_SHA
        or d.get("original_source_unchanged") is not True or d.get("bone_count")!=77
        or d.get("status")!="BLENDER_LOCAL_BONE_AXIS_INVENTORY_ONLY_ANATOMICAL_MAPPING_NOT_APPROVED"
        or any(d.get(k) is not False for k in NOT_GRANTED)):
        raise ValueError("unverified W8 rig identity or anatomy approval")
    bones={b["name"]:b for b in d["bones"]}
    if len(bones)!=77:
        raise ValueError("duplicate/missing rig bones")
    out={}
    for side in ("l","r"):
        b=bones["upperarm_"+side]
        head=np.asarray(b["rest_head_body_local_m"],dtype=float)
        tail=np.asarray(b["rest_tail_body_local_m"],dtype=float)
        if head.shape!=(3,) or tail.shape!=(3,) or not np.isfinite([*head,*tail]).all():
            raise ValueError("invalid authored upper-arm rest control")
        if not 0.1<float(np.linalg.norm(tail-head))<0.6:
            raise ValueError("unexpected upper-arm control span")
        out[side]=(head,tail)
    return out

def band_ids(rest,labels,head,tail,side,fraction):
    if (side not in ("l","r") or not 0<=fraction<=1 or rest.ndim!=2
        or rest.shape[1]!=3 or labels.shape!=(len(rest),) or not np.isfinite(rest).all()):
        raise ValueError("invalid rest skin arrays or side suffix")
    vec=tail-head
    span=float(np.linalg.norm(vec))
    if not np.isfinite(span) or span<=0:
        raise ValueError("zero-length authored control")
    u=vec/span
    along=(rest-head)@u
    radial=np.linalg.norm(rest-head-along[:,None]*u,axis=1)
    label_ok=np.isin(labels,(f"upperarm_{side}",f"forearm_tw0_{side}"))
    return np.flatnonzero(label_ok & (np.abs(along/span-fraction)<=0.025) & (radial<=0.09))

def pca_spread_mm2(points):
    """3D covariance largest-two-eigenvalue square-root product, NOT section area."""
    if points.ndim!=2 or points.shape[1]!=3 or len(points)<10 or not np.isfinite(points).all():
        raise ValueError("invalid PCA points")
    eig=np.linalg.eigvalsh(np.cov(points,rowvar=False,bias=True))
    if not np.isfinite(eig).all() or eig[-2]<=0 or eig[0]<-1e-10:
        raise ValueError("degenerate PCA proxy")
    return float(np.sqrt(eig[-1]*eig[-2])*1e6)

def audit(w8,rig):
    axes=controls(rig)
    src=Evidence("W8",w8)
    try:
        diagnosis=json.loads(src.read("diagnosis.json"))
        if (diagnosis.get("model")!="W8" or diagnosis.get("source_sha256")!=W8_SHA
            or diagnosis.get("source_and_copy_unchanged") is not True
            or diagnosis.get("approved") is not False
            or diagnosis.get("anatomical_approval")!="NOT_GRANTED"):
            raise ValueError("pinned diagnostic identity or anatomy status failed")
        frames={n:read_frame(src,"W8","shoulder_press",n) for n in FRAMES}
        first=frames[0]
        signature=first["record"]["triangle_indices_sha256"]
        if len(first["rest"])!=219974:
            raise ValueError("pinned W8 vertex count changed")
        for n,f in frames.items():
            saved=next((x for x in diagnosis["paths"]["shoulder_press"]["frames"]
                        if x["sample_index"]==n),None)
            if (saved is None or saved["counts"]!=f["record"]["counts"]
                or saved["triangle_indices_sha256"]!=signature
                or f["record"]["triangle_indices_sha256"]!=signature
                or not np.array_equal(f["tri"],first["tri"])
                or not np.array_equal(f["rest"],first["rest"])
                or not np.array_equal(f["labels"],first["labels"])):
                raise ValueError("W8 rest triangle/vertex/label frame identity changed")
        sides={}
        for side,(head,tail) in axes.items():
            ids={name:band_ids(first["rest"],first["labels"],head,tail,side,fraction)
                 for name,fraction in BANDS.items()}
            if any(len(x)<10 for x in ids.values()):
                raise ValueError("too few fixed skin IDs for PCA")
            def measures(vertices):
                s={name:pca_spread_mm2(vertices[sel]) for name,sel in ids.items()}
                return {"spread_product_mm2_proxy":{k:round(v,3) for k,v in s.items()},
                        "distal_over_middle_proxy":round(s["distal"]/s["middle"],5)}
            sides[side]={
                "authored_control_head_m":head.tolist(),"authored_control_tail_m":tail.tolist(),
                "fixed_rest_skin_vertex_counts":{k:len(v) for k,v in ids.items()},
                "rest":measures(first["rest"]),
                "posed_press":{str(n):{**measures(f["pose"]),"failing_native_counts":f["record"]["counts"]}
                              for n,f in frames.items()}}
        return {"status":"W8_READ_ONLY_PCA_PROXY_ONLY_ANATOMY_NOT_APPROVED",
                "model":"W8","source_sha256":W8_SHA,"rig_member_sha256":RIG_SHA,
                "native_source_runs":[39937882229,40029398965],
                "triangle_indices_sha256":signature,
                "rest_skin_vertex_ids_stable":True,"actual_elbow_centre_verified":False,
                "anatomical_side_verified":False,"isb_joint_axes_verified":False,
                "skin_deformation_approved":False,"human_rom_limits_validated":False,
                "model_files_written":False,"sides":sides,
                "limitations":["PCA spread-product is NOT anatomical area, circumference or muscle volume",
                               "Rest control tail is NOT a verified elbow centre",
                               "Side suffix is not anatomical side calibration",
                               "Press samples 0/6/8 do not test elbow curl or forearm pronation",
                               "No model correction or movement approval; ROM means are not limits"]}
    finally:
        src.close()

def markdown(report):
    lines=["# W8 elbow PCA read-only audit","",
           "**ANATOMY NOT APPROVED.** Spread-product proxy is not circumference or section area.","",
           "| Suffix | Rest distal/mid | Press 0 | Press 6 | Press 8 |",
           "|---|---:|---:|---:|---:|"]
    for side,entry in report["sides"].items():
        p=entry["posed_press"]
        lines.append(f"| {side} | {entry['rest']['distal_over_middle_proxy']:.5f} | "+
                     " | ".join(f"{p[str(n)]['distal_over_middle_proxy']:.5f}" for n in FRAMES)+" |")
    lines+=["","Fixed rest skin IDs; actual elbow centre/ISB axes and left/right anatomy unverified.",
            "No source files saved; press deformation still fails; no human ROM clamps.",""]
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--w8",required=True,type=Path)
    p.add_argument("--rig",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    report=audit(a.w8,a.rig)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"w8_elbow_taper_pca_proxy.json").write_text(json.dumps(report,indent=2)+"\n")
    (a.out/"w8_elbow_taper_pca_proxy.md").write_text(markdown(report))
    print(report["status"],{s:x["rest"]["distal_over_middle_proxy"] for s,x in report["sides"].items()})

if __name__=="__main__":
    main()
