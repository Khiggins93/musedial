"""Pack original companion gestures and make a reviewable animated preview."""
import hashlib
import io
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
paths=sorted((ROOT/'assets/rendered-companion').glob('*.png'))
assert len(paths)==145, f'Expected 145 frames, got {len(paths)}'
mask=Image.new('L',(192,192))
mask.putdata([round(255*max(0,min(1,min(x,y,191-x,191-y)/14))) for y in range(192) for x in range(192)])
frames=[ImageChops.multiply(Image.open(p).convert('RGB'),mask.convert('RGB')) for p in paths]
blob=bytearray();offsets=[0]
for im in frames:
    stream=io.BytesIO();im.save(stream,format='JPEG',quality=82,subsampling=0)
    blob.extend(stream.getvalue());offsets.append(len(blob))
assert len(blob)<=1000000,'Companion resource exceeds budget'
dest=ROOT/'firmware/MuseDial'
(dest/'companion_frames.h').write_text('#pragma once\n#include <stdint.h>\nextern const uint8_t companion_jpeg[];\nextern const uint32_t companion_offsets[146];\n')
with (dest/'companion_frames.cpp').open('w') as f:
    f.write('#include "companion_frames.h"\nconst uint32_t companion_offsets[146]={'+','.join(map(str,offsets))+'};\nconst uint8_t companion_jpeg[]={\n')
    for i in range(0,len(blob),24):f.write(','.join(map(str,blob[i:i+24]))+',\n')
    f.write('};\n')
out=ROOT/'build/previews/companion';out.mkdir(parents=True,exist_ok=True)
sequence=[]
for im in frames[:9]:sequence.extend([im]*6)
sequence+=frames[9:]
sequence[0].save(out/'companion.gif',save_all=True,append_images=sequence[1:],duration=50,loop=0)
sheet=Image.new('RGB',(960,212));draw=ImageDraw.Draw(sheet)
for i,(index,label) in enumerate([(2,'MIRADA'),(25,'SONRISA'),(57,'CARINO'),(93,'ABRAZO'),(129,'COSQUILLAS')]):
    sheet.paste(frames[index],(192*i,0));draw.text((192*i+55,196),label,fill='white')
sheet.save(out/'contact-sheet.png')
(out/'assets.json').write_text(json.dumps({'frames':145,'fps':20,'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()},indent=2))
print('Companion JPEG bytes:',len(blob))
