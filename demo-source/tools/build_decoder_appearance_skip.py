"""Skip inland mesh only for appearance op0, retaining forced visibility."""
from pathlib import Path
import subprocess,json,hashlib
r=Path(__file__).resolve().parents[1];w=r/'work/decoder-appearance-skip';w.mkdir(exist_ok=True)
asm='''org 01d20h
 ld a,(0e24fh)
 cp 7
 jp c,0f098h
 push hl
 ld hl,(0f269h)
 ld a,l
 and 3
 ld c,a
 srl h
 rr l
 srl h
 rr l
 ld (0f269h),hl
 pop hl
 ld a,c
 or a
 jp nz,0f0c9h
 ld a,(iy+0)
 and 64
 jp nz,0f0c9h
 ld a,(0e24fh)
 cp 9
 jp c,0f0c9h
 jp 0f0d0h
'''
(w/'helper.asm').write_text(asm)
subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(w/'helper.asm'),str(w/'helper.bin')],check=True)
helper=(w/'helper.bin').read_bytes();assert len(helper)+32<256
loader=(r/'work/boundary-nibble-dispatch/loader.bin').read_bytes();needle=bytes.fromhex('011400edb0');assert loader.count(needle)==1
newloader=loader.replace(needle,bytes([1,32+len(helper),0,0xed,0xb0]))
for suffix in ('','-external-88h'):
 src=r/('outputs/six-route-city-alpine-connected'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);mask=bytearray(len(old))
 def write(at,b,expected):
  assert old[at:at+len(b)]==expected
  assert not any(mask[at:at+len(b)])
  rom[at:at+len(b)]=b;mask[at:at+len(b)]=bytes([1])*len(b)
 write(8192+0x91,bytes.fromhex('c3201d00000000'),bytes.fromhex('3a4fe2fe073031'))
 write(0x2500,newloader,loader)
 write(0x2720,helper,bytes([255])*len(helper))
 assert len(rom)==4194304 and all(a==b or mask[i] for i,(a,b) in enumerate(zip(old,rom)))
 out=r/('outputs/six-route-decoder-appearance-skip'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 (out/'manifest.json').write_text(json.dumps(dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),helper_bytes=len(helper),adopted=False,native_verified=False,scope='Only inland op0 mesh skipped; flag64 and pieces7/8 retain full decode. Hidden scratch may differ; no gameplay changes.'),indent=2));print(out.name,len(helper))
