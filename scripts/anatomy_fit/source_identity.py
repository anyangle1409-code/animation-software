"""Group bibliographic aliases; distinct papers do not prove distinct cohorts."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def identity_groups(rows):
 parents={};tokens={}
 def root(x):
  while parents[x]!=x:x=parents[x]
  return x
 for row in rows:
  name=row.get('id')
  if not isinstance(name,str) or not name or name in parents:raise ValueError('unique nonempty source IDs required')
  parents[name]=name
  ids=[]
  doi=row.get('doi')
  if doi:
   if not isinstance(doi,str):raise ValueError('DOI must be text')
   doi=re.sub(r'^https?://(?:dx\.)?doi\.org/','',doi.strip().lower())
   if not re.fullmatch(r'10\.[^/\s]+/\S+',doi):raise ValueError('malformed DOI')
   ids.append('doi:'+doi)
  pmid=row.get('pmid')
  if pmid:
   if isinstance(pmid,bool) or not str(pmid).isdigit():raise ValueError('PMID must be digits')
   ids.append('pmid:'+str(int(pmid)))
  pmcid=row.get('pmcid')
  if pmcid:
   if not isinstance(pmcid,str) or not re.fullmatch(r'PMC\d+',pmcid.strip(),re.I):raise ValueError('PMCID must be PMC followed by digits')
   ids.append('pmcid:PMC'+str(int(pmcid.strip()[3:])))
  for token in ids:
   if token in tokens:parents[root(name)]=root(tokens[token])
   else:tokens[token]=name
 groups={}
 for name in parents:groups.setdefault(root(name),[]).append(name)
 return sorted([sorted(v) for v in groups.values()],key=lambda v:v[0])
if __name__=='__main__':
 source=ROOT/'ORIGINAL_V1_WORK/anatomy/canonical_proportion_sources_v1.json'
 rows=json.loads(source.read_text())['sources'];groups=identity_groups(rows)
 report={'schema_version':1,'status':'BIBLIOGRAPHIC_ALIAS_SCAN_ONLY','source_register':'canonical_proportion_sources_v1.json','records':len(rows),'identifier_groups':len(groups),'aliases':[g for g in groups if len(g)>1],'missing_identifier_records':[r['id'] for r in rows if not r.get('doi') and not r.get('pmid') and not r.get('pmcid')],'limitations':['Distinct groups do not establish independent subjects or cohorts.','Missing identifiers are separate placeholders, not evidence of independent replication.','Same cohort may appear in separate papers; explicit subject-provenance review remains required.']}
 (ROOT/'ORIGINAL_V1_WORK/anatomy/canonical_source_identity_review_v1.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'records':len(rows),'groups':len(groups),'aliases':report['aliases']}))
