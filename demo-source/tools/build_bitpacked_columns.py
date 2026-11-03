"""In-place exact smaller-column replacement; no road/traffic/art changes."""
from pathlib import Path
import json,hashlib
from audit_stage_repack_space import audit as old_audit
from audit_bitpacked_geometry import audit
from study_column_runs import sample
from study_boundary_bitpack import bitpack,unpack
R=Path(__file__).resolve().parents[1]
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-bitpacked-reader-v2'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old)
 layout=json.loads((src/'geometry-layout.json').read_text());g=R/('outputs/six-route-city-silhouettes'+suffix)
 forest=(g/'forest-expected.bin').read_bytes();city=(g/'city-expected.bin').read_bytes()
 _,_,patterns,_,_=old_audit(old,layout,forest,{'city':city})
 selected={};allowed=bytearray(len(old));freed=[]
 for ptr,(at,n,raw) in patterns.items():
  values=old[at:at+n] if raw else bytes(sample(old[at:at+n],j) for j in range(32))
  blob=bitpack(values)
  if len(blob)>=n:continue
  assert bytes(unpack(blob,j) for j in range(32))==values
  selected[ptr]=(at,n,len(blob));rom[at:at+len(blob)]=blob;allowed[at:at+len(blob)]=bytes([1])*len(blob)
  freed.append([at+len(blob),n-len(blob)])
 count=0
 for entries in layout['groups'].values():
  for bank,address in entries:
   at=bank*16384+(address&32767)-16384;end=at+2+int.from_bytes(old[at:at+2],'little');cursor=at+2
   for size in [175]+[30]*8+[32]:
    length=int.from_bytes(old[cursor:cursor+2],'little');cursor+=2;partend=cursor+length
    for first in range(0,size,8):
     flags=old[cursor];cursor+=1
     for j in range(min(8,size-first)):
      cursor+=1
      if flags&(1<<j):
       ptr=(old[cursor],int.from_bytes(old[cursor+1:cursor+3],'little'))
       if ptr in selected:rom[cursor+2]&=127;allowed[cursor+2]=1;count+=1
       cursor+=3
    assert cursor==partend
   assert cursor==end
 assert all(x==y or allowed[i] for i,(x,y) in enumerate(zip(old,rom)))
 proof=audit(rom,layout,forest,{'city':city})[0]
 out=R/('outputs/six-route-bitpacked-columns'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 (out/'geometry-layout.json').write_bytes((src/'geometry-layout.json').read_bytes())
 proof.update(bytes=len(rom),converted_patterns=len(selected),updated_references=count,nominal_freed_bytes=sum(n for _,n in freed),freed_spans=freed,adopted=False,scope='All24576decodedrecords exact. In-place freed tails fragmented; native rendering/fps pending.')
 (out/'manifest.json').write_text(json.dumps(proof,indent=2));print(suffix,proof['rom_sha256'],proof['nominal_freed_bytes'],flush=True)
