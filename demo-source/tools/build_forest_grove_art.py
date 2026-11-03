from pathlib import Path
import json,hashlib
from pack_atlas import pack
R=Path(__file__).resolve().parents[1];a=R/'assets/forest-grove-art-v1'
old=(R/'assets/forest-atlas.bin').read_bytes();new=(a/'forest-atlas.bin').read_bytes()
for i,(x,y) in enumerate(zip(old,new)):
 if x!=y:assert 128<=i//256<256 and i%256<78
before,old_used=pack(old,136);after,new_used=pack(new,136)
assert len(after)<=len(before),('extra bank needed',len(before),len(after))
for ext in ('','-external-88h'):
 src=R/('outputs/six-route-forest-groves'+ext);p=next(src.glob('*.rom'));rom=bytearray(p.read_bytes())
 for j,blob in enumerate(before):
  at=(136+j)*16384+8192;assert rom[at:at+8192]==blob,('baseline pack mismatch',j)
  if j<len(after):rom[at:at+8192]=after[j]
 out=R/('outputs/six-route-forest-grove-art'+ext);out.mkdir(exist_ok=True);(out/p.name).write_bytes(rom)
 for n in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(out/n).write_bytes((src/n).read_bytes())
 (out/'forest-atlas.bin').write_bytes(new)
 (out/'manifest.json').write_text(json.dumps({'bytes':len(rom),'sha256':hashlib.sha256(rom).hexdigest(),'old_packed_bytes':old_used,'new_packed_bytes':new_used,'banks':len(after),'scope':'Forest tree4 atlas only, existing palette, no geometry/code change. Runtime pending.'},indent=2));print(ext,old_used,new_used,len(after))
