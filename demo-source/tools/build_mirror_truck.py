"""Mirror-only truck identity fix. Preserve baseline and all gameplay bytes."""
from pathlib import Path
import subprocess,json,hashlib
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];W=R/'work/mirror-truck';W.mkdir(exist_ok=True)
s=(R/'outputs/six-route-mirror-sprite/sprite.asm').read_text()
s=s.replace(' ld a,(ix-14)\n cp 51',' ld a,(ix-13)\n cp 4\n jr z,truck\n ld a,(ix-14)\n cp 51',1)
s=s.replace(' call '+str(json.loads((R/'outputs/symbols.json').read_text())['_gfx_scaled']), 'draw_sprite:\n call '+str(json.loads((R/'outputs/symbols.json').read_text())['_gfx_scaled']),1)
s=s.replace('getx:\n','truck:\n ld a,224\n ld de,694\n jr draw_sprite\ngetx:\n',1)
(W/'sprite.asm').write_text(s)
subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(W/'sprite.asm'),str(W/'sprite.bin')],check=True)
code=(W/'sprite.bin').read_bytes();oldcode=(R/'outputs/six-route-mirror-sprite/sprite.bin').read_bytes()
im=Image.new('P',(32,26),0);d=ImageDraw.Draw(im)
# Box body behind a tall cab, wide windshield, mirrors, grille and headlights.
d.rectangle((5,0,26,18),fill=14);d.line((5,0,26,0),fill=15)
d.rectangle((4,6,27,22),fill=14);d.rectangle((6,7,25,14),fill=12)
d.polygon([(7,8),(14,8),(10,13),(7,13)],fill=36)
d.line((6,15,25,15),fill=15);d.rectangle((4,16,27,17),fill=3)
d.rectangle((0,9,3,13),fill=12);d.rectangle((28,9,31,13),fill=12)
d.rectangle((4,19,9,20),fill=15);d.rectangle((22,19,27,20),fill=15)
d.rectangle((11,18,20,21),fill=12);d.line((12,19,19,19),fill=36)
d.rectangle((3,22,28,23),fill=12);d.rectangle((4,24,8,25),fill=12);d.rectangle((23,24,27,25),fill=12)
d.rectangle((13,22,18,22),fill=15)
raw=im.tobytes();(W/'truck.bin').write_bytes(raw)
for suffix in ('','-external-88h'):
 src=R/('outputs/pixel-tree-smooth'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();b=bytearray(old);allowed=set()
 assert hashlib.sha256(old).hexdigest()==json.loads((src/'manifest.json').read_text())['sha256']
 def patch(at,data):b[at:at+len(data)]=data;allowed.update(range(at,at+len(data)))
 at=207*16384+8192
 assert b[at:at+len(oldcode)]==oldcode
 assert b[at+len(oldcode):at+len(code)]==bytes([255])*(len(code)-len(oldcode))
 patch(at,code)
 for y in range(26):
  offset=(694+y-512)*256+224;at=(4+offset//8192)*16384+8192+offset%8192
  assert b[at:at+32]==bytes(32)
  patch(at,raw[y*32:(y+1)*32])
 assert len(b)==4194304 and all(i in allowed for i,(a,c) in enumerate(zip(old,b)) if a!=c)
 O=R/('outputs/mirror-truck'+suffix);O.mkdir(exist_ok=True);(O/p.name).write_bytes(b)
 (O/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(b).hexdigest(),source_sha256=hashlib.sha256(old).hexdigest(),bytes=len(b),scope='Mirror sprite selection: traffic ID4 uses truck front. Other identities and gameplay unchanged.'),indent=2))
print('Both mirror-only ROMs built.')
