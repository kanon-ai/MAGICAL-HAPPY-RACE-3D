"""Stage1 vertical proportions only, preserving footprints and ground anchors."""
from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parents[1];W=R/'work/coast-scale';W.mkdir(exist_ok=True)
oldcode=(R/'work/natural-coast/vegetation.bin').read_bytes()
s=(R/'work/natural-coast/vegetation.asm').read_text()
s=s.replace(' ld a,c\n cp 5',' ld a,c\n cp 4\n jp z,lower_palm\n cp 5',1)
s=s.replace('store_kind:\n','store_kind:\n call building_height\n',1)
s=s.replace('jr nc,store_kind','jp nc,store_kind').replace('jr nz,store_kind','jp nz,store_kind')
s+='''
lower_palm:
 ld l,(ix-5)
 ld h,(ix-4)
 ld de,4
 add hl,de
 ld a,(hl)
 ld d,a
 srl a
 srl a
 ld e,a
 ld a,d
 sub e
 ld (hl),a
 jp store_kind
building_height:
 ld a,(0e24fh)
 cp 8
 ret nc
 ld a,c
 cp 2
 ret nc
 push bc
 push de
 push hl
 push iy
 push af
 ld a,(ix-1)
 ld c,60
 db 0edh,0c9h
 ld de,0100h
 add hl,de
 push hl
 pop iy
 pop af
 ld c,a
'''
for n,(bottom,top) in enumerate(((2,17),(7,12),(22,37),(27,32))):
 s+=f'''
 ld l,(iy+{bottom})
 ld h,(iy+{bottom+1})
 ld e,(iy+{top})
 ld d,(iy+{top+1})
 push de
 or a
 sbc hl,de
 srl h
 rr l
 ld a,c
 or a
 jr nz,half_{n}
 ld d,h
 ld e,l
 srl h
 rr l
 add hl,de
half_{n}:
 ex de,hl
 pop hl
 or a
 sbc hl,de
 ld (iy+{top}),l
 ld (iy+{top+1}),h
'''
s+=' pop iy\n pop hl\n pop de\n pop bc\n ret\n'
(W/'vegetation.asm').write_text(s)
subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(W/'vegetation.asm'),str(W/'vegetation.bin')],check=True)
code=(W/'vegetation.bin').read_bytes();assert len(code)<512
for suffix in ('','-external-88h'):
 src=R/('outputs/natural-coast-yellow'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();rom=bytearray(old);at=211*16384+8192+0x1c00
 assert hashlib.sha256(old).hexdigest()==json.loads((src/'manifest.json').read_text())['sha256']
 assert old[at:at+len(oldcode)]==oldcode and old[at+len(oldcode):at+len(code)]==bytes([255])*(len(code)-len(oldcode))
 rom[at:at+len(code)]=code
 assert rom[:at]==old[:at] and rom[at+len(code):]==old[at+len(code):] and len(rom)==4194304
 O=R/('outputs/coast-scale'+suffix);O.mkdir(exist_ok=True);(O/p.name).write_bytes(rom)
 (O/'manifest.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(old).hexdigest(),sha256=hashlib.sha256(rom).hexdigest(),bytes=len(rom),helper_bytes=len(code),scope='Stage1 hotel roof height x1.75, civic roof x1.5, palms x0.75. Ground corners, footprints, other stages, textures, cars and gameplay unchanged.',native_verified=False),indent=2))
 print(O)
