"""Classify shoreline vertices offline within the existing 80-byte helper slot."""
from pathlib import Path
import subprocess,json,hashlib
r=Path(__file__).resolve().parents[1]
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix in ('','-external-88h'):
 src=r/('outputs/six-route-city-alpine-connected'+suffix)
 base=r/('outputs/six-route-road-row-flags-v2'+suffix)
 asm=(base/'row.asm').read_text()
 assert asm.count(' add hl,bc\n and 1')==1
 asm=asm.replace(' add hl,bc\n and 1',' add hl,bc\n ld b,a\n and 1')
 before=' ld a,e\n cp 6\n jr z,beach\n cp 5\n jr nz,no_beach'
 assert before in asm
 asm=asm.replace(before,' ld a,b\n and 2\n jr z,no_beach')
 out=r/('outputs/six-route-road-beach-flags'+suffix);out.mkdir(exist_ok=True)
 (out/'row.asm').write_text(asm)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'row.asm'),str(out/'row.bin')],check=True)
 code=(out/'row.bin').read_bytes();assert len(code)<=80
 path=next(src.glob('*.rom'));old=path.read_bytes();rom=bytearray(old);mask=bytearray(len(old))
 at=off(0x9600);prior=(base/'row.bin').read_bytes();assert old[at:at+len(prior)]==prior
 assert old[at+len(prior):at+80]==bytes(80-len(prior))
 rom[at:at+80]=code+bytes(80-len(code));mask[at:at+80]=bytes([1])*80
 for bank in (189,190,212,213):
  for width in range(128):
   for index in range(12):
    at=bank*16384+8192+width*64+index*4+3
    assert old[at] in (0,1,2)
    rom[at]=old[at]|(4 if index in (6,7) else 0);mask[at]=1
 assert len(rom)==4194304 and all(a==b or mask[i] for i,(a,b) in enumerate(zip(old,rom)))
 (out/path.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 (out/'manifest.json').write_text(json.dumps(dict(bytes=len(rom),helper_bytes=len(code),sha256=hashlib.sha256(rom).hexdigest(),native_verified=False,adopted=False),indent=2))
 print(out.name,len(code))
