"""Repack geometry and stage snow-city feather rows; no renderer change."""
from pathlib import Path
import json,hashlib,copy
from audit_stage_repack_space import audit
R=Path(__file__).resolve().parents[1];plan=json.loads((R/'outputs/snow-city-repack-layout-study.json').read_text());locations=plan['locations']
rows=json.loads((R/'assets/snow-city-transition-study/snow-city-24.json').read_text());data=(R/'assets/snow-city-transition-study/snow-city-24.rle').read_bytes()
def phys(b,a):return b*16384+(a&0x7fff)-0x4000
def ptr(at,raw=False):return (at//16384,0x4000+at%16384+(0x8000 if raw else 0))
def packed(p):return bytes([p[0]])+p[1].to_bytes(2,'little')
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-raw-reclaim'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old)
 if not suffix:assert hashlib.sha256(old).hexdigest()==plan['source_sha256']
 g=R/('outputs/six-route-city-silhouettes'+suffix);layout=json.loads((g/'geometry-layout.json').read_text());newlayout=copy.deepcopy(layout);forest=(g/'forest-expected.bin').read_bytes();city=(g/'city-expected.bin').read_bytes()
 _,_,patterns,groups,slots=audit(old,layout,forest,{'city':city})
 allowedslots=set(slots);written=bytearray(len(old));seam=json.loads((R/('outputs/six-route-early-seam-data'+suffix)/'manifest.json').read_text());protected=bytearray(len(old))
 for at,n in seam['writes']:protected[at:at+n]=bytes([1])*n
 def write(at,blob,geometry=True):
  n=len(blob);assert not any(written[at:at+n]) and not any(protected[at:at+n])
  if geometry:assert at//8192*8192 in allowedslots and at//8192==(at+n-1)//8192
  rom[at:at+n]=blob;written[at:at+n]=bytes([1])*n
 mappings={};groupplaces={};rowplaces={}
 for item in locations:
  kind,key,at,n=item['kind'],item['key'],item['at'],item['bytes']
  if kind=='pattern':
   key=tuple(key);origin,size,raw=patterns[key];assert n==size;write(at,old[origin:origin+n]);mappings[key]=ptr(at,raw)
  elif kind=='group':groupplaces[tuple(key)]=(at,n)
  else:
   i=key[0];row=rows[i];assert n==row['bytes'];write(at,data[row['offset']:row['offset']+n]);rowplaces[i]=ptr(at)
 for stage,entries in layout['groups'].items():
  for index,(bank,address) in enumerate(entries):
   origin=phys(bank,address);at,n=groupplaces[stage,index];blob=bytearray(old[origin:origin+n]);assert n==int.from_bytes(blob[:2],'little')+2
   cursor=2
   for count in [175]+[30]*8+[32]:
    length=int.from_bytes(blob[cursor:cursor+2],'little');cursor+=2;end=cursor+length
    for first in range(0,count,8):
     flags=blob[cursor];cursor+=1
     for j in range(min(8,count-first)):
      cursor+=1
      if flags&(1<<j):
       key=(blob[cursor],int.from_bytes(blob[cursor+1:cursor+3],'little'));blob[cursor:cursor+3]=packed(mappings[key]);cursor+=3
    assert cursor==end
   assert cursor==n;write(at,blob);newlayout['groups'][stage][index]=ptr(at)
  before=b''.join(packed(x) for x in entries);origin=old.find(before);assert origin>=0 and old.find(before,origin+1)<0
  write(origin,b''.join(packed(x) for x in newlayout['groups'][stage]),False)
 directory=b''.join(packed(rowplaces[i]) for i in range(len(rows)));at=phys(211,0x7944);assert len(directory)==546 and old[at:at+546]==b'\xff'*546;write(at,directory,False)
 assert all(a==b or written[i] for i,(a,b) in enumerate(zip(old,rom)))
 for at,n in seam['writes']:assert old[at:at+n]==rom[at:at+n]
 proof=audit(rom,newlayout,forest,{'city':city})[0]
 out=R/('outputs/six-route-snow-city-data'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 (out/'geometry-layout.json').write_text(json.dumps(newlayout));proof.update(bytes=len(rom),directory_address=0x7944,geometry_free_after=plan['geometry_free_after'],scope='All geometry relocated, every decoded record exact, old seams/code/art unchanged; new snow-city rows staged only; native pending',adopted=False)
 (out/'manifest.json').write_text(json.dumps(proof,indent=2));print(suffix,proof['rom_sha256'],flush=True)
