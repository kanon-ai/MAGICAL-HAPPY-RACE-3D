"""City-stage art preview only. Dependent transition bands are NOT rebuilt yet."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
sky=(R/'assets/city-alpine-v1/city-sky.bin').read_bytes();prior=(R/'assets/city-sky.bin').read_bytes()
assert len(sky)==len(prior)==19968
for suffix in ('','-external-88h'):
    src=R/('outputs/six-route-snow-city-trees'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);allowed=bytearray(len(old))
    for j in range(3):
        part=sky[j*8192:(j+1)*8192];at=(153+j)*16384+8192
        assert old[at:at+len(part)]==prior[j*8192:j*8192+len(part)]
        rom[at:at+len(part)]=part;allowed[at:at+len(part)]=b'\1'*len(part)
    assert len(rom)==4194304 and all(a==b or allowed[i] for i,(a,b) in enumerate(zip(old,rom)))
    out=R/('outputs/six-route-city-alpine-preview'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(rom)
    for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
    (out/'city-sky.bin').write_bytes(sky)
    (out/'manifest.json').write_text(json.dumps({'sha256':hashlib.sha256(rom).hexdigest(),'bytes':len(rom),'scope':'City panorama only; native city preview. Dependent snow/city and city/night strips stale; do not publish or call full-route-ready.','adopted':False},indent=2))
    print(out.name)
