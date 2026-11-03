"""Precompute road vertex widening classification; exact stream candidate."""
from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parents[1]
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-grove-understory'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);out=R/('outputs/six-route-road-row-flags'+suffix);out.mkdir(exist_ok=True)
 port=0x8f if suffix else 0x9f
 asm=f'''org 09600h
row_stream:
 ld c,(hl)
 inc hl
 ld b,(hl)
 inc hl
 ld d,(hl)
 inc hl
 ld a,(hl)
 inc hl
 push hl
 ld hl,0
 rrca
 jr c,absolute
 ld hl,(0e811h)
absolute:
 add hl,bc
 and 1
 jr z,no_shift
 push de
 ld de,(0f6eeh)
 add hl,de
 pop de
no_shift:
 ld a,e
 cp 6
 jr z,beach
 cp 5
 jr nz,no_beach
beach:
 push de
 ld de,(0ecf0h)
 or a
 sbc hl,de
 pop de
no_beach:
 ld a,l
 out ({port}),a
 ld a,h
 out ({port}),a
 ld a,(0e813h)
 add a,d
 neg
 out ({port}),a
 sbc a,a
 out ({port}),a
 ld a,1
 out ({port}),a
 xor a
 out ({port}),a
 pop hl
 dec e
 jr nz,row_stream
 jp 08e02h
'''
 (out/'row.asm').write_text(asm);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'row.asm'),str(out/'row.bin')],check=True)
 code=(out/'row.bin').read_bytes();assert len(code)<=172
 assert old[off(0x9600):off(0x96ac)]==bytes(172)
 assert old[off(0x8dc0):off(0x8dc0)+3]==bytes.fromhex('4e2346')
 rom[off(0x9600):off(0x9600)+len(code)]=code;rom[off(0x8dc0):off(0x8dc0)+3]=bytes.fromhex('c30096')
 for bank in (212,213):
  for w in range(128):
   for i in range(12):
    at=bank*16384+8192+w*64+i*4+3;flag=old[at];assert flag in (0,1)
    rom[at]=flag | (2 if not flag and i in (3,4,5,8,9) else 0)
 (out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 report=dict(bytes=len(rom),helper_bytes=len(code),changed_bytes=sum(a!=b for a,b in zip(old,rom)),sha256=hashlib.sha256(rom).hexdigest(),adopted=False,scope='Road cross-section flags and equivalent row stream only; native proof pending.')
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(out.name,report)
