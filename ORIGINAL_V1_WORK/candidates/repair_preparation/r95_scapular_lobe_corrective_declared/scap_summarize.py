import json, sys
SP = r"C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
tag = sys.argv[1]
d = json.load(open(SP + r"\scmp_%s_P3B1.json" % tag))
print("vs P3B1 (strict, with the flexion keys present):")
for r in d["regressions"]:
    print("  ", r["name"], r["region"], r["metric"], r["baseline"], "->", r["candidate"])
d = json.load(open(SP + r"\scmp_%s_r93.json" % tag))
print("vs r93:")
for r in d["regressions"]:
    print("  ", r["name"], r["region"], r["metric"], r["baseline"], "->", r["candidate"])
r = {x["pose"]: x for x in json.load(open(SP + r"\spt_%s\pose_test_report.json" % tag))}
print("SI", {p: r[p]["self_intersecting_face_pairs"] for p in ("press_top", "press_top_rhythm", "pullup_hang", "pullup_hang_rhythm", "squat_bottom", "pushup_bottom")}, "(r93 30/24/0/0/80/162; P3B1 95/54/4/0/108/158)")
print("press_top p99", r["press_top"]["edge_ratio_p99"], "vol", r["press_top"]["volume_ratio"], "| pullup_top torso min", r["pullup_top"]["by_region"]["torso"]["min_ratio"])
