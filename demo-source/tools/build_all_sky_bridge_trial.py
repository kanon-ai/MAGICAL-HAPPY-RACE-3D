from pathlib import Path
import json,hashlib,subprocess
R=Path(__file__).resolve().parents[1]
S=json.loads((R/'outputs/symbols.json').read_text())
banks=[191,196,197,198,199,200,201,202,203,204,205,206]
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-integrated'+suffix);O=R/('outputs/six-route-all-sky-bridge'+suffix);O.mkdir(exist_ok=True)
 rom=bytearray((src/name).read_bytes());original=bytes(rom)
 asm=(R/('outputs/six-route-sky-bridge-cache'+suffix)/'bridge.asm').read_text().split('pointers:')[0]
 target=S['_scene_target']
 old=f'ld a,({target})\n cp 5\n ret nz';assert old in asm
 asm=asm.replace(old,f'ld a,({target})\n or a\n ret z\n cp 6\n ret nc\n cp 5\n jr nz,band')
 asm=asm.replace('add a,52\n srl a\n srl a\n srl a','add a,56\n srl a\n srl a\n srl a\n srl a')
 needle=' ld c,a\n ld a,(0dbeah)';assert needle in asm
 asm=asm.replace(needle,f' ld c,a\n ld a,({target})\n dec a\n ld b,a\n add a,a\n add a,b\n add a,a\n add a,b\n add a,c\n ld c,a\n ld a,(0dbeah)')
 asm+='pointers:\n'
 for n in range(35):asm+=f' db {banks[n//3]}\n dw {0x6200+n%3*2496}\n'
 (O/'bridge.asm').write_text(asm)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'bridge.asm'),str(O/'bridge.bin')],check=True)
 code=(O/'bridge.bin').read_bytes();assert len(code)<=512,len(code)
 data=(R/'outputs/all-sky-bridge-study/bands.bin').read_bytes();assert len(data)==35*2496
 for i,b in enumerate(banks):
  at=b*16384+8192
  if b not in [191,196,197,198,199]:assert rom[at:at+8192]==b'\xff'*8192
  block=bytearray(b'\xff'*8192);block[:len(code)]=code
  for j in range(3):
   n=i*3+j
   if n<35:block[512+j*2496:512+(j+1)*2496]=data[n*2496:(n+1)*2496]
  rom[at:at+8192]=block
 assert len(rom)==4194304
 (O/name).write_bytes(rom)
 for a in ('city-atlas.bin','night-atlas.bin'):(O/a).write_bytes((src/a).read_bytes())
 (O/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),source_sha256=hashlib.sha256(original).hexdigest(),helper_bytes=len(code),reserved_halfbanks=banks,additional_reserved_bytes=7*8192,scope='All five panorama joins feathered in seven pan bins; native validation pending. Free capacity accounting needs re-audit.'),indent=2))
 print(O,len(code))
