"""Lossless raw/compressed pattern mix; isolated assets, no playable ROM edits."""
from pathlib import Path
from collections import Counter
import json,sys
from study_column_runs import sample
R=Path(__file__).resolve().parents[1];D=R/'work/column-dictionary';O=R/'work/hybrid-dictionary';O.mkdir(exist_ok=True)
if '--joined' in sys.argv:
 D=R/'work/joined-column-dictionary';O=R/'work/joined-hybrid-dictionary';O.mkdir(exist_ok=True)
stages=('coast','canyon','forest','snow','city','night')
index=(D/'index.bin').read_bytes();packed=(D/'patterns.bin').read_bytes()
refs={n:(D/f'{n}-references.bin').read_bytes() for n in stages}
weights=Counter()
for data in refs.values():
 for at in range(0,len(data),3):weights[int.from_bytes(data[at+1:at+3],'little')]+=1
columns=[];decoded=[];scores=[]
for i in range(len(index)//4):
 at=index[i*4]*8192+int.from_bytes(index[i*4+1:i*4+3],'little')
 c=packed[at:at+packed[at]+1];columns.append(c)
 decoded.append(bytes(sample(c,j) for j in range(32)))
 # Expected token visits for all 32 samples, weighted by all-stage use.
 p=1;covered=0;visits=0;depth=0
 while covered<32:
  t=c[p];p+=1;n=(t&63)+1;depth+=1;visits+=n*depth;covered+=n
  p+=n if t>>6==0 else 2 if t>>6==3 else 1
 cost=32-len(c)
 if i:scores.append((weights[i]*(visits+32)/max(1,cost),i,cost))
chosen=set();growth=0;budget=256*1024
for _,i,cost in sorted(scores,reverse=True):
 if growth+cost<=budget:chosen.add(i);growth+=cost
blocks=[];locations=[None]*len(columns)
for i in sorted(range(len(columns)),key=lambda i:32 if i in chosen else len(columns[i]),reverse=True):
 data=decoded[i] if i in chosen else columns[i]
 candidates=[j for j,b in enumerate(blocks) if len(b)+len(data)<=8192]
 slot=max(candidates,key=lambda j:len(blocks[j])) if candidates else len(blocks)
 if slot==len(blocks):blocks.append(bytearray())
 locations[i]=(slot,len(blocks[slot]),int(i in chosen));blocks[slot].extend(data)
assert len(blocks)<256
outindex=b''.join(bytes([slot])+offset.to_bytes(2,'little')+bytes([raw]) for slot,offset,raw in locations)
(O/'index.bin').write_bytes(outindex)
(O/'patterns.bin').write_bytes(b''.join(b+b'\xff'*(8192-len(b)) for b in blocks))
for name,data in refs.items():
 expected=(D/f'{name}-expected.bin').read_bytes();actual=bytearray(len(expected))
 for group in range(128):
  for field in range(447):
   at=(group*447+field)*3;base=data[at];i=int.from_bytes(data[at+1:at+3],'little')
   slot,offset,raw=locations[i];c=blocks[slot][offset:offset+(32 if raw else len(columns[i]))]
   values=c if raw else bytes(sample(c,j) for j in range(32))
   for j,value in enumerate(values):actual[(group*32+j)*447+field]=(base+value)&255
 assert actual==expected,name
report=dict(raw_patterns=len(chosen),total_patterns=len(columns),pattern_halfbanks=len(blocks),extra_padded_bytes=len(blocks)*8192-len(packed),all_24576_records_exact=True,weighted_raw_reference_fraction=sum(weights[i] for i in chosen)/sum(v for i,v in weights.items() if i),limitation='Offline only; native flag dispatch, physical ROM placement and speed unverified.')
(O/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
