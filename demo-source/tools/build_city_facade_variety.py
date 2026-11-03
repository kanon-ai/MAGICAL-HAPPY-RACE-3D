"""Use existing city facade tiles by stable world piece; no geometry/art growth."""
from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parents[1]
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
asm='''org 09650h
 ld l,(ix-10)
 ld h,(ix-9)
 ld de,58
 add hl,de
 ld a,(0e24fh)
 add a,(hl)
 ld d,a
 ld b,0
 cp 40
 ld a,(ix-8)
 jr nc,night
 cp 1
 ld c,5
 ret z
 cp 3
 ret z
 ; Before city, retain original building selection.
 ld e,a
 ld a,d
 cp 32
 ld a,e
 jr c,original_building
 cp 2
 jr z,balcony
 ld a,d
 and 1
 ld c,0
 ret z
 ld c,6
 ret
balcony:
 ld a,d
 and 2
 ld c,2
 ret z
 ld c,1
 ret
night:
 cp 3
 ld c,1
 ret z
original_building:
 cp 2
 ld c,2
 ret z
 ld c,0
 ret
'''
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-road-row-flags-v2'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old)
 out=R/('outputs/six-route-city-facade-variety'+suffix);out.mkdir(exist_ok=True)
 (out/'facades.asm').write_text(asm);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'facades.asm'),str(out/'facades.bin')],check=True)
 code=(out/'facades.bin').read_bytes();assert len(code)<=0x96ac-0x9650
 assert old[off(0x9650):off(0x96ac)]==bytes(0x5c)
 assert old[off(0xdbac):off(0xdbac)+3]==bytes.fromhex('dd6ef6')
 rom[off(0x9650):off(0x9650)+len(code)]=code;rom[off(0xdbac):off(0xdbac)+3]=bytes.fromhex('c35096')
 assert len(rom)==4194304
 (out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 result={'bytes':len(rom),'helper_bytes':len(code),'changed_bytes':sum(a!=b for a,b in zip(old,rom)),'sha256':hashlib.sha256(rom).hexdigest(),'adopted':False,'scope':'Only facade choice for worldpieces32..39, original kinds0/2. Trees, night, geometry, textures and simulation unchanged. Native/visual validation pending.'}
 (out/'manifest.json').write_text(json.dumps(result,indent=2));print(out.name,result)
