"""Replace only the reserved 896-byte wall material; preserve renderer/gameplay."""
from pathlib import Path
import json,hashlib
from structure_vram_layout import validate,ART
R=Path(__file__).resolve().parents[1]
validate(dict(ART,tunnel_concrete=(192,754,64,14)))
material=(R/'assets/tunnel-material-v2/concrete-64x14.bin').read_bytes();assert len(material)==896
for suffix in ('','-external-88h'):
 src=R/'outputs'/('six-route-tunnel-div'+suffix);out=R/'outputs'/('six-route-tunnel-toned'+suffix);out.mkdir(exist_ok=True)
 p=next(src.glob('*.rom'));original=p.read_bytes();rom=bytearray(original);allowed=set()
 for y in range(14):
  v=(754+y-512)*256+192;at=(4+v//8192)*16384+8192+v%8192
  rom[at:at+64]=material[y*64:(y+1)*64];allowed.update(range(at,at+64))
 assert len(rom)==4194304 and all(i in allowed for i,(a,b) in enumerate(zip(original,rom)) if a!=b)
 target=out/p.name
 if target.exists():assert target.read_bytes()==rom,'Prior candidate must reproduce exactly'
 target.write_bytes(rom)
 for name in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(out/name).write_bytes((src/name).read_bytes())
 report=dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),code_unchanged=True,adopted=False)
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
