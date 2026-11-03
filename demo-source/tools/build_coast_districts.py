"""Coastal district facade variety; only existing scenery identity helper changes."""
from pathlib import Path
import subprocess,hashlib,json
R=Path(__file__).resolve().parents[1];W=R/'work/coast-districts';W.mkdir(exist_ok=True)
s=(R/'work/coast-scale/vegetation.asm').read_text().replace('org 07c00h','org 07c00h\n call district_building',1)
s+="""
district_building:
 ld a,(0e24fh)
 cp 7
 ret nc
 ld a,c
 cp 4
 jr c,district_select
 cp 6
 ret nz
district_select:
 push hl
 push de
 ld a,(0e24fh)
 srl a
 add a,a
 add a,a
 ld e,a
 ld l,(ix-12)
 ld h,(ix-11)
 ld a,(hl)
 rrca
 rrca
 rrca
 and 3
 add a,e
 ld e,a
 ld d,0
 ld hl,district_types
 add hl,de
 ld c,(hl)
 pop de
 pop hl
 ret
district_types:
 db 3,6,0,3
 db 0,2,1,0
 db 6,3,6,1
 db 2,1,3,2
"""
(W/'vegetation.asm').write_text(s)
subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(W/'vegetation.asm'),str(W/'vegetation.bin')],check=True)
code=(W/'vegetation.bin').read_bytes();prior=(R/'work/coast-scale/vegetation.bin').read_bytes();assert len(code)<1024
for suffix in ('','-external-88h'):
 src=R/('outputs/mirror-truck'+suffix);p=next(src.glob('*.rom'));old=p.read_bytes();b=bytearray(old);at=211*16384+8192+0x1c00
 assert hashlib.sha256(old).hexdigest()==json.loads((src/'manifest.json').read_text())['sha256']
 assert old[at:at+len(prior)]==prior
 assert old[at+len(prior):at+len(code)]==bytes([255])*(len(code)-len(prior))
 b[at:at+len(code)]=code
 assert b[:at]==old[:at] and b[at+len(code):]==old[at+len(code):] and len(b)==4194304
 O=R/('outputs/coast-districts'+suffix);O.mkdir(exist_ok=True);(O/p.name).write_bytes(b)
 (O/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(b).hexdigest(),source_sha256=hashlib.sha256(old).hexdigest(),bytes=len(b),helper_bytes=len(code),scope='Coast pieces0-6 building type from stable world style plus district. Existing textures, footprints, placement, vegetation, transitions and gameplay preserved.'),indent=2))
print('Districts built:',len(code),'helper bytes')
