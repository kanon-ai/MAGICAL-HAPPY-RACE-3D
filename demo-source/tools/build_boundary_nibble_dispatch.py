"""Use alternate geometry/markers/curve only on actual pieces31 and32."""
from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];W=R/'work/boundary-nibble-dispatch';W.mkdir(exist_ok=True)
placements=json.loads((R/'outputs/boundary-nibble-plan/placement.json').read_text());places={(x['kind'],x['key']):(x['at'],x['bytes']) for x in placements}
def pointer(at):return (at//16384,0x4000+at%16384)
def packed(p):return bytes([p[0]])+p[1].to_bytes(2,'little')
def physical(b,a):return b*16384+a-0x4000
def codeoff(a):return (1+(a-0x8000)//8192)*16384+8192+(a-0x8000)%8192
def assemble(name,s):
 (W/f'{name}.asm').write_text(s)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(W/f'{name}.asm'),str(W/f'{name}.bin')],check=True)
 return (W/f'{name}.bin').read_bytes()
selector=assemble('geometry-selector','''org 01d00h
 cp 31
 jr z,snow
 cp 32
 jr z,city
 rrca
 rrca
 rrca
 and 7
 ret
snow:
 ld a,6
 ret
city:
 ld a,7
 ret
''')
appearance=assemble('appearance-normalize','''org 0f2f1h
 cp 6
 jr c,normal
 sub 3
normal:
 push hl
 ld l,a
 ld h,0
 jp 0f271h
''');assert len(appearance)==13
reader=(R/'work/bitpacked-nibble-reader/reader.bin').read_bytes()
loader=assemble('loader',f'''org 06500h
 xor a
 ld (06000h),a
 ld hl,06600h
 ld de,01f00h
 ld bc,{len(reader)}
 ldir
 ld hl,06700h
 ld de,01d00h
 ld bc,{len(selector)}
 ldir
 ld hl,02000h
 ret
''');assert len(loader)<256 and len(selector)<256
route_layout=json.loads((R/'outputs/six-route-layout-lined-dedup/layout.json').read_text())
route_block=next(x['blocks'][0] for x in route_layout['allocations'] if x['name']=='route lookup directory')
for suffix in ('','-external-88h'):
 src=R/('outputs/six-route-boundary-nibble-data'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);written=bytearray(len(old))
 layout=json.loads((src/'geometry-layout.json').read_text());overlay=json.loads((src/'boundary-geometry-layout.json').read_text())
 protected=bytearray(len(old))
 for at,size in json.loads((R/'outputs/six-route-early-seam-data/manifest.json').read_text())['writes']:protected[at:at+size]=bytes([1])*size
 for item in json.loads((R/'outputs/snow-city-repack-layout-study.json').read_text())['locations']:
  if item['kind']=='snow-city':protected[item['at']:item['at']+item['bytes']]=bytes([1])*item['bytes']
 occupied=bytearray(protected)
 for item in placements:occupied[item['at']:item['at']+item['bytes']]=bytes([1])*item['bytes']
 route_at=None
 for item in layout['physical_slots']:
  start=item['bank']*16384+item['offset'];cursor=start
  while cursor<start+8192:
   if occupied[cursor]:cursor+=1;continue
   end=cursor+1
   while end<start+8192 and not occupied[end]:end+=1
   if end-cursor>=48*54:route_at=cursor;break
   cursor=end
  if route_at is not None:break
 assert route_at is not None,'Need contiguous2592bytes for48piece routing'
 def write(at,data,before=None):
  end=at+len(data);assert not any(written[at:end]) and not any(protected[at:end])
  if before is not None:assert old[at:end]==before,(hex(at),old[at:end].hex(),before.hex())
  rom[at:end]=data;written[at:end]=bytes([1])*len(data)
 route_origin=physical(route_block['bank'],route_block['address']);original=old[route_origin:route_origin+324]
 directory=bytearray().join(original[(i//8)*54:(i//8+1)*54] for i in range(48))
 for piece,stage,indices in [(31,'snow',(14,15)),(32,'city',(0,1))]:
  for index in indices:
   at,_=places['marker',f'{stage}:{index}'];assert at%16384==8192
   directory[piece*54+index*3:piece*54+index*3+3]=packed(pointer(at))
  at,_=places['curve',stage];directory[piece*54+48:piece*54+51]=packed(pointer(at))
 assert len(directory)==2592;write(route_at,directory)
 # Geometry stage6/7 directories are installed in cache1900..1bff.
 extras=b''.join(packed(x) for s in ('snow','city') for x in overlay['groups'][s]);assert len(extras)==768
 write(0x3100,extras,bytes([255])*768)
 needle=bytes.fromhex('010009edb0');at=old.find(needle,8192,8192+0x56);assert at>=0
 write(at+1,(3072).to_bytes(2,'little'),(2304).to_bytes(2,'little'))
 # Stage key is geometry-specific. Appearance entry normalizes6/7 back3/4.
 needle=bytes.fromhex('3a4fe20f0f0fe6074f');at=old.find(needle,8192+0x1bf,8192+0x220);assert at>=0
 write(at+3,bytes.fromhex('cd001d0000'),bytes.fromhex('0f0f0fe607'))
 write(8192+0x26d,bytes.fromhex('c3f1f200'),bytes.fromhex('e56f2600'))
 write(8192+0x2f1,appearance,bytes([255])*len(appearance))
 needle=bytes.fromhex('01f102edb0');at=old.find(needle,9216,9344);assert at>=0
 write(at+1,(766).to_bytes(2,'little'),(753).to_bytes(2,'little'))
 oldloader=(R/'work/bitpacked-nibble-reader/loader.bin').read_bytes()
 write(0x2500,loader,oldloader+bytes([255])*(len(loader)-len(oldloader)))
 write(0x2700,selector,bytes([255])*len(selector))
 helper=(R/'outputs/six-route-trial-lined-dedup/helpers.asm').read_text()
 helper=helper.replace('ld bc,24576',f"ld bc,{route_block['address']}").replace('ld a,240',f"ld a,{route_block['bank']}")
 original_helper=assemble('original-helper',helper);assert old[codeoff(0x8572):codeoff(0x8572)+len(original_helper)]==original_helper
 helper=helper.replace(' rrca\n rrca\n rrca\n and 7',' nop\n nop\n nop\n and 63')
 bank,address=pointer(route_at)
 helper=helper.replace(f"ld bc,{route_block['address']}",f'ld bc,{address}').replace(f"ld a,{route_block['bank']}",f'ld a,{bank}')
 new_helper=assemble('piece-helper',helper);assert len(new_helper)==len(original_helper)
 write(codeoff(0x8572),new_helper,original_helper)
 assert len(rom)==4194304 and all(x==y or written[i] for i,(x,y) in enumerate(zip(old,rom)))
 # Routing proof: original entries everywhere except explicitly selected pointers.
 for piece in range(48):
  entry=rom[route_at+piece*54:route_at+(piece+1)*54]
  if piece not in (31,32):assert entry==original[(piece//8)*54:(piece//8+1)*54]
  assert entry[51:54]==original[(piece//8)*54+51:(piece//8)*54+54]
 out=R/('outputs/six-route-boundary-nibble-dispatch'+suffix);out.mkdir(exist_ok=True);(out/p.name).write_bytes(rom)
 for f in src.glob('*.bin'):(out/f.name).write_bytes(f.read_bytes())
 for name in ('geometry-layout.json','boundary-geometry-layout.json'):(out/name).write_bytes((src/name).read_bytes())
 report={'sha256':hashlib.sha256(rom).hexdigest(),'bytes':len(rom),'piece_directory_offset':route_at,'piece_directory_bytes':2592,'geometry_keys':{'31':6,'32':7},'appearance_normalization':{'6':3,'7':4},'adopted':False,'scope':'Onlypieces31/32 selectalternategeometry/markers/curve; native scope/invalidation/appearance/visual tests pending.'}
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print(suffix,report,flush=True)
