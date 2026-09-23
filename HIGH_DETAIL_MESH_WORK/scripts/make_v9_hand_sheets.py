from PIL import Image,ImageOps,ImageDraw,ImageFont
from pathlib import Path
root=Path('renders_v9_hand_geometry_review')
pairs=[('curl','dumbbell_bicep_curl_bottom'),('pushup','push_up_bottom'),('pullup','pull_up_peak')]
for label,stem in pairs:
    files=[root/f'{stem}_{kind}_hand.png' for kind in ('baseline','candidate')]
    ims=[Image.open(p).convert('RGB') for p in files]
    canvas=Image.new('RGB',(ims[0].width*2,ims[0].height+52),(33,36,40))
    d=ImageDraw.Draw(canvas)
    for j,im in enumerate(ims):
        canvas.paste(im,(j*im.width,52))
        d.text((j*im.width+24,16),('V8 accepted knee baseline','V9 hand review')[j],fill='white')
    out=root/f'V8_V9_{label.upper()}_HAND_COMPARISON.jpg'
    canvas.save(out,quality=94)
    print(out)
