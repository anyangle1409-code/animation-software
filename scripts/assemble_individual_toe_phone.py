"""Phone review of actual neutral and explicitly posed toe-control probes."""
from pathlib import Path
import sys,json
from PIL import Image,ImageDraw,ImageFont
out=Path(sys.argv[1]);W=1400
trajectory=json.loads((out/'toe_trajectories.json').read_text())
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
f=lambda n:ImageFont.truetype(font,n)
im=Image.new('RGB',(W,3350),(19,27,37));d=ImageDraw.Draw(im)
d.text((35,25),'ORIGINAL_v1 | individual toe-control trial',font=f(40),fill='white')
d.text((35,85),'Actual mesh | unchanged source stations | separate 95-control rig',font=f(25),fill='#b2c4d8')
d.text((35,130),'UNAPPROVED: deformation fails; foot shape still rejected',font=f(28),fill='#ffc36b')
d.text((35,175),'Left-foot display extract below 160 mm; complete body retained',font=f(24),fill='#b2c4d8')
y=230
for tag,label in [('neutral','NEUTRAL | no imposed toe rotation'),
                  ('hallux_MTP_only_15deg','POSED TEST | big toe base only, +15 degrees'),
                  ('digit2_PIP_only_15deg','POSED TEST | second toe PIP only, +15 degrees')]:
    d.text((35,y),label,font=f(30),fill='white');y+=48
    panel=Image.open(out/(tag+'_three_quarter.png')).convert('RGB').resize((1330,887))
    im.paste(panel,(35,y));y+=920
d.text((35,3160),'28 new controls; 196 trajectory samples; 4 native isolation tests pass.',font=f(25),fill='#b2c4d8')
d.text((35,3210),f'Sampled motion fails: {trajectory["maximum_triangle_reversals"]} orientation reversals; floor {trajectory["minimum_any_sample_z_mm"]:.3f} mm.',font=f(25),fill='#ffc36b')
d.text((35,3260),'Foot remains 30.92 cm. No production/app rig replacement or approval.',font=f(25),fill='#ffc36b')
im.save(out/'INDIVIDUAL_TOE_TRIAL_PHONE.png')
