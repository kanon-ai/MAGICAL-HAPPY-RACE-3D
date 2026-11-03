"""Promote hot compressed patterns without changing code or existing allocations."""
from pathlib import Path
from collections import Counter
import json,hashlib
from study_column_runs import sample
R=Path(__file__).resolve().parents[1]
layout=json.loads((R/'outputs/dictionary-components-jump17-hybrid-lined/coast/geometry-layout.json').read_text())
free=json.loads((R/'outputs/decoder-copy-review/remaining-layout-slots.json').read_text())['still_blank_slots']
assert free==[[208,8192],[209,8192],[210,8192],[211,8192]]
def physical(bank,address):
 address&=0x7fff
 assert 0x4000<=address<0x8000
 return bank*16384+address-0x4000
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-traffic-overtake'+suffix);O=R/('outputs/six-route-decoder-hot-raw'+suffix);O.mkdir(exist_ok=True)
 rom=bytearray((src/name).read_bytes());before=bytes(rom)
 refs=[];weights=Counter();patterns={};visits={}
 for stage,groups in layout['groups'].items():
  assert len(groups)==128
  for bank,address in groups:
   at=physical(bank,address);size=int.from_bytes(rom[at:at+2],'little');at+=2;end=at+size
   for count in [175]+[30]*8+[32]:
    length=int.from_bytes(rom[at:at+2],'little');at+=2;part_end=at+length
    for start in range(0,count,8):
     flags=rom[at];at+=1
     for k in range(min(8,count-start)):
      at+=1 # base
      if flags&(1<<k):
       pb=rom[at];pa=int.from_bytes(rom[at+1:at+3],'little');key=(pb,pa)
       if not pa&0x8000:
        refs.append((at,key));weights[key]+=1
        if key not in patterns:
         p=physical(pb,pa);coded=bytes(rom[p:p+rom[p]+1])
         patterns[key]=bytes(sample(coded,i) for i in range(32))
         pos=1;covered=0;depth=0;v=0
         while covered<32:
          token=coded[pos];pos+=1;n=(token&63)+1;depth+=1;v+=n*depth;covered+=n
          pos+=n if token>>6==0 else 2 if token>>6==3 else 1
         assert covered==32 and pos==len(coded)
         visits[key]=v
       at+=3
    assert at==part_end,(stage,at,part_end)
   assert at==end,(stage,at,end)
 chosen=sorted(patterns,key=lambda k:(weights[k]*visits[k],weights[k],k),reverse=True)[:1024]
 allowed=set();mapping={}
 for bank,offset in free:assert rom[bank*16384+offset:bank*16384+offset+8192]==b'\xff'*8192
 for i,key in enumerate(chosen):
  bank,offset=free[i//256];local=(i%256)*32;at=bank*16384+offset+local
  rom[at:at+32]=patterns[key];allowed.update(range(at,at+32));mapping[key]=(bank,0x8000|0x4000|offset|local)
 changed=0
 for at,key in refs:
  if key in mapping:
   bank,address=mapping[key];replacement=bytes([bank])+address.to_bytes(2,'little')
   rom[at:at+3]=replacement;allowed.update(range(at,at+3));changed+=1
   assert bytes(rom[physical(bank,address):physical(bank,address)+32])==patterns[key]
 assert all(i in allowed for i,(a,b) in enumerate(zip(before,rom)) if a!=b)
 assert len(rom)==4194304
 (O/name).write_bytes(rom)
 for asset in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(O/asset).write_bytes((src/asset).read_bytes())
 (O/'manifest.json').write_text(json.dumps(dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),promoted_patterns=len(chosen),patched_references=changed,compressed_references_before=len(refs),extra_bytes=32768,code_unchanged=True,scope='All six stages, existing compressed groups parsed with exact length assertions; each promoted column equals all32 decoded samples. Native verification pending.'),indent=2))
 print(O,changed,len(refs))
