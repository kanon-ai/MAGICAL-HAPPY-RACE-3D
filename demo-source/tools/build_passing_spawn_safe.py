"""Keep respawn candidates below the signed circular-distance boundary."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
assert 6000+4*240+4*240<8192
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-passing-beacons'+suffix);out=R/('outputs/six-route-passing-spawn-safe'+suffix);out.mkdir(exist_ok=True)
 p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);bank=206*16384+8192
 needle=bytes.fromhex('01581b');region=old[bank+0x200:bank+0x220];assert region.count(needle)==1
 at=bank+0x200+region.index(needle);rom[at:at+3]=bytes.fromhex('017017')
 assert len(rom)==4194304
 assert sum(a!=b for a,b in zip(old,rom))==2
 (out/p.name).write_bytes(rom)
 for name in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(out/name).write_bytes((src/name).read_bytes())
 report=dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),spawn_base=6000,maximum_candidate=7920,patch_address=0x6000+at-bank,playable_adoption=False,native_validation=False)
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
