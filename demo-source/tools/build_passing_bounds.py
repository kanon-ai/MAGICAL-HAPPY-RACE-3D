from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parents[1]
asm='''org 0a980h
width_limit:
 push bc
 push de
 push hl
 ld a,208
 ld (06000h),a
 ld a,(0e24fh)
 ld hl,(0e247h)
 ld de,0
 call 06000h
 ld l,a
 ld h,0
 add hl,hl
 add hl,hl
 ld e,a
 add hl,de
 srl l
 ld a,l
 ld (0f6f5h),a
 ld a,252
 ld (06000h),a
 pop hl
 pop de
 pop bc
 ld a,(0f6f5h)
 add a,64
 ld iy,0e253h
 ret
steer_limit:
 ld a,(0f6f5h)
 add a,100
 ld iy,0e253h
 ret
clamp_limit:
 ld a,(0f6f5h)
 add a,100
 ld l,a
 ld h,0
 ret
'''
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-passing-structures'+suffix);o=R/('outputs/six-route-passing-bounds'+suffix);o.mkdir(exist_ok=True)
 (o/'bounds.asm').write_text(asm);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(o/'bounds.asm'),str(o/'bounds.bin'),str(o/'bounds.sym')],check=True)
 code=(o/'bounds.bin').read_bytes();assert len(code)<=0x77
 sym={x.split()[0]:int(x.split()[2].rstrip('H'),16) for x in (o/'bounds.sym').read_text().splitlines()}
 p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old)
 def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
 rom[off(0xa980):off(0xa980)+len(code)]=code
 for a,expected,label in [(0x33e9,'3e40fd2153e2','width_limit'),(0x3416,'3e64fd2153e2','steer_limit'),(0x342c,'216400','clamp_limit')]:
  at=214*16384+8192+a-0x2400;e=bytes.fromhex(expected);assert old[at:at+len(e)]==e,(hex(a),old[at:at+len(e)].hex())
  rom[at:at+len(e)]=b'\xcd'+sym[label].to_bytes(2,'little')+bytes(len(e)-3)
 assert len(rom)==4194304
 (o/p.name).write_bytes(rom)
 for f in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(o/f).write_bytes((src/f).read_bytes())
 (o/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),helper_bytes=len(code),symbols=sym,playable_adoption=False,pending='Native bounds validation, traffic merges, props and mirror'),indent=2))
 print(o.name,len(code),sym)
