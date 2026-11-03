"""Connect shared appearance tiles to coast rendering in a separate trial."""
from pathlib import Path
import json,re,subprocess,hashlib,sys
from audit_rom_layout import audit
R=Path(__file__).resolve().parents[1];O=R/'outputs/dictionary-appearance';O.mkdir(exist_ok=True)
relocated='--relocated' in sys.argv
joined='--joined' in sys.argv
suffix='-joined' if joined else ''
dedup='--dedup' in sys.argv
assert not dedup or joined
layout_suffix=suffix+('-dedup' if dedup else '')
assert not joined or relocated
if relocated:O=R/'outputs/dictionary-relocated';O.mkdir(exist_ok=True)
if joined:O=R/'outputs/dictionary-relocated-joined';O.mkdir(exist_ok=True)
if dedup:O=R/'outputs/dictionary-relocated-joined-dedup';O.mkdir(exist_ok=True)
base=(R/'outputs/MAGICAL_HAPPY_RALLY_3D.rom').read_bytes()
source=R/f'outputs/dictionary-standalone-hybrid{suffix}'
rom=bytearray((source/'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom').read_bytes())
geom=json.loads((R/f'outputs/dictionary-components-jump17-hybrid{suffix}/coast/geometry-layout.json').read_text())
claimed={(x['bank'],x['offset']) for x in geom['physical_slots']}
free=[x for x in audit(base)['free_slots'] if (x['bank'],x['offset']) not in claimed]
def put(data):
 blocks=[]
 for start in range(0,len(data),8192):
  x=free.pop(0);at=x['bank']*16384+x['offset'];part=data[start:start+8192]
  rom[at:at+8192]=part+b'\xff'*(8192-len(part))
  blocks.append((x['bank'],0x4000+x['offset']))
 return blocks
def ptr(block):return bytes([block[0]])+block[1].to_bytes(2,'little')
D=R/('work/joined-column-dictionary' if joined else 'work/column-dictionary')
tiles=put((D/'appearance-tiles.bin').read_bytes())
indices=put((D/'appearance-index.bin').read_bytes())
directory=bytearray()
for stage in range(6):
 directory.extend(bytes(51));b,a=indices[stage//4];directory.extend(ptr((b,a+(stage%4)*2048)))
for block in tiles:directory.extend(ptr(block))
directory_bank,directory_address=put(directory)[0]
if relocated:
 rom=bytearray((R/f'outputs/six-route-layout{layout_suffix}/six-route-data-image.bin').read_bytes())
 final=json.loads((R/f'outputs/six-route-layout{layout_suffix}/layout.json').read_text())
 directory_block=next(a for a in final['allocations'] if a['name']=='route lookup directory')['blocks'][0]
 directory_bank,directory_address=directory_block['bank'],directory_block['address']
asm=(R/f'work/dictionary-standalone-hybrid{suffix}/decoder.asm').read_text()
old=''' ld a,(route_piece_address)
 and 7
 add a,238
 ld (06000h),a
 ld hl,(phase_value)
 add hl,hl
 ld a,h
 or 060h
 ld h,a
 ld a,(hl)
 inc hl
 ld h,(hl)
 ld l,a
'''
new=''' push de
 ld hl,(phase_value)
 add hl,hl
 ld a,(route_piece_address)
 and 7
 rrca
 rrca
 rrca
 or h
 ld h,a
 xor a
 call appearance_lookup
 pop de
'''
assert asm.count(old)==1;asm=asm.replace(old,new)
asm+=f'\ndirectory_bank equ {directory_bank}\ndirectory_address equ {directory_address}\n'+(R/'tools/appearance_lookup.asm').read_text()
(O/'decoder.asm').write_text(asm)
subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'decoder.asm'),str(O/'decoder.bin'),str(O/'decoder.sym')],check=True)
code=(O/'decoder.bin').read_bytes();assert len(code)<768,len(code)
sym={n:int(v,16) for n,v in re.findall(r'(\w+)\s+EQU\s+0([0-9A-F]+)H',(O/'decoder.sym').read_text())}
rom[8192:8192+len(code)]=code
# Installer copies the combined decoder/helper; the loader itself is unchanged.
oldlen=json.loads((source/'build-manifest.json').read_text())['decoder_bytes']
needle=b'\x01'+oldlen.to_bytes(2,'little')+b'\xed\xb0'
at=rom.find(needle,8192+1024,8192+1152);assert at>=0
rom[at+1:at+3]=len(code).to_bytes(2,'little')
manifest=json.loads((source/'build-manifest.json').read_text());unpack=manifest['entry']
at=(1+(unpack-0x8000)//8192)*16384+8192+(unpack-0x8000)%8192
rom[at:at+3]=b'\xc3'+sym['entry'].to_bytes(2,'little')
# Replace only the appearance load block in the compiled VIEW image.
S=json.loads((R/'outputs/symbols.json').read_text());rp=S['_route_piece']
needle=b'\x3a'+rp.to_bytes(2,'little')+bytes.fromhex('e6 07 c6 ee 32 00 60 dd 6e f9 dd 66 fa 29 fd 21 00 60 eb fd 19 fd 7e 00 dd 77 fd fd 7e 01 dd 77 fe')
start=214*16384+8192;view=bytes(rom[start:start+6144]);assert view.count(needle)==1
patch=bytes.fromhex('dd 6e f9 dd 66 fa 29 3a')+rp.to_bytes(2,'little')+bytes.fromhex('e6 07 0f 0f 0f b4 67 af cd')+sym['appearance_lookup'].to_bytes(2,'little')+bytes.fromhex('dd 75 fd dd 74 fe')
assert len(patch)<=len(needle)
at=start+view.index(needle);rom[at:at+len(needle)]=patch+bytes(len(needle)-len(patch))
if relocated:
 markers=next(a for a in final['allocations'] if a['name']=='coast markers')['blocks']
 assert all(b['bank']==markers[0]['bank']+i and b['address']==0x6000 for i,b in enumerate(markers))
 needle=b'\x3a'+(S['_course_phase']+1).to_bytes(2,'little')+bytes.fromhex('c6 de 32 00 60')
 assert rom.count(needle)==1
 at=rom.index(needle);rom[at+4]=markers[0]['bank']
 curve=next(a for a in final['allocations'] if a['name']=='coast curve')['blocks'][0]
 assert curve['address']==0x6000
 needle=bytes.fromhex('21 00 60 36 fb 7b c6 70 47 0a 32')+S['_course_curve'].to_bytes(2,'little')
 assert rom.count(needle)==1
 at=rom.index(needle);rom[at+4]=curve['bank'];rom[at+7]=0x60
target=O/'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom';target.write_bytes(rom)
(O/'build-manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),decoder_bytes=len(code),final_six_route_layout=relocated,scope='Coast-only compatibility gate; stage-specific geometry/marker/curve dispatch not enabled.'),indent=2)+'\n')
print('Combined code bytes',len(code))
