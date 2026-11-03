"""Isolated one-LRMM mirror-car trial; projection and traffic remain unchanged."""
from pathlib import Path
import json, subprocess, hashlib, re
from PIL import Image, ImageDraw
R=Path(__file__).resolve().parents[1]
S=json.loads((R/'outputs/symbols.json').read_text())
asm=f'''org 06000h
 push iy
 ; Arguments follow the existing SDCC gfx_scaled callee-clean ABI.
 xor a
 push af
 inc sp
 ld hl,660
 push hl
 ld a,({S['_mirror_bottom']})
 ld l,a
 ld h,0
 push hl
 ld l,(ix-2)
 ld h,(ix-1)
 ld e,(ix-20)
 ld d,0
 or a
 sbc hl,de
 push hl
 call getx
 push hl
 ld l,(ix-16)
 ld h,0
 add hl,hl
 ld de,steps
 add hl,de
 ld e,(hl)
 inc hl
 ld d,(hl)
 push de
 ; Clip at the mirror's right edge (gfx_scaled itself clips at 256).
 call getx
 ex de,hl
 ld hl,88
 or a
 sbc hl,de
 ld a,h
 or a
 jr nz,fullwidth
 ld a,l
 cp (ix-16)
 jr c,widthready
fullwidth:
 ld a,(ix-16)
widthready:
 ld l,a
 ld h,(ix-20)
 push hl
 ld a,32
 push af
 inc sp
 ld a,(ix-14)
 cp 51
 ld a,160
 jr z,originready
 ld a,(ix-14)
 cp 14
 ld a,192
 jr z,originready
 ld a,224
originready:
 ld de,668
 call {S['_gfx_scaled']}
 pop iy
 ret
getx:
 ld l,(ix-22)
 ld h,(ix-21)
 ld a,(ix-16)
 srl a
 ld e,a
 ld d,0
 or a
 sbc hl,de
 ret
steps:
'''+ '\n'.join('dw '+str(8192//w if w else 8192) for w in range(256))+'\n'
# Last sampled source row must remain inside our 26-row sprite, including tiny cars.
assert all(((max(3,w*4//5)-1)*(8192//w))>>8 <26 for w in range(3,256))
sprites=[]
for body,shade,light in [(51,49,54),(14,7,65),(3,32,36)]:
 im=Image.new('P',(32,26),0);d=ImageDraw.Draw(im)
 d.polygon([(8,0),(23,0),(27,9),(30,12),(31,22),(0,22),(1,12),(4,9)],fill=body)
 d.polygon([(9,2),(22,2),(25,9),(6,9)],fill=12)
 d.polygon([(9,2),(14,2),(10,8),(7,8)],fill=36)
 d.line([(9,0),(22,0)],fill=light)
 d.polygon([(4,11),(27,11),(29,16),(2,16)],fill=light)
 d.line([(3,17),(28,17)],fill=shade)
 d.rectangle((1,18,7,20),fill=15);d.rectangle((24,18,30,20),fill=15)
 d.rectangle((10,18,21,20),fill=12)
 d.rectangle((1,22,30,23),fill=12)
 d.rectangle((3,24,7,25),fill=12);d.rectangle((24,24,28,25),fill=12)
 sprites.append(im)
pal=list(map(int,re.findall(r'\d+', (R/'src/palette_data.h').read_text().split('{',1)[1])))
pal=[round(v*255/31) for v in pal]
def codeoff(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 O=R/('outputs/six-route-mirror-sprite'+suffix);O.mkdir(exist_ok=True)
 (O/'sprite.asm').write_text(asm)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'sprite.asm'),str(O/'sprite.bin')],check=True)
 code=(O/'sprite.bin').read_bytes();assert len(code)<8192
 src=R/('outputs/six-route-traffic-balanced-safe'+suffix)
 rom=bytearray((src/name).read_bytes());old=bytes(rom);allowed=set()
 def patch(at,data):
  rom[at:at+len(data)]=data;allowed.update(range(at,at+len(data)))
 bank=207*16384+8192;assert rom[bank:bank+8192]==b'\xff'*8192
 assert rom[codeoff(0xb02c):codeoff(0xb02c)+3]==bytes.fromhex('dd7eec')
 assert rom[codeoff(0xa935):codeoff(0xa935)+8]==bytes.fromhex('dde5dd210000dd39')
 patch(codeoff(0xb02c),bytes.fromhex('c335a9'))
 patch(codeoff(0xa935),bytes.fromhex('3ecf320060cd00603efc320060c351b3'))
 patch(bank,code)
 for k,im in enumerate(sprites):
  raw=im.tobytes()
  for y in range(26):
   offset=(668+y-512)*256+160+k*32
   at=(4+offset//8192)*16384+8192+offset%8192
   patch(at,raw[y*32:(y+1)*32])
 assert len(rom)==4194304
 assert all(i in allowed for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
 (O/name).write_bytes(rom)
 preview=Image.new('P',(96,26),0);preview.putpalette(pal)
 for k,im in enumerate(sprites):preview.paste(im,(32*k,0))
 preview.resize((576,156),Image.Resampling.NEAREST).save(O/'sprites.png')
 for asset in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(O/asset).write_bytes((src/asset).read_bytes())
 (O/'manifest.json').write_text(json.dumps(dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),helper_bytes=len(code),scope='Mirror car art and draw calls only; native verification pending.'),indent=2))
 print(O,len(code))
