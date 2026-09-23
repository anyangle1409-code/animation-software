"""Make matched-camera V6/V7 squat knee comparison for human review."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[1]
sources=root/'renders_v7_knee_retopology'/'comparison_sources'
out=root/'renders_v7_knee_retopology'/'V7_KNEE_V6_COMPARISON.jpg'
views=('front','side','three_quarter')
tile=(500,545); pad=16; head=28
sheet=Image.new('RGB',(2*tile[0]+3*pad,3*(tile[1]+head)+4*pad),'white')
draw=ImageDraw.Draw(sheet)
for row,view in enumerate(views):
    for col,(prefix,label) in enumerate((('v6','V6 baseline'),('v7','V7 review'))):
        im=Image.open(sources/f'{prefix}_{view}.png').convert('RGB');im.thumbnail(tile,Image.Resampling.LANCZOS)
        x=pad+col*(tile[0]+pad);y=pad+row*(tile[1]+head+pad)
        draw.text((x,y),f'{label} - {view.replace("_"," ")}',fill='black')
        sheet.paste(im,(x,y+head))
out.parent.mkdir(exist_ok=True)
sheet.save(out,quality=91)
print(out)
