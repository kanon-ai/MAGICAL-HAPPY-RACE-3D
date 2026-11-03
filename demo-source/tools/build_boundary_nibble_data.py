"""Stage exact boundary assets but retain original runtime route directories."""
from pathlib import Path
import runpy,json,hashlib,copy
from audit_bitpacked_geometry import audit
R=Path(__file__).resolve().parents[1]
n=runpy.run_path(str(R/'tools/plan_boundary_nibble_fit.py'));assert n['failure'] is None
def pointer(at,raw=False):return (at//16384,0x4000+at%16384+(0x8000 if raw else 0))
def packed(p):return bytes([p[0]])+p[1].to_bytes(2,'little')
def group_data(fields,refs):
 body=bytearray()
 for origin,count in [(0,175)]+[(175+j*30,30) for j in range(8)]+[(415,32)]:
  part=bytearray()
  for first in range(origin,origin+count,8):
   flag=len(part);part.append(0)
   for j in range(min(8,origin+count-first)):
    base,key=fields[first+j];part.append(base)
    if key is not None:part[flag]|=1<<j;part.extend(packed(refs[key]))
  body.extend(len(part).to_bytes(2,'little'));body.extend(part)
 return len(body).to_bytes(2,'little')+body
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-bitpacked-nibble'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);written=bytearray(len(old))
 layout=json.loads((src/'geometry-layout.json').read_text());newlayout=copy.deepcopy(layout);g=R/('outputs/six-route-city-silhouettes'+suffix)
 forest=(g/'forest-expected.bin').read_bytes();city=(g/'city-expected.bin').read_bytes();audit(old,layout,forest,{'city':city})
 def write(at,blob,geometry=True):
  end=at+len(blob);assert not any(written[at:end]) and not any(n['protected'][at:end])
  if geometry:assert at//8192*8192 in n['slots'] and at//8192==(end-1)//8192
  rom[at:end]=blob;written[at:end]=bytes([1])*len(blob)
 refs={};places={}
 for job in n['placed']:
  kind,key,at,size=job['kind'],job['key'],job['at'],job['bytes'];places[kind,key]=(at,size)
  if kind=='pattern':
   value=n['keys'][int(key)];blob,raw=n['pool'][value];assert len(blob)==size;write(at,blob);refs[value]=pointer(at,raw)
  elif kind in ('marker','curve'):
   assert at%16384==8192
   if kind=='marker':
    stage,index=key.split(':');data=(R/f'work/snow-city-turn/{stage}/assets/road-markers.bin').read_bytes();blob=data[int(index)*8192:(int(index)+1)*8192]
   else:blob=(R/f'work/snow-city-turn/{key}/assets/long-course.bin').read_bytes()[124::256]+bytes([255])*4096
   assert len(blob)==size;write(at,blob)
 for stage,entries in n['groups'].items():
  for i,fields in enumerate(entries):
   at,size=places['group',f'{stage}:{i}'];blob=group_data(fields,refs);assert len(blob)==size;write(at,blob);newlayout['groups'][stage][i]=pointer(at)
  before=b''.join(packed(x) for x in layout['groups'][stage]);at=old.find(before);assert at>=0 and old.find(before,at+1)<0
  write(at,b''.join(packed(x) for x in newlayout['groups'][stage]),False)
 overlay=copy.deepcopy(newlayout)
 for stage,entries in n['overrides'].items():
  for i,fields in entries.items():
   at,size=places['override',f'{stage}:{i}'];blob=group_data(fields,refs);assert len(blob)==size;write(at,blob);overlay['groups'][stage][i]=pointer(at)
  at,size=places['directory',stage];blob=b''.join(packed(x) for x in overlay['groups'][stage]);assert len(blob)==size;write(at,blob)
 proof=audit(rom,newlayout,forest,{'city':city})[0]
 expected={s:(R/f'work/snow-city-turn/{s}/outputs/{s}-expected.bin').read_bytes() for s in ('snow','city')}
 alternate=audit(rom,overlay,forest,expected)[0]
 assert len(rom)==4194304 and all(x==y or written[i] for i,(x,y) in enumerate(zip(old,rom)))
 out=R/('outputs/six-route-boundary-nibble-data'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 (out/'geometry-layout.json').write_text(json.dumps(newlayout));(out/'boundary-geometry-layout.json').write_text(json.dumps(overlay))
 proof.update(bytes=len(rom),remaining_geometry_bytes=n['report']['remaining_bytes'],alternate_records_exact=alternate['all_24576_compact_records_exact'],adopted=False,scope='Original runtime directories preserved; boundary geometry/markers/curves staged only. Native relocation proof and boundary dispatch pending.')
 (out/'manifest.json').write_text(json.dumps(proof,indent=2));print(suffix,proof['rom_sha256'],flush=True)
