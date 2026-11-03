"""Widen the reflected road's right edge using signed rear-world distances."""
from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parents[1]
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
asm='''org 0b030h
first_edge:
 push bc
 push de
 push hl
 push iy
 ld l,c
 ld h,0
 add hl,hl
 ld de,depths
 add hl,de
 ld e,(hl)
 inc hl
 ld d,(hl)
 ld a,208
 ld (06000h),a
 ld a,(0e24fh)
 ld hl,(0e247h)
 call 06000h
 ld c,a
 ld a,(iy+2)
 db 0edh,0c9h
 ld d,h
 ld e,l
 add hl,hl
 add hl,hl
 add hl,de
 ld b,7
shift:
 srl h
 rr l
 djnz shift
 ld (0f6f8h),hl
 ld a,252
 ld (06000h),a
 pop iy
 pop de
 add hl,de
 pop de
 pop bc
 jp 08d35h
second_edge:
 push de
 ld de,(0f6f8h)
 add hl,de
 pop de
 jp 08d35h
depths: dw -512,-160,-72,-32
'''
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-passing-markers'+suffix);out=R/('outputs/six-route-passing-mirror-width'+suffix);out.mkdir(exist_ok=True)
 (out/'mirror-width.asm').write_text(asm)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'mirror-width.asm'),str(out/'mirror-width.bin'),str(out/'mirror-width.sym')],check=True)
 symbols={x.split()[0]:int(x.split()[2].rstrip('H'),16) for x in (out/'mirror-width.sym').read_text().splitlines()}
 code=(out/'mirror-width.bin').read_bytes();assert len(code)<0x100
 path=next(src.glob('*.rom'));old=path.read_bytes();rom=bytearray(old)
 assert old[off(0xb02c):off(0xb02c)+3]==bytes.fromhex('c335a9') # Retired mirror-car body is bypassed.
 assert old[off(0xb030):off(0xb030)+16]==bytes.fromhex('77f9dd36fa00dd7ef9dd77f7dd36f800')
 for address,label in ((0xac14,'first_edge'),(0xac1c,'second_edge')):
  at=off(address);assert old[at:at+3]==bytes.fromhex('cd358d')
  rom[at:at+3]=b'\xcd'+symbols[label].to_bytes(2,'little')
 rom[off(0xb030):off(0xb030)+len(code)]=code
 assert len(rom)==4194304
 (out/path.name).write_bytes(rom)
 for name in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(out/name).write_bytes((src/name).read_bytes())
 report=dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),helper_bytes=len(code),symbols=symbols,playable_adoption=False,pending='Extra mirror lane divider, beacons, AI, normal-drive verification')
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
