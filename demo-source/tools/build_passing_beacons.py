"""Shift beacon projected X with its own road widening; no mapper/I/O changes."""
from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parents[1]
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
asm="""org 0b130h
 push af
 push bc
 push de
 push hl
 ld l,(ix-6)
 ld h,(ix-5)
 ld de,25
 ld bc,-1
divide:
 inc bc
 or a
 sbc hl,de
 jr nc,divide
 ld d,b
 ld e,c
 ld hl,(0e247h)
 ld a,(0e24fh)
 call 0b200h
 ld c,a
 ld l,(ix-4)
 ld h,(ix-3)
 inc hl
 inc hl
 ld a,(hl)
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
 pop de
 add hl,de
 ld (60197),hl
 ex de,hl
 pop de
 pop bc
 pop af
 ret
 defs 0b200h-$,0ffh
"""+(R/'src/passing_layout.asm').read_text().replace('org 06000h','')
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-passing-traffic-asm'+suffix);out=R/('outputs/six-route-passing-beacons'+suffix);out.mkdir(exist_ok=True)
 (out/'beacon.asm').write_text(asm)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'beacon.asm'),str(out/'beacon.bin')],check=True)
 code=(out/'beacon.bin').read_bytes();assert 0xb130+len(code)<0xb351
 p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old)
 assert old[off(0xbc8f):off(0xbc8f)+3]==bytes.fromhex('2225eb')
 assert old[off(0xb02c):off(0xb02c)+3]==bytes.fromhex('c335a9')
 rom[off(0xbc8f):off(0xbc8f)+3]=bytes.fromhex('cd30b1')
 rom[off(0xb130):off(0xb130)+len(code)]=code
 assert len(rom)==4194304
 (out/p.name).write_bytes(rom)
 for name in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(out/name).write_bytes((src/name).read_bytes())
 report=dict(bytes=len(rom),helper_bytes=len(code),sha256=hashlib.sha256(rom).hexdigest(),playable_adoption=False,native_validation=False)
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
