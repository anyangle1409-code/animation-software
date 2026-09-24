"""Make matched V11/V12 hand geometry review boards."""
from pathlib import Path
import os
from PIL import Image,ImageDraw,ImageFont

version=os.environ.get('BOARD_VERSION','v12c_palm_volume')
label=os.environ.get('BOARD_LABEL','V12c')
baseline_label=os.environ.get('BASELINE_LABEL','V11')
R=Path(__file__).resolve().parents[1]/f'renders_{version}'
try:font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',28)
except OSError:font=ImageFont.load_default()
sets={
 f'{label.upper()}_{baseline_label.upper()}_OPEN_HAND_COMPARISON.jpg':[('Open palm','open_hand_review','hand'),('Back','open_hand_review','hand_back'),('Thumb-index web','open_hand_review','hand_web')],
 f'{label.upper()}_{baseline_label.upper()}_CLOSED_FIST_COMPARISON.jpg':[('Palm','closed_fist_review','hand'),('Back','closed_fist_review','hand_back'),('Side','closed_fist_review','hand_side')],
 f'{label.upper()}_{baseline_label.upper()}_EXERCISE_HAND_COMPARISON.jpg':[('Curl grip','dumbbell_bicep_curl_bottom','hand'),('Push-up contact','push_up_bottom','hand'),('Pull-up grip','pull_up_peak','hand')],
}
for name,views in sets.items():
    w,h=550,600
    board=Image.new('RGB',(w*len(views),h*2+82),(23,27,32));draw=ImageDraw.Draw(board)
    for col,(title,pose,view) in enumerate(views):
        draw.text((col*w+14,7),title,fill=(245,245,245),font=font)
        for row,kind in enumerate(('baseline','candidate')):
            with Image.open(R/f'{pose}_{kind}_{view}.png') as im:
                board.paste(im.convert('RGB').resize((w,h),Image.Resampling.LANCZOS),(col*w,42+row*h))
            draw.text((col*w+12,46+row*h),baseline_label if row==0 else label,fill=(255,255,255),font=font,stroke_width=2,stroke_fill=(0,0,0))
    board.save(R/name,quality=92,subsampling=0);print(R/name)
