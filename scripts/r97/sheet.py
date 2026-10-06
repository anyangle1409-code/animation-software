import sys
from PIL import Image, ImageDraw
# usage: sheet.py out.png cols cell file1 [file2 ...]
out, cols, cell = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
files = sys.argv[4:]
rows = (len(files)+cols-1)//cols
S = Image.new('RGB', (cols*cell, rows*(cell+18)), (20,20,20))
d = ImageDraw.Draw(S)
for i,f in enumerate(files):
    im = Image.open(f).convert('RGB').resize((cell,cell))
    x,y = (i%cols)*cell, (i//cols)*(cell+18)
    S.paste(im,(x,y+18)); d.text((x+4,y+3), f.split('/')[-1][:60], fill=(230,230,230))
S.save(out)
