"""JPEG + row silhouette spans in a checksummed flash resource image."""
import io,json,struct,zlib,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'build/previews/halloween'; OUT.mkdir(parents=True,exist_ok=True)
paths=sorted((ROOT/'assets/rendered-halloween').glob('*.png'))
assert len(paths)==480,'Render all twelve 40-frame clips first'
names=['TRANQUILO','CURIOSO','TRAVIESO','SALUDO','RISITA','SORPRESA','BOO','CARCAJADA','BAILE','HECHIZO','DORMILON','BOSTEZO']
images=[]; masks=[]
for p in paths:
    im=Image.open(p).convert('RGBA'); assert im.size==(192,192)
    black=Image.new('RGB',im.size); black.paste(im,mask=im.getchannel('A')); images.append(black)
    alpha=im.getchannel('A'); spans=bytearray()
    for y in range(192):
        xs=[x for x in range(192) if alpha.getpixel((x,y))>24]
        spans.extend((min(xs),max(xs)) if xs else (255,0))
    masks.append(spans)
for count in [40,32]:
    selected=[m*40+(f*40//count) for m in range(12) for f in range(count)]
    for quality in range(82,75,-2):
        offsets=[0]; blob=bytearray()
        for i in selected:
            buf=io.BytesIO(); images[i].save(buf,format='JPEG',quality=quality,subsampling=0,optimize=False)
            blob.extend(buf.getvalue()); offsets.append(len(blob))
        table=struct.pack('<'+'I'*len(offsets),*offsets)
        silhouettes=b''.join(masks[i] for i in selected)
        payload=table+silhouettes+blob
        if len(payload)+48<=3*1024*1024:break
    if len(payload)+48<=3*1024*1024:break
assert len(payload)+48<=3*1024*1024,'Halloween asset budget exceeded'
span_offset=48+len(table); jpeg_offset=span_offset+len(silhouettes)
header=struct.pack('<8s10I',b'HWEEN3\0\0',1,12,count,192,192,20,48+len(payload),jpeg_offset,span_offset,zlib.crc32(payload))
result=header+payload
dest=ROOT/'build/Halloween'; dest.mkdir(parents=True,exist_ok=True)
(dest/'halloween.bin').write_bytes(result)
images[0].save(OUT/'halloween-preview.gif',save_all=True,append_images=images[1:],duration=50,loop=0)
sheet=Image.new('RGB',(768,636)); draw=ImageDraw.Draw(sheet)
for i,name in enumerate(names):
    x=i%4*192; y=i//4*212; sheet.paste(images[i*40+10],(x,y)); draw.text((x+50,y+194),name,fill='orange')
sheet.save(OUT/'halloween-expressions.png')
(OUT/'halloween-assets.json').write_text(json.dumps({'clips':names,'frames_per_clip':count,'fps':20,'jpeg_quality':quality,'bytes':len(result),'sha256':hashlib.sha256(result).hexdigest(),'crc32':zlib.crc32(payload),'header_bytes':48,'silhouette_encoding':'192 pairs of inclusive x spans per frame; 255,0 empty'},indent=2))
print('Halloween assets:',len(result),'bytes;',count,'frames/clip; JPEG',quality)
