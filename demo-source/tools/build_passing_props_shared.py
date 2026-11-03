"""Replace scenery's software byte multiply with existing R800 MULUB."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
oldcode=bytes.fromhex('dde5dd');newcode=bytes.fromhex('c30066');wrapper=bytes.fromhex('eb2a47e23a4fe2c30064')
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-passing-props-mul'+suffix);out=R/('outputs/six-route-passing-props-shared'+suffix);out.mkdir(exist_ok=True)
 p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);at=211*16384+8192
 assert old[at:at+3]==oldcode
 assert old[at+0x600:at+0x600+len(wrapper)]==bytes([255])*len(wrapper)
 assert old[at+0x400:at+0x405]==bytes.fromhex("4f19cb7c28")
 rom[at:at+3]=newcode
 rom[at+0x600:at+0x600+len(wrapper)]=wrapper
 (out/p.name).write_bytes(rom)
 for name in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(out/name).write_bytes((src/name).read_bytes())
 report=dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),patch_bytes=13,playable_adoption=False,runtime_verified=False)
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
