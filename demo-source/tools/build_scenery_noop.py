"""Skip identity scenery loops in verified retired instruction gaps only."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
patches=[(0xd9a1,'c384db','c3a4d9'),(0xd9a4,'d60838073a4fe2d60e3818','3a4fe2fe0eda84dbc3c6a9'),(0xa9c6,'06dd9e07e2cfa9ee','793cca7fdbc384db')]
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-grove-understory'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old)
 bounds=(R/'outputs/six-route-passing-bounds/bounds.bin').read_bytes();assert len(bounds)==70 and old[off(0xa980):off(0xa9c6)]==bounds
 assert old[off(0xdb7f):off(0xdb7f)+5]==bytes.fromhex('ddf9dde1c9')
 for address,before,after in patches:
  a=off(address);x=bytes.fromhex(before);y=bytes.fromhex(after);assert len(x)==len(y) and old[a:a+len(x)]==x
  rom[a:a+len(y)]=y
 out=R/('outputs/six-route-scenery-noop'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 result=dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),source_sha256=hashlib.sha256(old).hexdigest(),changed_bytes=sum(x!=y for x,y in zip(old,rom)),patches=patches,adopted=False,scope='Only skip remaining appearance loop when piece>=14 and keep==255. Banks and data unchanged. Native tests pending.')
 (out/'manifest.json').write_text(json.dumps(result,indent=2));print(out.name,result['changed_bytes'])
