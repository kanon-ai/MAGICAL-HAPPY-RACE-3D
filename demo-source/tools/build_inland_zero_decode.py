"""Trial: skip inland mesh decoding only for absent choice0, retaining overrides."""
from pathlib import Path
import subprocess,hashlib,json
R=Path(__file__).resolve().parents[1];w=R/'work/inland-zero-decode';assert not w.exists();w.mkdir()
asm='''org 01f80h
 ld a,(0e24fh)
 cp 16
 jp c,0f094h
 push hl
 ld hl,(0f269h)
 ld a,l
 and 3
 push af
 srl h
 rr l
 srl h
 rr l
 ld (0f269h),hl
 pop af
 pop hl
 or a
 jp nz,0f0c9h
 bit 6,(iy+0)
 jp nz,0f0c9h
 jp 0f0d0h
'''
(w/'skip.asm').write_text(asm);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(w/'skip.asm'),str(w/'skip.bin')],check=True)
code=(w/'skip.bin').read_bytes();assert 128+len(code)<=256
reader=(R/'work/bitpacked-nibble-reader/reader.bin').read_bytes();assert len(reader)==116
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-night-facade-variety'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);written=set()
 def write(at,data,expect):
  assert old[at:at+len(data)]==expect,(hex(at),old[at:at+len(data)].hex());rom[at:at+len(data)]=data;written.update(range(at,at+len(data)))
 assert old[0x2600:0x2674]==reader and old[0x2674:0x2700]==bytes([255])*140
 write(0x2680,code,bytes([255])*len(code))
 write(0x250b,(128+len(code)).to_bytes(2,'little'),len(reader).to_bytes(2,'little'))
 write(8192+0x91,bytes.fromhex('c3801f'),bytes.fromhex('3a4fe2'))
 assert len(rom)==4194304 and all(a==b or i in written for i,(a,b) in enumerate(zip(old,rom)))
 out=R/('outputs/six-route-inland-zero-decode'+suffix);assert not out.exists();out.mkdir();(out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 result={'sha256':hashlib.sha256(rom).hexdigest(),'bytes':len(rom),'helper_bytes':len(code),'reader_copy_bytes':128+len(code),'changed_bytes':sum(a!=b for a,b in zip(old,rom)),'adopted':False,'scope':'Experimental choice0 mesh skip forpiece>=16,bit64 override retained. Coast/canyonoriginalpath. Native safety/pixels/performance pending.'}
 (out/'manifest.json').write_text(json.dumps(result,indent=2));print(result)
