"""Art-only truck UV/material update on the verified stable snow baseline."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
study=R/'outputs/truck-side-material-study'
packet=(study/'truck-packets.bin').read_bytes()
material=(study/'truck-material.bin').read_bytes()
old_packet=(R/'assets/truck-packets.bin').read_bytes()
vram=(R/'assets/vram.bin').read_bytes()
assert len(packet)==2360 and len(material)==384
for suffix,expected in (('', 'de8b2ebd5a2e2ede8e9e876485b35cba9ce5ed74adf55e17763e5b834f8285fb'),('-external-88h','64d41e168b48aaea88ef70f41230f858b4f133f5515a6e04bb426aa21f891fc7')):
    src=R/('outputs/six-route-snow-roadside-depth'+suffix)
    path=next(src.glob('*.rom'));old=path.read_bytes()
    assert hashlib.sha256(old).hexdigest()==expected
    rom=bytearray(old);allowed=set()
    at=251*16384+8192
    assert old[at:at+2360]==old_packet
    rom[at:at+2360]=packet;allowed.update(range(at,at+2048))
    for y in range(12):
        offset=(32+y)*256+224
        at=(12+offset//8192)*16384+8192+offset%8192
        assert old[at:at+32]==vram[65536+offset:65536+offset+32]
        rom[at:at+32]=material[y*32:(y+1)*32]
        allowed.update(range(at,at+32))
    changes=[i for i,(a,b) in enumerate(zip(old,rom)) if a!=b]
    assert len(rom)==4194304 and all(i in allowed for i in changes)
    assert rom[251*16384+8192+2048:251*16384+8192+2360]==old_packet[2048:]
    out=R/('outputs/six-route-truck-side-material'+suffix);out.mkdir(exist_ok=True)
    (out/path.name).write_bytes(rom)
    for asset in src.glob('*.bin'):(out/asset.name).write_bytes(asset.read_bytes())
    report=dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),changed_bytes=len(changes),
                runtime_code_geometry_palette_unchanged=True,added_bytes=0,adopted=False,
                scope='Truck side/rear UV and existing384-byte material only. Native visual verification pending; no clipping trial code included.')
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
