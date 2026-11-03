from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
def off(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
assert len((R/'work/portal-tree-mask/filter.bin').read_bytes())==192
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-city-tunnel-tree-clear'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();b=bytearray(old)
 base=next((R/('outputs/six-route-city-tunnel-portal-lod'+suffix)).glob('*.rom')).read_bytes()
 assert old[off(0xca20):off(0xca20)+3]==bytes.fromhex('cd5abd')
 assert old[off(0xb260):off(0xb260)+3]==bytes.fromhex('cd8ab2')
 b[off(0xb260):off(0xb260)+39]=base[off(0xb260):off(0xb260)+39]
 b[off(0xb34a):off(0xb34a)+6]=bytes.fromhex('cd8ab2c35abd')
 b[off(0xca20):off(0xca20)+3]=bytes.fromhex('cd4ab3')
 assert all(off(0xb260)<=i<off(0xb351) or off(0xca20)<=i<off(0xca20)+3 for i,(x,y) in enumerate(zip(old,b)) if x!=y)
 out=R/('outputs/six-route-city-tunnel-tree-clear-v2'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(b)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 report={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'scope':'Move tree filter before actual draw_objects CA20->BD5A, preserve original beacon/tunnel late hook. Native verification pending.'};(out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
