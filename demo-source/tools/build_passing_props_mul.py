"""Replace scenery's software byte multiply with existing R800 MULUB."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
oldcode=bytes.fromhex('672e005506082930011910fa');newcode=bytes.fromhex('4bedc9c3e060')+bytes(6)
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-passing-props-fast'+suffix);out=R/('outputs/six-route-passing-props-mul'+suffix);out.mkdir(exist_ok=True)
 p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);at=211*16384+8192+0xd4
 assert old[at:at+12]==oldcode
 rom[at:at+12]=newcode
 (out/p.name).write_bytes(rom)
 for name in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(out/name).write_bytes((src/name).read_bytes())
 report=dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),patch_bytes=12,playable_adoption=False,runtime_verified=False)
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
