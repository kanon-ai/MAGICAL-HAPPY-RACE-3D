from pathlib import Path
import argparse,subprocess,hashlib,json
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--name',default='general-bit-reader');args=p.parse_args()
assert args.name.replace('-','').isalnum()
w=R/'work'/('build-'+args.name);assert not w.exists();w.mkdir()
subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(R/'tools/general_bit_reader.asm'),str(w/'reader.bin'),str(w/'reader.sym')],check=True)
code=(w/'reader.bin').read_bytes();assert len(code)<=256
assert 'skip_invisible\tEQU 01F74H' in (w/'reader.sym').read_text()
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-inland-zero-decode'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old)
 assert old[0x2091:0x2094]==bytes.fromhex('c3801f')
 assert old[0x250b:0x250d]==(171).to_bytes(2,'little')
 rom[0x2600:0x2700]=code+bytes([255])*(256-len(code));rom[0x250b:0x250d]=len(code).to_bytes(2,'little');rom[0x2091:0x2094]=bytes.fromhex('c3741f')
 assert len(rom)==4194304 and all(a==b or 0x2600<=i<0x2700 or 0x250b<=i<0x250d or 0x2091<=i<0x2094 for i,(a,b) in enumerate(zip(old,rom)))
 out=R/('outputs/six-route-'+args.name+suffix);assert not out.exists();out.mkdir();(out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 report={'sha256':hashlib.sha256(rom).hexdigest(),'reader_bytes':len(code),'bytes':len(rom),'adopted':False,'scope':'Reader-only trial, data unchanged; native/pixel/performance proof separate'}
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
