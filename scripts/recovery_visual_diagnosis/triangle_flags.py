"""Triangle IDs for the existing native metric conditions; no acceptance changes."""
def flag_triangles(faces,rest_areas,areas,raw_pairs):
 if len(faces)!=len(rest_areas) or len(faces)!=len(areas):raise ValueError('Triangle correspondence changed')
 collapsed=[];stretched=[]
 for i,(a0,a) in enumerate(zip(rest_areas,areas)):
  if a0>1e-12:
   ratio=a/a0
   if ratio<0.1:collapsed.append(i)
   if ratio>2:stretched.append(i)
 sets=[set(f) for f in faces]
 pairs=sorted(set((a,b) for a,b in raw_pairs if a<b and not sets[a]&sets[b]))
 return {'collapsed':collapsed,'stretched':stretched,'intersections':pairs}

def compare_rows(rows,baseline):
 differences=[]
 if len(rows)!=len(baseline):differences.append({'field':'sample_count','current':len(rows),'baseline':len(baseline)})
 for i,(a,b) in enumerate(zip(rows,baseline)):
  for key in sorted(set(a)|set(b)):
   if a.get(key)!=b.get(key):differences.append({'sample_index':i,'field':key,'current':a.get(key),'baseline':b.get(key)})
 return differences
