"""Lossless hot canyon columns in existing raw format; no runtime-code edits."""
from pathlib import Path
import json,hashlib,collections
from audit_forest_repack_space import audit
from study_column_runs import sample
R=Path(__file__).resolve().parents[1]
for ext in ('','-external-88h'):
 src=R/('outputs/six-route-forest-grove-art'+ext);path=next(src.glob('*.rom'));old=path.read_bytes();rom=bytearray(old)
 geo=R/('outputs/six-route-forest-groves'+ext);layout=json.loads((geo/'geometry-layout.json').read_text());expected=(geo/'forest-expected.bin').read_bytes()
 _,_,patterns,groups,slots=audit(old,layout,expected)
 used=bytearray(len(old));refs=collections.defaultdict(list);weight=collections.Counter()
 for off,n,raw in patterns.values():used[off:off+n]=b'\1'*n
 for stage,entries in layout['groups'].items():
  for bank,address in entries:
   at=bank*16384+address-0x4000;size=int.from_bytes(old[at:at+2],'little');used[at:at+size+2]=b'\1'*(size+2)
   cursor=at+2;field=0
   for count in [175]+[30]*8+[32]:
    length=int.from_bytes(old[cursor:cursor+2],'little');cursor+=2;end=cursor+length
    for first in range(0,count,8):
     flags=old[cursor];cursor+=1
     for j in range(min(8,count-first)):
      cursor+=1
      if flags&(1<<j):
       ptr=(old[cursor],int.from_bytes(old[cursor+1:cursor+3],'little'))
       if stage=='canyon' and not ptr[1]&0x8000:
        refs[ptr].append(cursor);weight[ptr]+=1 if field<175 or field>=415 else .2
       cursor+=3
      field+=1
    assert cursor==end
 free=[]
 for start in slots:
  pos=start
  while pos<start+8192:
   if used[pos]:pos+=1;continue
   end=pos+1
   while end<start+8192 and not used[end]:end+=1
   free.append([pos,end-pos]);pos=end
 scores=[]
 for ptr,sites in refs.items():
  off,n,_=patterns[ptr];blob=old[off:off+n];q=1;depth=0;visits=0;covered=0
  while covered<32:
   t=blob[q];q+=1;count=(t&63)+1;depth+=1;visits+=depth*count;covered+=count;q+=count if t>>6==0 else 2 if t>>6==3 else 1
  scores.append((weight[ptr]*(visits+32),ptr))
 changed=bytearray(len(old));selected=[]
 for score,ptr in sorted(scores,reverse=True)[:512]:
  candidates=[(n,k) for k,(off,n) in enumerate(free) if n>=32]
  if not candidates:break
  _,k=min(candidates);at,n=free[k];free[k]=[at+32,n-32]
  off,n,_=patterns[ptr];blob=old[off:off+n];raw=bytes(sample(blob,j) for j in range(32));rom[at:at+32]=raw;changed[at:at+32]=b'\1'*32
  new=bytes([at//16384])+(0xc000+at%16384).to_bytes(2,'little')
  for site in refs[ptr]:rom[site:site+3]=new;changed[site:site+3]=b'\1'*3
  selected.append({'old_pointer':ptr,'references':len(refs[ptr]),'score':score,'raw_offset':at})
 assert selected and len(rom)==4194304
 assert all(x==y or changed[i] for i,(x,y) in enumerate(zip(old,rom)))
 proof=audit(rom,layout,expected)[0]
 out=R/('outputs/six-route-canyon-raw-columns'+ext);out.mkdir(exist_ok=True);(out/path.name).write_bytes(rom)
 for p in src.glob('*.bin'):(out/p.name).write_bytes(p.read_bytes())
 proof.update(scope='All24576decodedrecords exact; only canyon column pointers and raw geometry payload change. Native verification pending.',raw_patterns=len(selected),additional_raw_bytes=len(selected)*32,selected=selected)
 (out/'manifest.json').write_text(json.dumps(proof,indent=2));print(ext,len(selected),len(selected)*32,hashlib.sha256(rom).hexdigest(),flush=True)
