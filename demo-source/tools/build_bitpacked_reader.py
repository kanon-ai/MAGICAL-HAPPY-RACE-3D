"""Install hybrid-reader extension only; leave every course/data byte unchanged."""
from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parents[1];W=R/'work/bitpacked-reader';W.mkdir(exist_ok=True)
reader='''org 01f00h
 ld c,a
 bit 7,(hl)
 jp nz,bitpacked_sample
 inc hl
 ld a,(hl)
 jp 0f169h
'''+(R/'tools/bitpacked_sample.asm').read_text()
(W/'reader.asm').write_text(reader)
pasmo='C:/Software/Pasmo/pasmo.exe'
subprocess.run([pasmo,'--bin',str(W/'reader.asm'),str(W/'reader.bin')],check=True)
blob=(W/'reader.bin').read_bytes();assert len(blob)<256
loader=f'''org 06500h
 xor a
 ld (06000h),a
 ld hl,06600h
 ld de,01f00h
 ld bc,{len(blob)}
 ldir
 ld hl,02000h
 ret
'''
(W/'loader.asm').write_text(loader)
subprocess.run([pasmo,'--bin',str(W/'loader.asm'),str(W/'loader.bin')],check=True)
loader=(W/'loader.bin').read_bytes();assert len(loader)<256
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-snow-city-ground'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);allowed=set()
 def write(at,new,before):
  assert old[at:at+len(new)]==before
  rom[at:at+len(new)]=new;allowed.update(range(at,at+len(new)))
 write(8192+42,bytes.fromhex('cd0065'),bytes.fromhex('210020'))
 write(8192+0x166,bytes.fromhex('c3001f'),bytes.fromhex('4f237e'))
 write(0x2500,loader,b'\xff'*len(loader));write(0x2600,blob,b'\xff'*len(blob))
 assert len(rom)==4194304 and all(x==y or i in allowed for i,(x,y) in enumerate(zip(old,rom)))
 out=R/('outputs/six-route-bitpacked-reader'+suffix);out.mkdir(exist_ok=True)
 (out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 (out/'geometry-layout.json').write_bytes((src/'geometry-layout.json').read_bytes())
 report={'sha256':hashlib.sha256(rom).hexdigest(),'bytes':len(rom),'reader_bytes':len(blob),'reader_cache_segment_address':0x1f00,'changed_offsets':sorted(i for i,(x,y) in enumerate(zip(old,rom)) if x!=y),'scope':'Decoder dispatch/boot helper only; every geometry/art/gameplay byte unchanged; native integration pending'}
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(suffix,report['sha256'])
