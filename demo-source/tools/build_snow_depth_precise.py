from pathlib import Path
import json,hashlib,argparse
from audit_current_snow_precise_space import inspect
from audit_bitpacked_geometry import audit,sample
from study_column_runs import column_pack
from study_boundary_bitpack import bitpack
R=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--name',default='snow-roadside-depth');args=parser.parse_args();assert args.name.replace('-','').isalnum()
plan=json.loads((R/'outputs/snow-depth-precise-placement.json').read_text());assert plan['failure'] is None
base=(R/'work/snow-roadside-depth/snow/outputs/snow-expected.bin').read_bytes();turn=(R/'work/snow-roadside-depth-turn/snow/outputs/snow-expected.bin').read_bytes()
unique={};refs=[]
for dataset in (base,turn):
 entries=[]
 for g in range(128):
  block=dataset[g*32*447:(g+1)*32*447]
  if block not in unique:unique[block]=len(unique)
  entries.append(unique[block])
 refs.append(entries)
def ptr(at,raw=False):return at//16384,0x4000+at%16384+(0x8000 if raw else 0)
def pack(p):return bytes([p[0]])+p[1].to_bytes(2,'little')
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-general-bit-reader'+suffix);path=next(src.glob('*.rom'));old=path.read_bytes();rom=bytearray(old)
 _,protected,patterns,groups,slots,layout,overlay=inspect(old,suffix)
 pool={}
 for ref,(at,n,raw) in patterns.items():
  if not all(protected[at:at+n]):continue
  blob=old[at:at+n];values=blob if raw else bytes(sample(blob,j) for j in range(32));pool.setdefault(values,ref)
 written=bytearray(len(old));group_places={}
 def write(at,data,geometry=True):
  n=len(data);assert not any(written[at:at+n])
  if geometry:
   assert at//8192==(at+n-1)//8192 and at//8192*8192 in slots and not any(protected[at:at+n])
  rom[at:at+n]=data;written[at:at+n]=bytes([1])*n
 for job in plan['placements']:
  if job['kind']=='group':group_places[job['key']]=job;continue
  values=bytes.fromhex(job['key']);rle=column_pack(values);bp=bitpack(values)
  raw=len(values)<=min(len(rle),len(bp));blob=values if raw else min((rle,bp),key=len)
  assert len(blob)==job['bytes'] and (blob if raw else bytes(sample(blob,j) for j in range(32)))==values
  write(job['at'],blob);pool[values]=ptr(job['at'],raw)
 pointers=[]
 for block,key in unique.items():
  fields=[]
  for f in range(447):
   values=block[f::447];delta=bytes((v-values[0])&255 for v in values);fields.append((values[0],pool[delta] if any(delta) else None))
  body=bytearray()
  for first,count in [(0,175)]+[(175+j*30,30) for j in range(8)]+[(415,32)]:
   part=bytearray()
   for start in range(first,first+count,8):
    flag=len(part);part.append(0)
    for j in range(min(8,first+count-start)):
     value,ref=fields[start+j];part.append(value)
     if ref is not None:part[flag]|=1<<j;part.extend(pack(ref))
   body.extend(len(part).to_bytes(2,'little'));body.extend(part)
  blob=len(body).to_bytes(2,'little')+body;job=group_places[key];assert len(blob)==job['bytes'];write(job['at'],blob);pointers.append(ptr(job['at']))
 directories=[]
 assert bytes.fromhex('21006811001001000cedb0') in old[8192:8192+0x56], 'Runtime directory loader changed'
 for table,indices,at in zip((layout,overlay),refs,(0x2c80,0x3100)):
  before=b''.join(pack(p) for p in table['groups']['snow']);assert old[at:at+384]==before
  entries=[pointers[i] for i in indices];write(at,b''.join(pack(p) for p in entries),False);table['groups']['snow']=entries;directories.append(at)
 forest=(R/('outputs/six-route-forest-roadside-depth'+suffix)/'forest-expected.bin').read_bytes();city=(R/('outputs/six-route-city-silhouettes'+suffix)/'city-expected.bin').read_bytes()
 first=audit(rom,layout,forest,{'snow':base,'city':city})[0]
 second=audit(rom,overlay,forest,{'snow':turn,'city':(R/'work/snow-city-turn/city/outputs/city-expected.bin').read_bytes()})[0]
 assert first['all_24576_compact_records_exact'] and second['all_24576_compact_records_exact']
 assert len(rom)==4194304 and all(a==b or written[i] for i,(a,b) in enumerate(zip(old,rom)))
 out=R/('outputs/six-route-'+args.name+suffix);assert not out.exists();out.mkdir();(out/path.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 (out/'geometry-layout.json').write_text(json.dumps(layout));(out/'boundary-geometry-layout.json').write_text(json.dumps(overlay));(out/'snow-expected.bin').write_bytes(base);(out/'snow-turn-expected.bin').write_bytes(turn)
 report={'sha256':hashlib.sha256(rom).hexdigest(),'bytes':len(rom),'remaining_repack_bytes':plan['remaining_bytes'],'base_records_exact':True,'alternate_records_exact':True,'other_stages_code_art_preserved':True,'directory_offsets':directories,'native_verified':False,'scope':'Paired snow scenery repack; all decoded records exact, native rendering/performance pending'}
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(suffix,report,flush=True)
