"""Stage feather data in unreferenced geometry spans; renderer not installed yet."""
from pathlib import Path
import json,hashlib
from audit_forest_repack_space import audit
R=Path(__file__).resolve().parents[1]
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-passing-props-memo'+suffix);path=next(src.glob('*.rom'));old=path.read_bytes();rom=bytearray(old)
 geo=R/('outputs/six-route-forest-groves'+suffix);layout=json.loads((geo/'geometry-layout.json').read_text());expected=(geo/'forest-expected.bin').read_bytes()
 _,_,patterns,groups,slots=audit(old,layout,expected)
 used=bytearray(len(old))
 for at,n,raw in patterns.values():used[at:at+n]=b'\1'*n
 for entries in layout['groups'].values():
  for bank,address in entries:
   at=bank*16384+address-0x4000;n=int.from_bytes(old[at:at+2],'little')+2;used[at:at+n]=b'\1'*n
 free=[]
 for start in slots:
  at=start
  while at<start+8192:
   if used[at]:at+=1;continue
   end=at+1
   while end<start+8192 and not used[end]:end+=1
   free.append([at,end-at]);at=end
 original_free=sum(n for _,n in free);directory=bytearray();writes=[]
 for name in ('coast-canyon-24','canyon-forest-24'):
  root=R/'assets/early-transition-bands';rows=json.loads((root/(name+'.json')).read_text());data=(root/(name+'.rle')).read_bytes()
  for row in rows:
   n=row['bytes'];candidates=[(size,k) for k,(at,size) in enumerate(free) if size>=n];assert candidates,(name,row)
   _,k=min(candidates);at,size=free[k];free[k]=[at+n,size-n]
   assert not any(used[at:at+n]);blob=data[row['offset']:row['offset']+n];rom[at:at+n]=blob
   directory+=bytes([at//16384])+(0x4000+at%16384).to_bytes(2,'little');writes.append([at,n])
 d=211*16384+8192+0x1500;assert len(directory)==1092 and old[d:d+len(directory)]==b'\xff'*len(directory)
 rom[d:d+len(directory)]=directory;writes.append([d,len(directory)])
 mask=bytearray(len(old))
 for at,n in writes:mask[at:at+n]=b'\1'*n
 assert all(a==b or mask[i] for i,(a,b) in enumerate(zip(old,rom)))
 proof=audit(rom,layout,expected)[0]
 out=R/('outputs/six-route-early-seam-data'+suffix);out.mkdir(exist_ok=True);(out/path.name).write_bytes(rom)
 for p in src.glob('*.bin'):(out/p.name).write_bytes(p.read_bytes())
 proof.update(scope='Data-only staging; no renderer hook installed. All24576course records remain exact.',geometry_free_before=original_free,geometry_free_after=sum(n for _,n in free),directory_address=0x7500,writes=writes,sha256=hashlib.sha256(rom).hexdigest())
 (out/'manifest.json').write_text(json.dumps(proof,indent=2));print(suffix,original_free,sum(n for _,n in free),flush=True)
