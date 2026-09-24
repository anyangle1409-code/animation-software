"""Produce matched V10/V11 hand comparison boards from identical pose/camera renders.

The V10 board script with the V11 folder and labels: the baseline row is V10,
the row V11 is meant to improve on.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

R=Path(__file__).resolve().parents[1]/'renders_v11_hand_cleanup'
def first_font(*paths):
    for path in paths:
        try: return ImageFont.truetype(path,28)
        except OSError: pass
    return ImageFont.load_default()
font=first_font('C:/Windows/Fonts/arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')

sets={
 'V11_V10_OPEN_HAND_COMPARISON.jpg': [('Open palm','open_hand_review','hand'),('Back','open_hand_review','hand_back'),('Thumb-index web','open_hand_review','hand_web')],
 'V11_V10_CLOSED_FIST_COMPARISON.jpg': [('Palm','closed_fist_review','hand'),('Back','closed_fist_review','hand_back'),('Side','closed_fist_review','hand_side')],
 'V11_V10_EXERCISE_HAND_COMPARISON.jpg': [('Curl grip','dumbbell_bicep_curl_bottom','hand'),('Push-up contact','push_up_bottom','hand'),('Pull-up grip','pull_up_peak','hand')],
}
for name,views in sets.items():
    w,h=550,600
    board=Image.new('RGB',(w*len(views),h*2+82),(23,27,32))
    draw=ImageDraw.Draw(board)
    for col,(title,pose,view) in enumerate(views):
        draw.text((col*w+14,7),title,fill=(245,245,245),font=font)
        for row,kind in enumerate(('baseline','candidate')):
            src=R/f'{pose}_{kind}_{view}.png'
            with Image.open(src) as im:
                board.paste(im.convert('RGB').resize((w,h),Image.Resampling.LANCZOS),(col*w,42+row*h))
            draw.text((col*w+12,46+row*h),'V10' if row==0 else 'V11',fill=(255,255,255),font=font,stroke_width=2,stroke_fill=(0,0,0))
    board.save(R/name,quality=90,subsampling=0)
    print(R/name)
