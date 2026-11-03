"""Art-only traffic overlay. No code, mesh, UV, palette or behaviour edits."""
from pathlib import Path
import re,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];A=R/'assets/modern-traffic'
im=Image.open(A/'traffic-master.png').convert('RGB');assert im.size==(1536,1024)
pal=np.array([round(int(x)*255/31) for x in re.findall(r'\d+',(R/'src/palette_data.h').read_text().split('{')[1].split('}')[0])],dtype=np.int32).reshape(256,3)
atlas=Image.frombytes('P',(256,44),(A/'before-atlas.bin').read_bytes());atlas.putpalette(pal.astype('uint8').ravel().tolist())
def tile(box,size,gray=False):
 a=np.array(im.crop(box).resize(size,Image.Resampling.LANCZOS)).astype(np.float32)
 if gray:
  v=a.mean(axis=2);a=np.stack((v*.94,v*.98,v),axis=2)
 diff=a.reshape(-1,1,3)-pal[None,1:,:]
 pixels=(diff[:,:,0]**2+diff[:,:,1]**2*1.2+diff[:,:,2]**2).argmin(axis=1).astype('uint8')+1
 out=Image.frombytes('P',size,pixels.tobytes());out.putpalette(atlas.getpalette());return out
for n,(side,rear) in enumerate([
 ((23,145,697,275),(758,145,1075,282)),
 ((49,478,657,611),(758,474,1072,613)),
 ((23,811,699,947),(758,820,1075,959))]):
 atlas.paste(tile(side,(64,20)),(n*64,0));atlas.paste(tile(rear,(64,20)),(n*64,20))
atlas.paste(tile((803,76,1030,120),(32,16)),(192,0))
atlas.paste(tile((178,84,437,142),(32,16)),(192,16))
atlas.paste(tile((1177,505,1494,612),(32,12),True),(192,32))
atlas.paste(tile((109,201,221,310),(32,32)),(224,0))
# Truck's editable native material retains the established continuous UV layout:
# 16x12 rear doors and 16x12 full side. No repeated/misaligned side panels.
def nearest(rgb):return int(np.sum((pal[1:]-rgb)**2,axis=1).argmin()+1)
white=nearest((207,214,218));light=nearest((238,242,239));shade=nearest((122,141,153));dark=nearest((39,49,60));blue=nearest((43,93,139));amber=nearest((231,166,49));red=nearest((230,44,44))
truck=Image.new('P',(32,12),white);truck.putpalette(atlas.getpalette());d=ImageDraw.Draw(truck)
d.line((0,0,15,0),fill=light);d.line((7,0,7,9),fill=shade)
for x in (4,11):d.line((x,1,x,8),fill=shade);d.point((x+1,7),fill=dark)
d.line((0,9,15,9),fill=shade);d.rectangle((0,10,15,11),fill=dark)
for x in (1,14):d.point((x,10),fill=red);d.point((x,0),fill=amber)
d.line((6,10,9,10),fill=light)
d.rectangle((16,0,24,8),fill=white);d.line((16,0,24,0),fill=light)
for y in (3,6):d.line((16,y,24,y),fill=shade)
d.line((24,0,24,9),fill=shade);d.line((16,8,31,8),fill=blue)
d.rectangle((16,10,31,11),fill=dark);d.point((17,9),fill=amber);d.point((30,9),fill=amber)
atlas.paste(truck,(224,32));atlas.save(A/'traffic-atlas.png');atlas.resize((1024,176),Image.Resampling.NEAREST).save(A/'traffic-atlas-preview.png');data=atlas.tobytes();(A/'traffic-atlas.bin').write_bytes(data)
for suffix in ('','-external-88h'):
 src=R/('outputs/center-timer'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();assert hashlib.sha256(old).hexdigest()==json.loads((src/'manifest.json').read_text())['sha256']
 rom=bytearray(old);allowed=set()
 for y in range(44):
  offset=y*256;at=(12+offset//8192)*16384+8192+offset%8192
  assert old[at:at+256]==(A/'before-atlas.bin').read_bytes()[offset:offset+256]
  rom[at:at+256]=data[offset:offset+256];allowed.update(range(at,at+256))
 assert len(rom)==4194304 and all(i in allowed for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
 O=R/('outputs/modern-traffic'+suffix);O.mkdir(exist_ok=True);(O/p.name).write_bytes(rom)
 (O/'manifest.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(old).hexdigest(),sha256=hashlib.sha256(rom).hexdigest(),bytes=len(rom),changed_bytes=sum(a!=b for a,b in zip(old,rom)),scope='Existing 256x44 traffic atlas pixels only',code_geometry_uv_palette_player_timer_audio_unchanged=True,rom_growth=0,native_verified=False),indent=2))
 print(O)
