from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parents[1]
for ext in ('','-external-88h'):
 src=r/('outputs/six-route-traffic-cadence'+ext);out=r/('outputs/six-route-forest-understory'+ext);out.mkdir(exist_ok=True);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);at=214*16384+8192+0x1480;assert old[at:at+9]==bytes.fromhex('dd7ef8fe023e05300e');rom[at+6]=7
 assert [i for i,(a,b) in enumerate(zip(old,rom)) if a!=b]==[at+6];(out/p.name).write_bytes(rom)
 for n in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(out/n).write_bytes((src/n).read_bytes())
 (out/'manifest.json').write_text(json.dumps({'sha256':hashlib.sha256(rom).hexdigest(),'bytes':len(rom),'scope':'Forest kinds2/3 shrub7 insteadtree5; count/placement/traffic unchanged. Visual trial.'},indent=2))
