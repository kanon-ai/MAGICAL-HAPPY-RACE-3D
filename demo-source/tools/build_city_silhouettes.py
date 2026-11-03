"""Replace forest components only within verified geometry-owned ROM spans."""
from pathlib import Path
import json,hashlib
from audit_stage_repack_space import audit
from mesh_geometry_codec import encode
from study_column_runs import column_pack,sample
R=Path(__file__).resolve().parents[1]
expected=(R/'work/city-silhouettes/city/outputs/city-expected.bin').read_bytes()
records=[expected[i:i+447] for i in range(0,len(expected),447)]
assert len(records)==4096
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-city-facade-variety-v2'+suffix);path=next(src.glob('*.rom'));old=path.read_bytes();rom=bytearray(old)
 geo=R/('outputs/six-route-forest-groves'+suffix)
 layout=json.loads((geo/'geometry-layout.json').read_text());forest_expected=(geo/'forest-expected.bin').read_bytes()
 _,_,patterns,groups,slots=audit(old,layout,forest_expected)
 space=json.loads((R/'outputs/city-repack-space.json').read_text())[suffix or 'internal']
 assert hashlib.sha256(old).hexdigest()==space['sha256']
 used=bytearray([1])*len(old)
 for at,n in space['spans']:used[at:at+n]=bytes(n)
 protected=bytes(used)
 lookup={}
 for ptr,(off,n,raw) in patterns.items():
  if not all(used[off:off+n]):continue
  blob=old[off:off+n];values=blob if raw else bytes(sample(blob,j) for j in range(32));lookup.setdefault(values,ptr)
 fields=[];new={}
 for g in range(128):
  fs=[]
  for f in range(447):
   values=bytes(records[g*32+j][f] for j in range(32));base=values[0];delta=bytes((x-base)&255 for x in values)
   if not any(delta):ref=None
   elif delta in lookup:
    ref=lookup[delta];off,n,_=patterns[ref];used[off:off+n]=b'\1'*n
   else:
    ref=delta
    if delta not in new:
     coded=column_pack(delta);raw=len(coded)>=32;new[delta]=(delta if raw else coded,raw)
   fs.append((base,ref))
  fields.append(fs)
 spans=[(0,175)]+[(175+j*30,30) for j in range(8)]+[(415,32)]
 def serialize(fs,ptrs):
  body=bytearray()
  for origin,count in spans:
   part=bytearray()
   for first in range(origin,origin+count,8):
    flag=len(part);part.append(0)
    for j in range(min(8,origin+count-first)):
     base,ref=fs[first+j];part.append(base)
     if ref is not None:
      part[flag]|=1<<j;b,addr=ptrs.get(ref,ref) if ptrs is not None else (0,0);part.extend(bytes([b])+addr.to_bytes(2,'little'))
   body.extend(len(part).to_bytes(2,'little'));body.extend(part)
  assert len(body)<=2048
  return len(body).to_bytes(2,'little')+body
 free=[]
 for start in slots:
  pos=start
  while pos<start+8192:
   if used[pos]:pos+=1;continue
   end=pos+1
   while end<start+8192 and not used[end]:end+=1
   free.append([pos,end-pos]);pos=end
 jobs=[(('g',g),len(serialize(fs,None))) for g,fs in enumerate(fields)]+[(('p',key),len(blob)) for key,(blob,raw) in new.items()]
 locations={};written=bytearray(len(old))
 for key,n in sorted(jobs,key=lambda x:x[1],reverse=True):
  candidates=[(size,k) for k,(at,size) in enumerate(free) if size>=n]
  assert candidates,('fragmented capacity',n,sum(x[1] for x in free))
  _,k=min(candidates);at,size=free[k];free[k]=[at+n,size-n];locations[key]=at;written[at:at+n]=b'\1'*n
 def pointer(at,raw=False):return (at//16384,0x4000+at%16384+(0x8000 if raw else 0))
 ptrs={}
 for key,(blob,raw) in new.items():
  at=locations['p',key];rom[at:at+len(blob)]=blob;ptrs[key]=pointer(at,raw)
 entries=[]
 for g,fs in enumerate(fields):
  blob=serialize(fs,ptrs);at=locations['g',g];rom[at:at+len(blob)]=blob;entries.append(pointer(at))
 before=b''.join(bytes([b])+addr.to_bytes(2,'little') for b,addr in layout['groups']['city']);at=old.find(before);assert at>=0 and old.find(before,at+1)<0
 protected=bytearray(protected);protected[at:at+384]=bytes(384)
 layout['groups']['city']=entries;after=b''.join(bytes([b])+addr.to_bytes(2,'little') for b,addr in entries);rom[at:at+384]=after;written[at:at+384]=b'\1'*384
 assert len(rom)==4194304
 for i,(x,y) in enumerate(zip(old,rom)):
  if x!=y:assert written[i] and not protected[i],i
 report=audit(rom,layout,forest_expected,{'city':expected})[0]
 out=R/('outputs/six-route-city-silhouettes'+suffix);out.mkdir(exist_ok=True)
 (out/path.name).write_bytes(rom);(out/'geometry-layout.json').write_text(json.dumps(layout));(out/'city-expected.bin').write_bytes(expected);(out/'forest-expected.bin').write_bytes(forest_expected)
 for name in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin','forest-atlas.bin'):(out/name).write_bytes((src/name).read_bytes())
 report.update(scope="City-only ROM repack with complete host decode verification; native driving pending",bytes=len(rom),new_patterns=len(new),remaining_repack_bytes=sum(x[1] for x in free),other_stages_code_art_exact=True,runtime_verified=False)
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(suffix,report,flush=True)
