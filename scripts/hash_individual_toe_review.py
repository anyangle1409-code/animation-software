"""Hash final saved review exports, excluding the hash manifest itself."""
import sys,json,hashlib
from pathlib import Path
out=Path(sys.argv[1])
names=['INDIVIDUAL_TOE_TRIAL_PHONE.png','neutral_side.png','neutral_three_quarter.png',
 'hallux_MTP_only_15deg_side.png','hallux_MTP_only_15deg_three_quarter.png',
 'digit2_PIP_only_15deg_side.png','digit2_PIP_only_15deg_three_quarter.png',
 'HomeGymPT_ORIGINAL_v1_INDIVIDUAL_TOE_TRIAL.blend','individual_toe_trial.json','toe_trajectories.json']
report={name:{'sha256':hashlib.sha256((out/name).read_bytes()).hexdigest(),'bytes':(out/name).stat().st_size} for name in names}
(out/'export_hashes.json').write_text(json.dumps(report,indent=2)+'\n')
print('FINAL_EXPORTS_HASHED',len(report))
