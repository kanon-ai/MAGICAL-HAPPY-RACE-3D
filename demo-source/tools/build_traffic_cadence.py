from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
for ext in ('','-external-88h'):
 src=R/('outputs/six-route-tunnel-muted'+ext);dest=R/('outputs/six-route-traffic-cadence'+ext);dest.mkdir(exist_ok=True);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);start=206*16384+8192+256;needle=bytes.fromhex('3a4fe880e6ff28');at=old.find(needle,start,start+128);assert at>=0 and old.find(needle,at+1,start+128)<0
 rom[at+5]=127;assert [i for i,(a,b) in enumerate(zip(old,rom)) if a!=b]==[at+5];(dest/p.name).write_bytes(rom)
 for n in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(dest/n).write_bytes((src/n).read_bytes())
 (dest/'manifest.json').write_text(json.dumps({'sha256':hashlib.sha256(rom).hexdigest(),'bytes':len(rom),'offset':at+5,'old_mask':255,'new_mask':127,'scope':'Ordinary lane decision cadence only; existing clearance, lane sizes and movement preserved. Trial, runtime pending.'},indent=2));print(dest.name,hex(at+5))
