"""Skip mesh component decode only for raw width-zero object slots."""
from pathlib import Path
import subprocess,hashlib,json
r=Path(__file__).resolve().parents[1];w=r/'work/decoder-zero-width';w.mkdir(exist_ok=True)
s='''org 01d20h
 ld a,(iy+2)
 or a
 jp z,0f0d0h
 ld a,(0e24fh)
 cp 7
 jp nc,0f0c9h
 jp 0f098h
'''
(w/'helper.asm').write_text(s)
subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(w/'helper.asm'),str(w/'helper.bin')],check=True)
helper=(w/'helper.bin').read_bytes();assert len(helper)==18
loader=(r/'work/boundary-nibble-dispatch/loader.bin').read_bytes()
needle=bytes.fromhex('011400edb0');assert loader.count(needle)==1
newloader=loader.replace(needle,bytes([1,32+len(helper),0,0xed,0xb0]))
for suffix in ('','-external-88h'):
 src=r/('outputs/six-route-city-alpine-connected'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);allowed=bytearray(len(old))
 def write(at,b,expected):
  assert old[at:at+len(b)]==expected
  assert not any(allowed[at:at+len(b)])
  rom[at:at+len(b)]=b;allowed[at:at+len(b)]=bytes([1])*len(b)
 write(8192+0x91,bytes.fromhex('c3201d00000000'),bytes.fromhex('3a4fe2fe073031'))
 write(0x2500,newloader,loader)
 write(0x2720,helper,bytes([255])*len(helper))
 assert len(rom)==4194304 and all(a==b or allowed[i] for i,(a,b) in enumerate(zip(old,rom)))
 out=r/('outputs/six-route-decoder-zero-width'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 report=dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),helper_bytes=len(helper),adopted=False,native_verified=False,scope='Cache1d20 helper skips raw width-zero mesh component. Hidden mesh scratch may retain earlier values; visible mesh/profile/pixels must match.')
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
