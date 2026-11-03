"""Preserve the preceding simulation gap when detecting a player overtake."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
oldcode=bytes.fromhex('2141e8097e23462147e296234f789ee63f477912137812')
newcode=bytes.fromhex('216ce8097e23464f7912137812');newcode+=bytes(len(oldcode)-len(newcode))
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-passing-beacons'+suffix);out=R/('outputs/six-route-passing-gap-history'+suffix);out.mkdir(exist_ok=True)
 p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old)
 matches=[a for a in range(0x9fa3,0xa03b) if old[off(a):off(a)+len(oldcode)]==oldcode];assert len(matches)==1
 a=matches[0];rom[off(a):off(a)+len(oldcode)]=newcode
 (out/p.name).write_bytes(rom)
 for name in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(out/name).write_bytes((src/name).read_bytes())
 report=dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),patch_address=a,patch_bytes=len(oldcode),playable_adoption=False,native_validation=False)
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
