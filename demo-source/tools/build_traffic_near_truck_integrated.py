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
for suffix,expected in (('', '807b03e01e0ad3d18b07254c23e32e26818830e6d45bfb60a29cdc9d194ef41d'),('-external-88h','6ad7d8be53e447b70818646d90404feb852b45b32c0a911c2614e67945e9aac2')):
    src=R/('outputs/six-route-traffic-near-scratch-restore'+suffix)
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
    def near_faces(data):
        block=1024;count=data[block];assert count==46
        return b''.join(data[block+1+f*11:block+1+f*11+4]+data[block+1+count*11+f*8:block+1+count*11+f*8+8]+data[block+1+f*11+10:block+1+f*11+11] for f in range(0,count,2))
    before=near_faces(old_packet);after=near_faces(packet)
    start=206*16384+8192;end=start+8192
    at=old.find(before,start,end);assert at>=0 and old.find(before,at+1,end)<0
    assert len(before)==len(after)==299
    # Near table changes only its eight UV bytes, never indices/material flags.
    for i,(a,b) in enumerate(zip(before,after)):
        if a!=b:assert 4<=i%13<12
    rom[at:at+len(after)]=after;allowed.update(range(at,at+len(after)))
    changes=[i for i,(a,b) in enumerate(zip(old,rom)) if a!=b]
    assert len(rom)==4194304 and all(i in allowed for i in changes)
    assert rom[251*16384+8192+2048:251*16384+8192+2360]==old_packet[2048:]
    out=R/('outputs/six-route-traffic-near-truck-integrated'+suffix);out.mkdir(exist_ok=True)
    (out/path.name).write_bytes(rom)
    for asset in src.glob('*.bin'):(out/asset.name).write_bytes(asset.read_bytes())
    report=dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),changed_bytes=len(changes),
                runtime_code_geometry_palette_unchanged=True,added_bytes=0,adopted=False,
                scope='Truck side/rear UV and existing384-byte material only. Native visual verification pending; integrated with scratch-safe near renderer; native verification pending.')
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
