"""Standalone coast-compatible storage trial. Preserve the playable outputs.

Uses verified compiled runtime and isolated geometry pack; patches only boot and
the old course unpack entry. All stages deliberately still select coast geometry.
"""
from pathlib import Path
import json,re,subprocess,hashlib,sys
R=Path(__file__).resolve().parents[1];W=R/'work/dictionary-standalone';W.mkdir(parents=True,exist_ok=True)
O=R/'outputs/dictionary-standalone';O.mkdir(parents=True,exist_ok=True)
hybrid='--hybrid' in sys.argv
joined='--joined' in sys.argv
assert not joined or hybrid
if hybrid:
 W=R/'work/dictionary-standalone-hybrid';W.mkdir(exist_ok=True)
 O=R/'outputs/dictionary-standalone-hybrid';O.mkdir(exist_ok=True)
if joined:
 W=R/'work/dictionary-standalone-hybrid-joined';W.mkdir(exist_ok=True)
 O=R/'outputs/dictionary-standalone-hybrid-joined';O.mkdir(exist_ok=True)
S=json.loads((R/'outputs/symbols.json').read_text())
native=R/('outputs/dictionary-components-jump17-hybrid/coast' if hybrid else 'outputs/dictionary-components-jump17/coast')
if joined:native=R/'outputs/dictionary-components-jump17-hybrid-joined/coast'
layout=json.loads((native/'geometry-layout.json').read_text())
source=native/'decoder-test.rom'
rom=bytearray(source.read_bytes());assert hashlib.sha256(rom).hexdigest()==layout['test_rom_sha256']
asm=(R/'tools/dictionary_components_trial.asm').read_text()
# Decode mesh/rear directly to their final scratch addresses. Road metadata
# stays below F4AF, so these writes cannot overwrite the pending road expansion.
assert asm.count(' ld a,175\n call component\n')==1
asm=asm.replace(' ld a,175\n call component\n',' ld a,175\n call component\n ld de,0f500h\n')
move=' ld hl,0f5beh\n ld de,0f60fh\n ld bc,272\n lddr\n'
assert asm.count(move)==1
asm=asm.replace(move,'')
if hybrid:
 assert asm.count('sample:\n ld c,a\n')==1
 asm=asm.replace('sample:\n ld c,a\n','sample:\n bit 7,h\n jr z,compressed_sample\n res 7,h\n add a,l\n ld l,a\n jr nc,raw_ready\n inc h\nraw_ready:\n ld a,(hl)\n ret\ncompressed_sample:\n ld c,a\n')
asm=asm.replace('ready:\n jp ready',f'''ready:
 ld hl,02000h
 ld d,0
product_column:
 xor a
 ld b,32
product_byte:
 ld (hl),a
 inc hl
 add a,d
 djnz product_byte
 inc d
 jr nz,product_column
 xor a
 ld (06000h),a
 ld hl,06800h
 ld de,01000h
 ld bc,2304
 ldir
 ld a,255
 ld (last_group),a
 ld a,(saved_page)
 out (0fch),a
 jp {S['_main']}
''')
a=asm.index('enter_load:');b=asm.index('adapt:')
asm=asm[:a]+'''entry:
 ld (phase_value),hl
 ld a,l
 and 31
 ld (sample_phase),a
 ex af,af'
 push af
 ex af,af'
 exx
 push bc
 exx
 push iy
 in a,(0fch)
 ld (saved_page),a
 ld a,(cache_page)
 out (0fch),a
 ; Coast-only integration gate: do not switch candidate geometry yet.
 srl h
 rr l
 srl h
 rr l
 srl h
 rr l
 srl h
 rr l
 srl h
 rr l
 ld c,l
 ld a,(last_group)
 cp c
 jp z,decode
 ld a,c
 ld (last_group),a
 ld b,0
 add hl,hl
 add hl,bc
 ld bc,01000h
 add hl,bc
 ld a,(hl)
 inc hl
 ld c,(hl)
 inc hl
 ld h,(hl)
 ld l,c
 ld (06000h),a
 jp load_group
'''+asm[b:]+ '\nlast_group: db 255\n'
(W/'decoder.asm').write_text(asm)
pasmo='C:/Software/Pasmo/pasmo.exe'
def assemble(name):
    subprocess.run([pasmo,'--bin',str(W/f'{name}.asm'),str(W/f'{name}.bin'),str(W/f'{name}.sym')],cwd=R,check=True)
assemble('decoder')
decoder=(W/'decoder.bin').read_bytes();assert len(decoder)<768
symbols={n:int(v,16) for n,v in re.findall(r'(\w+)\s+EQU\s+0([0-9A-F]+)H',(W/'decoder.sym').read_text())}
installer=f'''org 0f300h
 xor a
 ld (06000h),a
 ld hl,06000h
 ld de,0f000h
 ld bc,{len(decoder)}
 ldir
 jp 0f000h
'''
(W/'installer.asm').write_text(installer);assemble('installer')
install=(W/'installer.bin').read_bytes();assert len(install)<128
boot=(R/'work/build/boot.asm').read_text().replace('0F300h','0F400h')
assert boot.count(f'jp {S["_main"]}')==1
boot=boot.replace(f'jp {S["_main"]}',f'''xor a
    ld (06000h),a
    ld hl,06400h
    ld de,0F300h
    ld bc,{len(install)}
    ldir
    jp 0F300h''')
(W/'boot.asm').write_text(boot);assemble('boot')
boot_data=(W/'boot.bin').read_bytes();assert len(boot_data)==8192
rom[:8192]=boot_data
# Bank 0 upper half was only a duplicate boot image; no runtime reader uses it.
rom[8192:16384]=b'\xff'*8192
rom[8192:8192+len(decoder)]=decoder
rom[8192+1024:8192+1024+len(install)]=install
directory=b''.join(bytes([bank])+address.to_bytes(2,'little') for name in ('coast','canyon','forest','snow','city','night') for bank,address in layout['groups'][name])
assert len(directory)==2304
rom[8192+2048:8192+2048+len(directory)]=directory
listing=(R/'work/build/game.lst').read_text()
unpack=0x8000+int(re.search(r'^\s*([0-9A-F]{8}).* _unpack_course:',listing,re.M)[1],16)
at=(1+(unpack-0x8000)//8192)*16384+8192+(unpack-0x8000)%8192
assert rom[at:at+3]==bytes.fromhex('7d e6 01')
rom[at:at+3]=b'\xc3'+symbols['entry'].to_bytes(2,'little')
target=O/'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom';target.write_bytes(rom)
report=dict(file=target.name,rom_bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),
            decoder_bytes=len(decoder),decoder_ram='F000-F2FF',installer_ram='F300-F37F startup only',
            stack_top='F400',entry=unpack,decoder_entry=symbols['entry'],
            limitation='Standalone trial still selects coast geometry for every stage. Markers/appearance and gameplay are unchanged. Stack/BGM/visual runtime verification pending.')
(O/'build-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
