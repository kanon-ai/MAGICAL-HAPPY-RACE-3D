"""Bake interior lighting into an isolated indexed material; keep the shared palette."""
from pathlib import Path
import re,json,hashlib
from pack_atlas import pack
R=Path(__file__).resolve().parents[1]
old=(R/'outputs/six-route-full-lined-rock-bore-rim-anticipate/scene-1-atlas.bin').read_bytes()
values=[int(x) for x in re.findall(r'\d+',(R/'src/palette_data.h').read_text().split('{')[1].split('}')[0])]
palette=[values[i:i+3] for i in range(0,768,3)]
# Offline lighting lookup: no extra runtime shading or global palette changes.
lookup=[]
for color in palette:
 target=[v*.55 for v in color]
 lookup.append(min(range(1,256),key=lambda i:sum(w*(palette[i][k]-target[k])**2 for k,w in enumerate((2,4,1)))))
new=bytearray(old)
for y in range(64):
 for x in range(50):new[(y+64)*256+206+x]=lookup[old[y*256+6+x]]
assert all(a==b or (64<=i//256<128 and 206<=i%256<256) for i,(a,b) in enumerate(zip(old,new)))
before,old_used=pack(old,128);after,new_used=pack(new,128)
assert len(after)<=len(before), 'Do not consume another ROM bank'
for suffix,expected in (('', 'eb41c0bc3818502112076a43a2e5b471344a816b50804000eaf4942a49728b29'),('-external-88h','e7e8291cef451c78d1cd8879b79fffb59c41fd098391ee1524f6c99ae94e796c')):
 src=R/('outputs/six-route-rock-bore-shadow'+suffix);p=next(src.glob('*.rom'));data=p.read_bytes()
 assert hashlib.sha256(data).hexdigest()==expected
 rom=bytearray(data)
 for i,blob in enumerate(before):
  at=(128+i)*16384+8192;assert rom[at:at+8192]==blob
  rom[at:at+8192]=after[i] if i<len(after) else b'\xff'*8192
 assert len(rom)==4194304
 out=R/('outputs/six-route-rock-bore-shaded'+suffix);out.mkdir(exist_ok=True)
 (out/p.name).write_bytes(rom)
 for asset in src.glob('*.bin'):(out/asset.name).write_bytes(asset.read_bytes())
 (out/'canyon-atlas.bin').write_bytes(new)
 report=dict(sha256=hashlib.sha256(rom).hexdigest(),bytes=len(rom),old_packed_bytes=old_used,new_packed_bytes=new_used,banks=len(after),palette_unchanged=True,material_rect=[206,832,50,64],runtime_verified=False,adopted=False)
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
