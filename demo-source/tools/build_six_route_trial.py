"""Experimental stage-specific geometry/markers/curve/appearance dispatch."""
from pathlib import Path
import json,re,subprocess,hashlib,sys
R=Path(__file__).resolve().parents[1];O=R/'outputs/six-route-trial';O.mkdir(exist_ok=True)
joined='--joined' in sys.argv
suffix='-joined' if joined else ''
dedup='--dedup' in sys.argv
assert not dedup or joined
if dedup:suffix+='-dedup'
if joined:O=R/'outputs/six-route-trial-joined';O.mkdir(exist_ok=True)
if dedup:O=R/'outputs/six-route-trial-joined-dedup';O.mkdir(exist_ok=True)
source=R/f'outputs/dictionary-relocated{suffix}'
layout=json.loads((R/f'outputs/six-route-layout{suffix}/layout.json').read_text())
marker_bank=next(a for a in layout['allocations'] if a['name']=='coast markers')['blocks'][0]['bank']
curve_bank=next(a for a in layout['allocations'] if a['name']=='coast curve')['blocks'][0]['bank']
rom=bytearray((source/'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom').read_bytes())
S=json.loads((R/'outputs/symbols.json').read_text())
def symbols(path):return {n:int(v,16) for n,v in re.findall(r'(\w+)\s+EQU\s+0([0-9A-F]+)H',path.read_text())}
old=symbols(source/'decoder.sym')
asm=(source/'decoder.asm').read_text()
needle=' ; Coast-only integration gate: do not switch candidate geometry yet.\n'
assert asm.count(needle)==1
asm=asm.replace(needle,''' ld a,(route_piece_address)
 rrca
 rrca
 rrca
 and 7
 ld c,a
 ld a,(last_stage)
 cp c
 jr z,same_stage
 ld a,c
 ld (last_stage),a
 ld a,255
 ld (last_group),a
same_stage:
''')
needle=' ld bc,01000h\n add hl,bc\n'
assert asm.count(needle)==1
asm=asm.replace(needle,''' push hl
 ld a,(last_stage)
 ld d,a
 ld e,0
 ld h,d
 ld l,e
 srl h
 rr l
 add hl,de
 pop de
 add hl,de
 ld bc,01000h
 add hl,bc
''')
assert asm.count(' xor a\n call appearance_lookup')==1
asm=asm.replace(' xor a\n call appearance_lookup',' ld a,(last_stage)\n call appearance_lookup')
asm+='\nlast_stage: db 255\n'
def assemble(name,text):
 (O/f'{name}.asm').write_text(text)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/f'{name}.asm'),str(O/f'{name}.bin'),str(O/f'{name}.sym')],check=True)
 return (O/f'{name}.bin').read_bytes(),symbols(O/f'{name}.sym')
code,new=assemble('decoder',asm);assert len(code)<768,len(code)
helpers=f'''org 08572h
marker_bank:
 ld e,a
 add a,a
 add a,e
 ld e,a
 jr stage_pointer
curve_read:
 ld b,e
 push bc
 ld e,48
 call stage_pointer
 pop de
 add hl,de
 ld a,(hl)
 ld ({S['_course_curve']}),a
 ret
stage_pointer:
 ld c,e
 ld b,0
 push bc
 ld a,({S['_route_piece']})
 rrca
 rrca
 rrca
 and 7
 ld l,a
 ld h,0
 add hl,hl
 ld d,h
 ld e,l
 add hl,hl
 add hl,de
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,de
 add hl,de
 add hl,de
 pop bc
 add hl,bc
 ld bc,{new['directory_address']}
 add hl,bc
 ld a,{new['directory_bank']}
 ld (06000h),a
 jp {new['mapped_pointer']}
'''
helper,H=assemble('helpers',helpers);assert len(helper)<=0x85c5-0x8572,len(helper)
def code_at(address):return (1+(address-0x8000)//8192)*16384+8192+(address-0x8000)%8192
rom[8192:8192+len(code)]=code
needle=b'\x01'+(source/'decoder.bin').stat().st_size.to_bytes(2,'little')+b'\xed\xb0'
at=rom.find(needle,9216,9344);assert at>=0;rom[at+1:at+3]=len(code).to_bytes(2,'little')
at=code_at(0x856f);assert rom[at]==0xc3
rom[at:at+3]=b'\xc3'+new['entry'].to_bytes(2,'little');rom[at+3:at+3+len(helper)]=helper
# VIEW appearance loader: compute stage separately from piece's offset.
needle=bytes.fromhex('af cd')+old['appearance_lookup'].to_bytes(2,'little')+bytes.fromhex('dd 75 fd dd 74 fe')
at=rom.find(needle,214*16384+8192,214*16384+8192+6144);assert at>=0
patch=b'\x3a'+S['_route_piece'].to_bytes(2,'little')+bytes.fromhex('0f 0f 0f e6 07 cd')+new['appearance_lookup'].to_bytes(2,'little')+bytes.fromhex('dd 75 fd dd 74 fe')
assert rom[at+len(needle):at+len(patch)]==bytes(len(patch)-len(needle))
rom[at:at+len(patch)]=patch
needle=b'\x3a'+(S['_course_phase']+1).to_bytes(2,'little')+bytes([0xc6,marker_bank])+bytes.fromhex('32 00 60')
assert rom.count(needle)==1;at=rom.index(needle)
rom[at+3:at+8]=b'\xcd'+H['marker_bank'].to_bytes(2,'little')+b'\0\0'
needle=bytes.fromhex('21 00 60 36')+bytes([curve_bank])+bytes.fromhex('7b c6 60 47 0a 32')+S['_course_curve'].to_bytes(2,'little')+b'\xc9'
assert rom.count(needle)==1;at=rom.index(needle)
rom[at:at+len(needle)]=b'\xc3'+H['curve_read'].to_bytes(2,'little')+bytes(len(needle)-3)
target=O/'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom';target.write_bytes(rom)
report=dict(sha256=hashlib.sha256(rom).hexdigest(),decoder_bytes=len(code),helper_bytes=len(helper),scope='Six candidate geometries dispatched; stage boundary joins not yet validated. Experimental only.')
(O/'build-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
