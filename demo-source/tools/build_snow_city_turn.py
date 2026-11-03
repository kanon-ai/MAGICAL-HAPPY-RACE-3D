"""Place paired-turn geometry with protected seams and synchronized markers."""
from pathlib import Path
import runpy,json,hashlib,copy
from study_column_runs import column_pack,sample
from audit_stage_repack_space import audit
R=Path(__file__).resolve().parents[1]
ns=runpy.run_path(str(R/'tools/plan_snow_city_turn_fit.py'));assert ns['failure'] is None
n=ns['n'];placements=ns['placed'];refs=sorted(n['refs'],key=str)
def phys(bank,address):return bank*16384+(address&0x7fff)-0x4000
def pointer(at,raw=False):return (at//16384,0x4000+at%16384+(0x8000 if raw else 0))
def packed(p):return bytes([p[0]])+p[1].to_bytes(2,'little')
def group_data(fields,pointers):
 body=bytearray()
 for origin,count in [(0,175)]+[(175+j*30,30) for j in range(8)]+[(415,32)]:
  part=bytearray()
  for first in range(origin,origin+count,8):
   flag=len(part);part.append(0)
   for j in range(min(8,origin+count-first)):
    base,ref=fields[first+j];part.append(base)
    if ref is not None:part[flag]|=1<<j;part.extend(packed(pointers[ref]))
  body.extend(len(part).to_bytes(2,'little'));body.extend(part)
 return len(body).to_bytes(2,'little')+body
route=json.loads((R/'outputs/six-route-layout-lined-dedup/layout.json').read_text())
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-snow-city-ground'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);written=bytearray(len(old))
 layout=json.loads((src/'geometry-layout.json').read_text());newlayout=copy.deepcopy(layout)
 g=R/('outputs/six-route-city-silhouettes'+suffix)
 audit(old,layout,(g/'forest-expected.bin').read_bytes(),{'city':(g/'city-expected.bin').read_bytes()})
 def write(at,blob,geometry=True):
  end=at+len(blob);assert not any(written[at:end]) and not any(n['protected'][at:end])
  if geometry:assert at//8192*8192 in n['slots'] and at//8192==(end-1)//8192
  rom[at:end]=blob;written[at:end]=bytes([1])*len(blob)
 pointers={};group_places={};marker_at=None
 for job in placements:
  kind,key,at,size=job['kind'],job['key'],job['at'],job['bytes']
  if kind=='pattern':
   ref=refs[key]
   if isinstance(ref,bytes):values=ref
   else:
    start,length,raw=n['patterns'][ref];assert old[start:start+length]==n['rom'][start:start+length]
    values=n['decoded'][ref]
   if not isinstance(ref,bytes) and not n['patterns'][ref][2]:
    start,length,_=n['patterns'][ref];blob=old[start:start+length]
   else:blob=column_pack(values)
   raw=len(blob)>=32
   if raw:blob=values
   assert len(blob)==size and (blob if raw else bytes(sample(blob,j) for j in range(32)))==values
   write(at,blob);pointers[ref]=pointer(at,raw)
  elif kind=='group':group_places[key]=(at,size)
  else:
   marker_at=at;blob=(R/'work/snow-city-turn/snow/assets/road-markers.bin').read_bytes()[-8192:]
   assert at%16384==8192,'Marker reader hardcodes CPU6000'
   assert len(blob)==size==8192;write(at,blob)
 index=0
 for stage,entries in n['finalgroups'].items():
  for i,fields in enumerate(entries):
   at,size=group_places[index];blob=group_data(fields,pointers);assert len(blob)==size
   write(at,blob);newlayout['groups'][stage][i]=pointer(at);index+=1
  before=b''.join(packed(x) for x in layout['groups'][stage]);at=old.find(before)
  assert at>=0 and old.find(before,at+1)<0
  write(at,b''.join(packed(x) for x in newlayout['groups'][stage]),False)
 # Existing unique marker blocks and curve tables retain their allocations.
 for stage in ('snow','city'):
  original=R/f'work/lined-route-shapes/{stage}/assets';candidate=R/f'work/snow-city-turn/{stage}/assets'
  blocks=next(a['blocks'] for a in route['allocations'] if a['name']==stage+' markers')
  a=(original/'road-markers.bin').read_bytes();b=(candidate/'road-markers.bin').read_bytes()
  for i,block in enumerate(blocks):
   x,y=a[i*8192:(i+1)*8192],b[i*8192:(i+1)*8192]
   at=phys(block['bank'],block['address']);assert old[at:at+8192]==x
   if x==y or (stage=='snow' and i==15):continue
   users=sum(t['bank']==block['bank'] and t['address']==block['address'] for alloc in route['allocations'] for t in alloc['blocks']);assert users==1
   write(at,y,False)
  block=next(a['blocks'][0] for a in route['allocations'] if a['name']==stage+' curve');at=phys(block['bank'],block['address'])
  a=(original/'long-course.bin').read_bytes()[124::256];b=(candidate/'long-course.bin').read_bytes()[124::256]
  assert old[at:at+4096]==a
  write(at,b,False)
 block=next(a['blocks'][0] for a in route['allocations'] if a['name']=='route lookup directory')
 at=phys(block['bank'],block['address'])+3*54+15*3
 shared=next(a['blocks'][15] for a in route['allocations'] if a['name']=='snow markers')
 assert old[at:at+3]==packed((shared['bank'],shared['address']))
 write(at,packed(pointer(marker_at)),False)
 expected={stage:(R/f'work/snow-city-turn/{stage}/outputs/{stage}-expected.bin').read_bytes() for stage in ('snow','city')}
 proof=audit(rom,newlayout,(g/'forest-expected.bin').read_bytes(),expected)[0]
 assert len(rom)==4194304 and all(x==y or written[i] for i,(x,y) in enumerate(zip(old,rom)))
 out=R/('outputs/six-route-snow-city-turn'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 (out/'geometry-layout.json').write_text(json.dumps(newlayout))
 proof.update(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),adopted=False,geometry_free_bytes=34,marker_allocation=[marker_at,8192],scope='Paired curve, matched marker/curve tables, exact decoded geometry; native validation pending')
 (out/'manifest.json').write_text(json.dumps(proof,indent=2));print(suffix,proof['sha256'],flush=True)
