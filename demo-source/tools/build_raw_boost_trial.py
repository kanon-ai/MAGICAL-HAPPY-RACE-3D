"""Promote frequent compressed columns into unused ROM slots; no code changes."""
from pathlib import Path
from collections import Counter
import json,hashlib,sys
import numpy as np
from study_column_runs import sample
R=Path(__file__).resolve().parents[1]
D=R/'work/lined-column-dictionary';H=R/'work/lined-hybrid-dictionary'
layout=json.loads((R/'outputs/six-route-layout-lined-dedup/layout.json').read_text())
geom=json.loads((R/'outputs/dictionary-components-jump17-hybrid-lined/coast/geometry-layout.json').read_text())
index=(H/'index.bin').read_bytes();packed=(H/'patterns.bin').read_bytes()
names=('coast','canyon','forest','snow','city','night')
source=R/'outputs/six-route-ground-crop/MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom';original=source.read_bytes()
assert hashlib.sha256(original).hexdigest()=='49d778af9d8167788f718ed11280bb01e168c1987760b862be48c18e673762f3'
external=(R/'outputs/six-route-ground-crop-external-88h/MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom').read_bytes()
assert hashlib.sha256(external).hexdigest()=='c6f97abb3aee33a2456545a5fece24add15bbd3983d8e8c24012d4c667c8d41c'
io_diff=[i for i,(a,b) in enumerate(zip(original,external)) if a!=b]
free=[tuple(x) for x in layout['free_slots']];assert len(free)==45 and all(b<252 for b,o in free)
weights=Counter();uses=[];values={};old_pointers={};compressed={}
for identifier in range(1,len(index)//4):
 block,off,raw=index[identifier*4],int.from_bytes(index[identifier*4+1:identifier*4+3],'little'),index[identifier*4+3]
 physical=geom['physical_slots'][block];addr=0x4000+physical['offset']+off
 pointer=bytes([physical['bank']])+(addr|(0x8000 if raw else 0)).to_bytes(2,'little')
 old_pointers[identifier]=pointer
 at=physical['bank']*16384+physical['offset']+off
 if raw:
  v=packed[block*8192+off:block*8192+off+32]
  assert original[at:at+32]==v
 else:
  at2=block*8192+off;c=packed[at2:at2+packed[at2]+1];assert original[at:at+len(c)]==c
  v=bytes(sample(c,j) for j in range(32));compressed[identifier]=c
 values[identifier]=v
for stage,name in enumerate(names):
 refs=(D/f'{name}-references.bin').read_bytes();assert len(refs)==128*447*4
 for group,(bank,addr) in enumerate(geom['groups'][name]):
  origin=bank*16384+addr-0x4000;at=origin+2;size=int.from_bytes(original[origin:at],'little');field=0
  for count in [175]+[30]*8+[32]:
   length=int.from_bytes(original[at:at+2],'little');at+=2;end=at+length
   for first in range(0,count,8):
    flags=original[at];at+=1
    for within in range(min(8,count-first)):
     ref=(group*447+field)*4;base=refs[ref];identifier=int.from_bytes(refs[ref+1:ref+4],'little')
     assert original[at]==base;at+=1
     assert bool(flags&(1<<within))==bool(identifier)
     if identifier:
      assert original[at:at+3]==old_pointers[identifier],(name,group,field)
      uses.append((at,identifier));at+=3
      # Coast native renderer intentionally omits all meshes.
      if stage or not 175<=field<415:weights[identifier]+=1
     field+=1
   assert at==end
  assert field==447 and at==origin+2+size
scores=[]
for identifier,c in compressed.items():
 p=1;covered=0;visits=0;depth=0
 while covered<32:
  t=c[p];p+=1;n=(t&63)+1;depth+=1;visits+=n*depth;covered+=n
  p+=n if t>>6==0 else 2 if t>>6==3 else 1
 scores.append((weights[identifier]*(visits+32),identifier))
ranked=[i for _,i in sorted(scores,reverse=True) if weights[i]]
root=R/'outputs/raw-boost-study';root.mkdir(exist_ok=True);reports=[]
for slots in (8,16,24,32,40):
 O=R/f'outputs/six-route-raw-boost-{slots}';O.mkdir(exist_ok=True)
 chosen=ranked[:slots*256];assert len(chosen)==slots*256
 rom=bytearray(original);pointers={}
 for n,i in enumerate(chosen):
  bank,offset=free[n//256];offset+=(n%256)*32;at=bank*16384+offset
  rom[at:at+32]=values[i];pointers[i]=bytes([bank])+(0xc000+offset).to_bytes(2,'little')
 changed_pointers=0
 for at,i in uses:
  if i in pointers:rom[at:at+3]=pointers[i];changed_pointers+=1
 # Every native component is decoded from the final physical ROM and compared
 # to authored expected records; neither the promoted bytes nor IDs are trusted.
 decoded_cache={};record_count=0
 for name in names:
  expected=np.frombuffer((D/f'{name}-expected.bin').read_bytes(),dtype=np.uint8).reshape(4096,447)
  for group,(bank,addr) in enumerate(geom['groups'][name]):
   at=bank*16384+addr-0x4000+2;cols=[]
   for count in [175]+[30]*8+[32]:
    length=int.from_bytes(rom[at:at+2],'little');at+=2;end=at+length
    for first in range(0,count,8):
     flags=rom[at];at+=1
     for within in range(min(8,count-first)):
      base=rom[at];at+=1
      if flags&(1<<within):
       key=bytes(rom[at:at+3]);at+=3
       if key not in decoded_cache:
        b=key[0];a=int.from_bytes(key[1:],'little');pos=b*16384+(a&0x7fff)-0x4000
        raw=bool(a&0x8000);v=bytes(rom[pos:pos+32]) if raw else bytes(sample(rom[pos:pos+rom[pos]+1],j) for j in range(32))
        decoded_cache[key]=np.frombuffer(v,dtype=np.uint8)
       col=decoded_cache[key]+np.uint8(base)
      else:col=np.full(32,base,dtype=np.uint8)
      cols.append(col)
    assert at==end
   assert np.array_equal(np.stack(cols,axis=1),expected[group*32:(group+1)*32]),(slots,name,group)
   record_count+=32
 # All changed bytes must belong to selected free slots or pointer triples.
 allowed=np.zeros(len(rom),dtype=bool)
 for bank,offset in free[:slots]:allowed[bank*16384+offset:bank*16384+offset+8192]=True
 for at,i in uses:
  if i in pointers:allowed[at:at+3]=True
 diff=np.frombuffer(original,dtype=np.uint8)!=np.frombuffer(rom,dtype=np.uint8)
 assert not np.any(diff&~allowed) and record_count==24576
 (O/source.name).write_bytes(rom)
 ext=bytearray(rom)
 for at in io_diff:assert ext[at]==original[at];ext[at]=external[at]
 (O/'MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom').write_bytes(ext)
 report=dict(slots=slots,raw_patterns_added=len(chosen),bytes_used=slots*8192,free_bytes=(45-slots)*8192,changed_pointers=changed_pointers,all_24576_records_exact=True,code_art_audio_unchanged=True,weighted_raw_fraction=sum(w for i,w in weights.items() if i not in compressed or i in pointers)/sum(weights.values()),sha256=hashlib.sha256(rom).hexdigest(),external_sha256=hashlib.sha256(ext).hexdigest(),scope='Offline final physical ROM decoding only; native FPS and picture verification pending.')
 (O/'build-manifest.json').write_text(json.dumps(report,indent=2)+'\n');reports.append(report);print(report,flush=True)
(root/'capacity.json').write_text(json.dumps(reports,indent=2)+'\n')
