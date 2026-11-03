from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-city-tunnel-depth-lod'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();b=bytearray(old)
 donor=next((R/('outputs/six-route-city-tunnel-tree-clear-v2'+suffix)).glob('*.rom')).read_bytes()
 assert old[off(0xca20):off(0xca20)+3]==bytes.fromhex('cd5abd')
 assert donor[off(0xca20):off(0xca20)+3]==bytes.fromhex('cd4ab3')
 assert donor[off(0xb34a):off(0xb34a)+6]==bytes.fromhex('cd8ab2c35abd')
 b[off(0xca20):off(0xca20)+3]=donor[off(0xca20):off(0xca20)+3]
 b[off(0xb28a):off(0xb350)]=donor[off(0xb28a):off(0xb350)]
 assert len(b)==4194304 and all(off(0xb28a)<=i<off(0xb350) or off(0xca20)<=i<off(0xca20)+3 for i,(x,y) in enumerate(zip(old,b)) if x!=y)
 assert b[off(0xb260):off(0xb260)+39]==old[off(0xb260):off(0xb260)+39]
 out=R/('outputs/six-route-city-tunnel-depth-lod-tree'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(b)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 report={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'scope':'Validated tree408 filter merged with experimental far-depth lining LOD; late tunnel pointer preserved. Runtime validation pending.'};(out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
