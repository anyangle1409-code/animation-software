import json,statistics
from pathlib import Path
R=Path(r'C:\Users\Mark\Documents\animation-software\HIGH_DETAIL_MESH_WORK');ref=json.loads((R/'reports/sculpt_reference.json').read_text());a=json.loads((R/'reports/poses/dumbbell_bicep_curl_bottom_baseline.json').read_text())['meshes'][0]['positions'];j=ref['shoulders']['L'];report={}
for version,folder in [('v1','poses'),('v2','poses_v2')]:
 b=json.loads((R/f'reports/{folder}/dumbbell_bicep_curl_bottom_candidate.json').read_text())['meshes'][0]['positions'];r={}
 for label,lo,hi in [('cap',-.02,.055),('upper_shaft',-.12,-.02),('lower_shaft',-.26,-.12)]:
  ids=[i for i,p in enumerate(a) if ref['ownership'][i]['L']>=.7 and lo<=p[1]-j[1]<hi];delta=[[1000*(b[i][k]-a[i][k]) for k in range(3)]for i in ids]
  r[label]={'count':len(ids),'mean_displacement_mm':[statistics.mean(d[k] for d in delta) for k in range(3)],'z_range_mm':[min(d[2]for d in delta),max(d[2]for d in delta)]}
 report[version]=r
(R/'reports/posterior_correspondence_v2.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
