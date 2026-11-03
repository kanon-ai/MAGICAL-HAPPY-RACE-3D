"""Right-only reflector adjustment in the isolated three-lane candidate."""
from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parents[1]
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
helper='''org 06300h
 push bc
 ld hl,(0e24bh)
 add hl,hl
 add hl,hl
 ex de,hl
 ld hl,18
 ld a,(0eb56h)
 or a
 jr z,near_ready
 ld hl,-30
near_ready:
 add hl,de
 ld l,0
 inc h
 or a
 sbc hl,de
 pop bc
 ld a,h
 add a,c
 ld h,a
 ex de,hl
 ld hl,(0e247h)
 ld a,(0e24fh)
 call 06400h
 ld c,a
 ld a,(0f6f6h)
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
 ld e,(ix-7)
 ld d,(ix-6)
 add hl,de
 ld (ix-7),l
 ld (ix-6),h
 ret
 defs 06400h-$,0ffh
'''+(R/'src/passing_layout.asm').read_text().replace('org 06000h','')
stub='''org 0a960h
 ld (0f6f6h),a
 push af
 push bc
 push de
 push hl
 push iy
 ld a,211
 ld (06000h),a
 call 06300h
 ld a,(0e24ch)
 call 08572h
 pop iy
 pop hl
 pop de
 pop bc
 pop af
 jp 08652h
'''
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-passing-props'+suffix);out=R/('outputs/six-route-passing-markers'+suffix);out.mkdir(exist_ok=True)
 def assemble(name,text):
  (out/(name+'.asm')).write_text(text)
  subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/(name+'.asm')),str(out/(name+'.bin'))],check=True)
  return (out/(name+'.bin')).read_bytes()
 h=assemble('marker-helper',helper);s=assemble('marker-stub',stub);assert len(s)==32 and len(h)<512
 path=next(src.glob('*.rom'));old=path.read_bytes();rom=bytearray(old)
 bank=211*16384+8192+0x300;assert old[bank:bank+len(h)]==b'\xff'*len(h)
 # This tail belongs to the retired mirror routine; the active gate ends A95C.
 assert old[off(0xa960):off(0xa980)]==bytes.fromhex('7506dd7407110000dd6e04dd6605093e58bd3e009ce27aa9ee80f288a93e5891')
 pattern=bytes.fromhex('7ee5c5cd5286dd73fddd72fec1e1')
 start=off(0xd3b3);at=old.find(pattern,start,start+300);assert at>=0
 rom[at+3:at+6]=bytes.fromhex('cd60a9')
 rom[off(0xa960):off(0xa980)]=s;rom[bank:bank+len(h)]=h
 assert len(rom)==4194304
 (out/path.name).write_bytes(rom)
 for f in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(out/f).write_bytes((src/f).read_bytes())
 report=dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),helper_bytes=len(h),stub_bytes=len(s),playable_adoption=False,native_validation=False)
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(out.name,report)
