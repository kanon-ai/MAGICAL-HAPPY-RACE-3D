"""Delay and ramp coast/canyon mirror terrain using rear-view distance."""
from pathlib import Path
import json,re,subprocess,hashlib
R=Path(__file__).resolve().parents[1];O=R/'outputs/six-route-mirror';O.mkdir(exist_ok=True)
source=R/'outputs/six-route-ground/MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'
rom=bytearray(source.read_bytes());S=json.loads((R/'outputs/symbols.json').read_text())
p=list(map(int,re.findall(r'\d+',(R/'src/palette_data.h').read_text().split('{')[1].split('}')[0])));pal=[p[i:i+3] for i in range(0,768,3)]
table=[]
for i in range(9):
 for start in (35,43):
  target=[pal[start][k]*(1-i/8)+pal[75][k]*i/8 for k in range(3)]
  table.append(start if i==0 else 75 if i==8 else min(range(256),key=lambda c:sum((pal[c][k]-target[k])**2 for k in range(3))))
asm=f'''org 0fdc1h
 ld a,({S['_route_piece']})
 cp 8
 jr z,coast_join
 ld a,b
 ret nc
 ld a,35
 ret
coast_join:
 ld a,({S['_distance']+1})
 or a
 jr z,index_ready
 dec a
 cp 9
 jr c,index_ready
 ld a,8
index_ready:
 add a,a
 ld l,a
 ld h,0
 ld de,colors
 add hl,de
 ld a,(hl)
 inc hl
 ld b,(hl)
 ret
colors: db {','.join(map(str,table))}
'''
(O/'mirror.asm').write_text(asm)
subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'mirror.asm'),str(O/'mirror.bin')],check=True)
code=(O/'mirror.bin').read_bytes();assert len(code)<=63,len(code)
at=255*16384+8192+1409;assert rom[at:at+len(code)]==b'\xff'*len(code);rom[at:at+len(code)]=code
needle=b'\x3a'+S['_route_piece'].to_bytes(2,'little')+bytes.fromhex('d6 08 38 03 78 18 02 3e 23')
assert rom.count(needle)==1;at=rom.index(needle);rom[at:at+len(needle)]=bytes.fromhex('cd c1 fd')+bytes(len(needle)-3)
(O/source.name).write_bytes(rom)
report=dict(sha256=hashlib.sha256(rom).hexdigest(),helper_bytes=len(code),colors=table,scope='Only coast/canyon mirror ground; holds coast through rear256 units then ramps over2048 units. No extra draw calls.')
(O/'build-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
