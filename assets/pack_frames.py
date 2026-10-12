"""Pack baseline JPEG frames into flash-resident C data; build a preview GIF."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops
import io, json, hashlib
ROOT=Path(__file__).resolve().parents[1]
frames=sorted((ROOT/'assets/rendered-v2.1').glob('*.png'))
OUT=ROOT/'build/previews/normal'
OUT.mkdir(parents=True,exist_ok=True)
assert len(frames)==360, f'Expected 360 frames, got {len(frames)}'
blob=bytearray(); offsets=[0]; previews=[]
for p in frames:
    im=Image.open(p).convert('RGB')
    assert im.size==(192,192)
    # Fade the stage into the black panel instead of exposing a square border.
    mask=Image.new('L',(192,192))
    mask.putdata([round(255*max(0,min(1,min(x,y,191-x,191-y)/14))) for y in range(192) for x in range(192)])
    im=ImageChops.multiply(im,mask.convert('RGB'))
    buf=io.BytesIO(); im.save(buf,format='JPEG',quality=82,subsampling=0,optimize=False)
    blob.extend(buf.getvalue()); offsets.append(len(blob))
    previews.append(im)
assert len(blob)<2700000, 'Asset budget exceeded'
dest=ROOT/'firmware/MuseDial'
(dest/'avatar_frames.h').write_text('#pragma once\n#include <stdint.h>\nextern const uint8_t avatar_jpeg[];\nextern const uint32_t avatar_offsets[361];\nstatic constexpr int CLIP_FRAMES = 40;\n')
with (dest/'avatar_frames.cpp').open('w') as f:
    f.write('#include "avatar_frames.h"\nconst uint32_t avatar_offsets[361] = {'+','.join(map(str,offsets))+'};\nconst uint8_t avatar_jpeg[] = {\n')
    for i in range(0,len(blob),24): f.write(','.join(map(str,blob[i:i+24]))+',\n')
    f.write('};\n')
previews[0].save(OUT/'3d-preview.gif',save_all=True,append_images=previews[1:],duration=50,loop=0)
sheet=Image.new('RGB',(576,636),'black'); draw=ImageDraw.Draw(sheet)
labels=['TRANQUILO','CURIOSO','PENSANDO','ANIMADO','DORMILON','FELIZ','SALUDO','SORPRESA','SUENO']
for i,label in enumerate(labels):
    x=(i%3)*192; y=(i//3)*212; sheet.paste(previews[i*40+10],(x,y)); draw.text((x+55,y+193),label,fill='white')
sheet.save(OUT/'3d-contact-sheet.png')
(OUT/'3d-assets.json').write_text(json.dumps({'frames':360,'clips':labels,'fps':20,'jpeg_bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest(),'renderer':'Blender Cycles, 32 samples, procedural geometry','jpeg_quality':82},indent=2))
print(len(blob),'JPEG bytes')
