"""Build a generic candidate review contact sheet from rendered PNGs."""

from __future__ import annotations
import argparse
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]

def sheet(destination,items,columns=3,cell=(420,490)):
    items=[(label,path) for label,path in items if path.is_file()]
    if not items:
        return False
    w,h=cell;rows=(len(items)+columns-1)//columns
    out=Image.new("RGB",(columns*w,rows*h),"white");draw=ImageDraw.Draw(out)
    for i,(label,path) in enumerate(items):
        im=Image.open(path);im.thumbnail((w-12,h-42))
        x=(i%columns)*w;y=(i//columns)*h
        out.paste(im,(x+(w-im.width)//2,y+30));draw.text((x+8,y+8),label,fill="black")
    out.save(destination,quality=90)
    return True

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--version",required=True);args=ap.parse_args()
    r=ROOT/f"renders_{args.version}";r.mkdir(exist_ok=True)
    anatomy=[
      ("Curl Bottom front",r/"dumbbell_bicep_curl_bottom_candidate_front.png"),
      ("Curl Bottom side",r/"dumbbell_bicep_curl_bottom_candidate_side.png"),
      ("Curl Bottom 3/4",r/"dumbbell_bicep_curl_bottom_candidate_three_quarter.png"),
      ("Curl Bottom back",r/"dumbbell_bicep_curl_bottom_candidate_back.png"),
      ("Squat peak",r/"air_squat_peak_candidate_three_quarter.png"),
      ("Curl peak",r/"dumbbell_bicep_curl_peak_candidate_three_quarter.png"),
      ("Press peak",r/"dumbbell_shoulder_press_peak_candidate_three_quarter.png"),
      ("Pull-up peak",r/"pull_up_peak_candidate_three_quarter.png"),
      ("Push-up peak",r/"push_up_peak_candidate_three_quarter.png"),
    ]
    details=[
      ("Curl hand",r/"dumbbell_bicep_curl_bottom_candidate_hand.png"),
      ("Push-up hand",r/"push_up_bottom_candidate_hand.png"),
      ("Pull-up hand",r/"pull_up_peak_candidate_hand.png"),
      ("Squat knee front",r/"air_squat_peak_candidate_knee_front.png"),
      ("Squat knee side",r/"air_squat_peak_candidate_knee_side.png"),
      ("Squat knee 3/4",r/"air_squat_peak_candidate_knee_three_quarter.png"),
      ("Press shoulder side",r/"dumbbell_shoulder_press_peak_candidate_shoulder_side.png"),
      ("Press shoulder 3/4",r/"dumbbell_shoulder_press_peak_candidate_shoulder_three_quarter.png"),
      ("Pull-up shoulder 3/4",r/"pull_up_peak_candidate_shoulder_three_quarter.png"),
    ]
    made=[]
    if sheet(r/f"{args.version.upper()}_ANATOMY_AND_EXERCISES.jpg",anatomy):
        made.append(str(r/f"{args.version.upper()}_ANATOMY_AND_EXERCISES.jpg"))
    if sheet(r/f"{args.version.upper()}_DETAILS.jpg",details):
        made.append(str(r/f"{args.version.upper()}_DETAILS.jpg"))
    print("\n".join(made) if made else "No matching renders found")

if __name__=="__main__":
    main()
